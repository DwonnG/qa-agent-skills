"""Discover Lambda functions and optionally filter by tag.

Usage:
  discover-functions --profile P [--region R] [--prefix app_] [--tag K=V ...]
                     [--names "fn1,fn2,..."] [--jobs 12]

Output: JSON with a `functions` array.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from _lib import detect_region, log, run_aws


_progress_lock = threading.Lock()
_progress = [0, 0]


def _check_tags(profile, region, fn, tag_filters, quiet):
    data = run_aws(profile, region, "lambda", "get-function",
                   "--function-name", fn, "--query", "Tags", quiet=quiet)
    with _progress_lock:
        _progress[0] += 1
        d, t = _progress[0], _progress[1]
        log(f"  [{d}/{t}] {fn}", quiet=quiet)
    if data is None:
        return None
    tags = data or {}
    if all(tags.get(k) == v for k, v in tag_filters.items()):
        return fn
    return None


def main():
    parser = argparse.ArgumentParser(description="Discover Lambda functions")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--region", default=None)
    parser.add_argument("--prefix", default="", help="Filter by function name prefix")
    parser.add_argument("--tag", action="append", default=[],
                        help="Filter by tag (Key=Value). Can be repeated.")
    parser.add_argument("--names", default="",
                        help="Comma-separated exact function names (skip discovery)")
    parser.add_argument("--jobs", type=int, default=12, metavar="N",
                        help="Parallel get-function calls when filtering by tag.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    quiet = args.quiet
    region = detect_region(args.profile, args.region)

    if args.names:
        functions = [n.strip() for n in args.names.split(",") if n.strip()]
    else:
        data = run_aws(args.profile, region, "lambda", "list-functions",
                       "--query", "Functions[].FunctionName", quiet=quiet)
        if data is None:
            sys.exit(1)
        functions = data

    if args.prefix:
        functions = [f for f in functions if f.startswith(args.prefix)]

    if not args.tag:
        result = {
            "region": region,
            "filter": {"prefix": args.prefix, "tags": {}},
            "scanned": len(functions),
            "count": len(functions),
            "functions": sorted(functions),
        }
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    tag_filters = {}
    for t in args.tag:
        if "=" not in t:
            print(f"ERROR: tag must be Key=Value, got: {t}", file=sys.stderr)
            sys.exit(1)
        k, v = t.split("=", 1)
        tag_filters[k.strip()] = v.strip()

    total = len(functions)
    _progress[0] = 0
    _progress[1] = total
    workers = max(1, min(args.jobs, total or 1))
    matched = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(_check_tags, args.profile, region, fn, tag_filters, quiet): fn
            for fn in functions
        }
        for fut in as_completed(futures):
            name = fut.result()
            if name:
                matched.append(name)

    result = {
        "region": region,
        "filter": {"prefix": args.prefix, "tags": tag_filters},
        "scanned": total,
        "count": len(matched),
        "functions": sorted(matched),
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

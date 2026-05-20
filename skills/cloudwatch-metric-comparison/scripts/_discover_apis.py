"""Discover API Gateway names (REST + HTTP/v2) and optionally filter by tag.

Usage:
  discover-apis --profile P [--region R] [--prefix app_] [--tag K=V ...]

Output: JSON with an `apis` array of names usable with `collect-metrics --apis`.
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


def _list_rest_apis(profile, region, quiet):
    out = []
    next_token = None
    while True:
        args = ["apigateway", "get-rest-apis"]
        if next_token:
            args += ["--position", next_token]
        data = run_aws(profile, region, *args, quiet=quiet)
        if data is None:
            return out
        for item in data.get("items", []):
            out.append({
                "name": item.get("name", ""),
                "id": item.get("id", ""),
                "kind": "REST",
                "tags": item.get("tags", {}) or {},
            })
        next_token = data.get("position")
        if not next_token:
            break
    return out


def _list_http_apis(profile, region, quiet):
    out = []
    next_token = None
    while True:
        args = ["apigatewayv2", "get-apis"]
        if next_token:
            args += ["--next-token", next_token]
        data = run_aws(profile, region, *args, quiet=quiet)
        if data is None:
            return out
        for item in data.get("Items", []):
            out.append({
                "name": item.get("Name", ""),
                "id": item.get("ApiId", ""),
                "kind": item.get("ProtocolType", "HTTP"),
                "tags": item.get("Tags", {}) or {},
            })
        next_token = data.get("NextToken")
        if not next_token:
            break
    return out


def _fetch_rest_tags(profile, region, item, quiet):
    arn = f"arn:aws:apigateway:{region}::/restapis/{item['id']}"
    data = run_aws(profile, region, "apigateway", "get-tags",
                   "--resource-arn", arn, quiet=quiet)
    with _progress_lock:
        _progress[0] += 1
        d, t = _progress[0], _progress[1]
        log(f"  [{d}/{t}] tags {item['name']}", quiet=quiet)
    if data is None:
        return item
    item["tags"] = data.get("tags", {}) or {}
    return item


def main():
    parser = argparse.ArgumentParser(description="Discover API Gateways")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--region", default=None)
    parser.add_argument("--prefix", default="", help="Filter by API name prefix")
    parser.add_argument("--tag", action="append", default=[],
                        help="Filter by tag (Key=Value). Can be repeated.")
    parser.add_argument("--include", choices=["rest", "http", "all"], default="all")
    parser.add_argument("--jobs", type=int, default=12, metavar="N")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    quiet = args.quiet
    region = detect_region(args.profile, args.region)

    items = []
    if args.include in ("rest", "all"):
        items += _list_rest_apis(args.profile, region, quiet)
    if args.include in ("http", "all"):
        items += _list_http_apis(args.profile, region, quiet)

    if args.prefix:
        items = [i for i in items if (i.get("name") or "").startswith(args.prefix)]

    tag_filters = {}
    for t in args.tag:
        if "=" not in t:
            print(f"ERROR: tag must be Key=Value, got: {t}", file=sys.stderr)
            sys.exit(1)
        k, v = t.split("=", 1)
        tag_filters[k.strip()] = v.strip()

    if tag_filters:
        rest_to_fetch = [i for i in items if i.get("kind") == "REST" and not i.get("tags")]
        if rest_to_fetch:
            total = len(rest_to_fetch)
            _progress[0] = 0
            _progress[1] = total
            workers = max(1, min(args.jobs, total))
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = [ex.submit(_fetch_rest_tags, args.profile, region, i, quiet)
                           for i in rest_to_fetch]
                for _ in as_completed(futures):
                    pass

        items = [
            i for i in items
            if all((i.get("tags") or {}).get(k) == v for k, v in tag_filters.items())
        ]

    items.sort(key=lambda i: i.get("name") or "")

    result = {
        "region": region,
        "filter": {"prefix": args.prefix, "tags": tag_filters, "include": args.include},
        "count": len(items),
        "apis": [i.get("name") for i in items if i.get("name")],
        "details": items,
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

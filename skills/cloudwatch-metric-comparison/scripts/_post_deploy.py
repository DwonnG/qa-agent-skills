"""One-shot post-deployment metric comparison.

Minimal input: just `--profile`. Defaults:
  - region:        AWS_REGION env > profile config > us-east-1
  - prefix:        app_
  - tag:           none (use --tag K=V to scope by tag, repeatable)
  - anchor:        <prefix>api_handler
  - baseline:      T - 30 days  (where T = anchor LastModified)
  - current:       T -> now
  - threshold:     25%
  - min-baseline:  10
  - format:        md (human-readable)

Usage:
  post-deploy --profile P
  post-deploy --profile P --prefix staging_ --baseline-days 14 --threshold 50
  post-deploy --profile P --release-time 2026-05-06T14:00:00Z   # override anchor
  post-deploy --profile P --compare-releases                    # release N vs N-1
  post-deploy --profile P --out report.md --quiet --exit-code
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from _lib import (
    detect_region,
    exit_code_for,
    iso,
    log,
    parse_iso,
    render_csv,
    render_markdown,
    render_text,
    run_aws,
    summary_status,
    write_output,
)


def _resolve_release_time(profile, region, anchor, explicit, quiet):
    """Return (datetime_utc, source_description). Falls back to (None, reason) if anchor missing."""
    if explicit:
        return parse_iso(explicit), f"explicit --release-time {explicit}"

    data = run_aws(
        profile, region, "lambda", "get-function-configuration",
        "--function-name", anchor, "--query", "LastModified",
        quiet=quiet,
    )
    if data is None or not isinstance(data, str):
        return None, f"anchor function '{anchor}' not found or unreadable"

    try:
        dt = parse_iso(data)
        return dt, f"anchor LastModified ({anchor}={data})"
    except Exception as e:
        return None, f"could not parse LastModified for {anchor}: {e}"


def _parse_release_pair(events: list) -> list[datetime]:
    """Extract sorted (descending) UpdateFunctionCode timestamps from CloudTrail events.

    Pure function — easy to unit-test. Accepts the raw `Events` array from
    CloudTrail's `lookup-events` response. Filters to EventName starting
    with 'UpdateFunctionCode' (covers the v1 and v2 API names) and returns
    UTC datetimes sorted newest-first.
    """
    if not events:
        return []
    timestamps: list[datetime] = []
    for ev in events:
        name = ev.get("EventName", "")
        if not name.startswith("UpdateFunctionCode"):
            continue
        ts_raw = ev.get("EventTime")
        if not ts_raw:
            continue
        try:
            timestamps.append(parse_iso(ts_raw))
        except Exception:
            continue
    timestamps.sort(reverse=True)
    return timestamps


def _choose_baseline_start(
    prev_release: datetime,
    current_release: datetime,
    min_baseline_days: int,
) -> tuple[datetime, bool, float]:
    """Pick the baseline start, widening past prev_release for hotfixes.

    Returns (baseline_start_dt, widened, gap_hours).

    If the gap between releases is shorter than `min_baseline_days`, treat the
    current release as a hotfix and widen the baseline back to
    `current_release - min_baseline_days` so the comparison sees a real
    pre-hotfix window instead of just the few hours/days the prior release ran.
    Otherwise honor the natural prev->current window.
    """
    gap_hours = (current_release - prev_release).total_seconds() / 3600.0
    min_delta = timedelta(days=min_baseline_days)
    if (current_release - prev_release) < min_delta:
        return current_release - min_delta, True, gap_hours
    return prev_release, False, gap_hours


def _resolve_release_pair(profile, region, anchor, lookback_days, quiet):
    """Return (t_prev_dt, t_current_dt, source) for the two most recent code deploys of `anchor`.

    Falls back to (None, None, reason) if fewer than two deploys are visible
    in CloudTrail within the lookback window.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    data = run_aws(
        profile, region, "cloudtrail", "lookup-events",
        "--lookup-attributes", f"AttributeKey=ResourceName,AttributeValue={anchor}",
        "--start-time", iso(start),
        "--end-time", iso(end),
        "--max-items", "100",
        quiet=quiet,
    )
    if data is None or not isinstance(data, dict):
        return None, None, f"CloudTrail lookup-events returned no data for {anchor}"

    events = data.get("Events") or []
    timestamps = _parse_release_pair(events)
    if len(timestamps) < 2:
        seen = sorted({ev.get("EventName", "?") for ev in events})
        seen_summary = (
            f"saw {len(events)} total events for this resource: {', '.join(seen)}"
            if events else
            f"CloudTrail returned 0 events for resource '{anchor}' "
            f"(verify the function exists and has had any activity in the lookback window)"
        )
        return (
            None,
            None,
            f"need 2 UpdateFunctionCode events for {anchor} in last {lookback_days}d, "
            f"found {len(timestamps)}; {seen_summary}",
        )
    t_current, t_prev = timestamps[0], timestamps[1]
    return (
        t_prev,
        t_current,
        f"CloudTrail UpdateFunctionCode on {anchor}: prev={iso(t_prev)} current={iso(t_current)}",
    )


def _list_lambdas(profile, region, prefix, tag_filters, quiet):
    data = run_aws(profile, region, "lambda", "list-functions",
                   "--query", "Functions[].FunctionName", quiet=quiet)
    if data is None:
        raise RuntimeError("lambda list-functions failed")
    functions = data
    if prefix:
        functions = [f for f in functions if f.startswith(prefix)]
    if not tag_filters:
        return sorted(functions)

    matched = []
    log(f"Filtering {len(functions)} functions by tag {tag_filters}", quiet=quiet)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def check(fn):
        tags = run_aws(profile, region, "lambda", "get-function",
                       "--function-name", fn, "--query", "Tags", quiet=quiet) or {}
        if all(tags.get(k) == v for k, v in tag_filters.items()):
            return fn
        return None

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(check, fn) for fn in functions]
        for fut in as_completed(futures):
            name = fut.result()
            if name:
                matched.append(name)
    return sorted(matched)


def main():
    parser = argparse.ArgumentParser(description="One-shot post-deploy metric comparison")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--region", default=None)
    parser.add_argument("--prefix", default="app_",
                        help="Lambda name prefix (default app_). Use '' to disable.")
    parser.add_argument("--tag", action="append", default=None,
                        help="Tag filter K=V. Repeatable. AND across keys. Default: no tag filter.")
    parser.add_argument("--anchor", default=None,
                        help="Anchor function name. Default <prefix>api_handler.")
    parser.add_argument("--release-time", default=None,
                        help="ISO timestamp; skip anchor lookup.")
    parser.add_argument("--compare-releases", action="store_true",
                        help="Compare release N vs N-1 (CloudTrail UpdateFunctionCode on the "
                             "anchor). Baseline = prev_release -> current_release. "
                             "Current = current_release -> now.")
    parser.add_argument("--lookback-days", type=int, default=30,
                        help="How far back to scan CloudTrail for --compare-releases (default 30).")
    parser.add_argument("--min-baseline-days", type=int, default=7,
                        help="With --compare-releases: if the gap between the two releases is "
                             "shorter than this (i.e. a hotfix), widen the baseline back to "
                             "current_release - N days instead of using the brief inter-release "
                             "window (default 7).")
    parser.add_argument("--no-compare-releases-fallback", action="store_true",
                        help="With --compare-releases: do NOT silently fall back to anchor "
                             "LastModified + --baseline-days when CloudTrail returns no "
                             "UpdateFunctionCode events. Default is to fall back so the run "
                             "always produces a report.")
    parser.add_argument("--baseline-days", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=25.0)
    parser.add_argument("--min-baseline", type=float, default=10.0)
    parser.add_argument("--apis", default="",
                        help="Comma-separated API Gateway names to include.")
    parser.add_argument("--format", choices=["json", "md", "text", "csv"], default="md")
    parser.add_argument("--out", default=None)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--exit-code", action="store_true")
    args = parser.parse_args()

    quiet = args.quiet
    region = detect_region(args.profile, args.region)

    tag_filters: dict[str, str] = {}
    if args.tag:
        for t in args.tag:
            if t.strip() == "":
                continue  # tolerate accidental --tag '' for backward compat
            if "=" not in t:
                print(f"ERROR: --tag must be Key=Value, got: {t}", file=sys.stderr)
                sys.exit(3)
            k, v = t.split("=", 1)
            tag_filters[k.strip()] = v.strip()

    anchor = args.anchor or f"{args.prefix.rstrip('_')}_api_handler"

    log(f"Region: {region}", quiet=quiet)
    log(f"Prefix: {args.prefix!r}   Tag filter: {tag_filters}", quiet=quiet)
    log(f"Anchor: {anchor}", quiet=quiet)

    prev_release_dt: datetime | None = None
    baseline_widened = False
    release_gap_hours: float | None = None
    fallback_reason: str | None = None

    if args.compare_releases:
        if args.release_time:
            print(
                "ERROR: --compare-releases and --release-time are mutually exclusive.",
                file=sys.stderr,
            )
            sys.exit(3)
        prev_release_dt, release_dt, source = _resolve_release_pair(
            args.profile, region, anchor, args.lookback_days, quiet=quiet
        )
        if release_dt is None or prev_release_dt is None:
            if args.no_compare_releases_fallback:
                print(
                    f"ERROR: --compare-releases failed: {source}\n"
                    f"Hint: widen --lookback-days, pick a different --anchor, or drop "
                    f"--compare-releases to use --baseline-days instead.",
                    file=sys.stderr,
                )
                sys.exit(3)
            log(
                f"WARN: --compare-releases unavailable ({source}). "
                f"Falling back to anchor LastModified + --baseline-days {args.baseline_days}.",
                quiet=quiet,
            )
            fallback_reason = source
            prev_release_dt = None  # disable release-vs-release reporting
            release_dt, fb_source = _resolve_release_time(
                args.profile, region, anchor, None, quiet=quiet
            )
            if release_dt is None:
                print(
                    f"ERROR: --compare-releases fallback failed: {fb_source}\n"
                    f"Original CloudTrail issue: {fallback_reason}",
                    file=sys.stderr,
                )
                sys.exit(3)
            source = f"{fb_source} (fell back from --compare-releases)"
            baseline_end = release_dt
            baseline_start = baseline_end - timedelta(days=args.baseline_days)
            current_start = release_dt
            current_end = datetime.now(timezone.utc)
        else:
            baseline_start, baseline_widened, release_gap_hours = _choose_baseline_start(
                prev_release_dt, release_dt, args.min_baseline_days
            )
            baseline_end = release_dt
            current_start = release_dt
            current_end = datetime.now(timezone.utc)
    else:
        release_dt, source = _resolve_release_time(
            args.profile, region, anchor, args.release_time, quiet=quiet
        )
        if release_dt is None:
            print(
                f"ERROR: could not determine release time. {source}\n"
                f"Hint: pass --anchor <function> or --release-time <ISO8601>",
                file=sys.stderr,
            )
            sys.exit(3)
        baseline_end = release_dt
        baseline_start = baseline_end - timedelta(days=args.baseline_days)
        current_start = release_dt
        current_end = datetime.now(timezone.utc)

    if prev_release_dt is not None:
        log(f"Prev release:    {iso(prev_release_dt)}", quiet=quiet)
    log(f"Release time: {iso(release_dt)}  (source: {source})", quiet=quiet)
    log(f"Baseline: {iso(baseline_start)} -> {iso(baseline_end)}", quiet=quiet)
    log(f"Current:  {iso(current_start)} -> {iso(current_end)}", quiet=quiet)

    try:
        functions = _list_lambdas(args.profile, region, args.prefix, tag_filters, quiet=quiet)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    apis = [a.strip() for a in args.apis.split(",") if a.strip()]
    log(f"Discovered {len(functions)} Lambdas, {len(apis)} APIs", quiet=quiet)

    if not functions and not apis:
        print("ERROR: no functions or APIs in scope after filtering", file=sys.stderr)
        sys.exit(3)

    from _collect_metrics import _build_queries
    from _lib import (
        compute_change,
        daily_rate,
        fetch_metric_data,
        select_period,
        severity_for,
    )

    period_b = select_period(iso(baseline_start), iso(baseline_end))
    period_c = select_period(iso(current_start), iso(current_end))
    queries_b, mapping_b = _build_queries(functions, apis, period_b)
    queries_c, _ = _build_queries(functions, apis, period_c)

    try:
        baseline_data = fetch_metric_data(
            args.profile, region, queries_b, iso(baseline_start), iso(baseline_end), quiet=quiet
        )
        current_data = fetch_metric_data(
            args.profile, region, queries_c, iso(current_start), iso(current_end), quiet=quiet
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    baseline_seconds = (baseline_end - baseline_start).total_seconds()
    current_seconds = (current_end - current_start).total_seconds()

    notes = [f"release time = {iso(release_dt)} (source: {source})"]
    if fallback_reason is not None:
        notes.append(
            f"--compare-releases fell back to anchor LastModified + "
            f"--baseline-days {args.baseline_days}. "
            f"Original CloudTrail issue: {fallback_reason}"
        )
    if prev_release_dt is not None:
        gap_hours = release_gap_hours if release_gap_hours is not None else 0.0
        notes.append(
            f"comparing release N (current = {iso(release_dt)}) vs "
            f"release N-1 (prev = {iso(prev_release_dt)}); gap = {gap_hours:.1f}h"
        )
        if baseline_widened:
            notes.append(
                f"Hotfix detected (gap < {args.min_baseline_days}d). Widened baseline back to "
                f"{iso(baseline_start)} so the comparison spans real pre-hotfix behavior "
                f"instead of the brief inter-release window."
            )
    if current_seconds < 3600:
        notes.append(
            f"Current window is short ({int(current_seconds)}s); "
            "results may be noisy — re-run later for a stable picture."
        )

    meta_block = {
        "region": region,
        "generated_at": iso(datetime.now(timezone.utc)),
        "release_time": iso(release_dt),
        "release_time_source": source,
        "anchor_function": anchor,
        "baseline_window": f"{iso(baseline_start)} to {iso(baseline_end)}",
        "current_window": f"{iso(current_start)} to {iso(current_end)}",
        "baseline_start": iso(baseline_start),
        "baseline_end": iso(baseline_end),
        "current_start": iso(current_start),
        "current_end": iso(current_end),
        "baseline_period": period_b,
        "current_period": period_c,
        "threshold_pct": args.threshold,
        "min_baseline": args.min_baseline,
        "lambda_count": len(functions),
        "api_count": len(apis),
        "notes": notes,
    }
    if prev_release_dt is not None:
        meta_block["prev_release_time"] = iso(prev_release_dt)
        meta_block["mode"] = "release-vs-release"
        meta_block["release_gap_hours"] = round(release_gap_hours or 0.0, 2)
        meta_block["baseline_widened"] = baseline_widened
        meta_block["min_baseline_days"] = args.min_baseline_days
    elif fallback_reason is not None:
        meta_block["mode"] = "release-vs-baseline (fallback from --compare-releases)"
        meta_block["compare_releases_fallback_reason"] = fallback_reason
    else:
        meta_block["mode"] = "release-vs-baseline"

    results = {
        "meta": meta_block,
        "exceeded": [],
        "within_threshold": [],
        "low_volume": [],
        "errors_summary": {"total_baseline_per_day": 0.0, "total_current_per_day": 0.0},
    }

    for qid, info in mapping_b.items():
        b_vals = baseline_data.get(qid, {}).get("values", [])
        c_vals = current_data.get(qid, {}).get("values", [])
        baseline = daily_rate(b_vals, info["stat"], baseline_seconds)
        current = daily_rate(c_vals, info["stat"], current_seconds)

        if baseline == 0 and current == 0:
            continue

        pct, status = compute_change(baseline, current)

        is_sum = info["stat"] == "Sum"
        suppressed = is_sum and baseline < args.min_baseline and status != "new_activity"

        change_value = pct if pct != float("inf") else "new_activity"
        entry = {
            "resource": info["resource"],
            "type": info["type"],
            "metric": info["metric"],
            "statistic": info["stat"],
            "baseline": round(baseline, 2),
            "current": round(current, 2),
            "change_pct": round(change_value, 1) if isinstance(change_value, float) else change_value,
            "status": status,
            "severity": severity_for(info["metric"], pct, status),
        }

        if suppressed:
            entry["suppressed_reason"] = f"baseline < min_baseline ({args.min_baseline})"
            results["low_volume"].append(entry)
            continue

        if info["metric"] == "Errors":
            results["errors_summary"]["total_baseline_per_day"] += baseline
            results["errors_summary"]["total_current_per_day"] += current

        if status == "new_activity" or status == "stopped" or abs(pct) >= args.threshold:
            entry["exceeded"] = True
            results["exceeded"].append(entry)
        else:
            entry["exceeded"] = False
            results["within_threshold"].append(entry)

    results["errors_summary"]["total_baseline_per_day"] = round(
        results["errors_summary"]["total_baseline_per_day"], 2
    )
    results["errors_summary"]["total_current_per_day"] = round(
        results["errors_summary"]["total_current_per_day"], 2
    )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

    def sort_key(e):
        change = e.get("change_pct")
        magnitude = abs(change) if isinstance(change, (int, float)) else 1e9
        return (severity_rank.get(e.get("severity", "low"), 9), -magnitude)

    results["exceeded"].sort(key=sort_key)

    status_label, summary_line = summary_status(results)
    results["meta"]["status"] = status_label
    results["meta"]["summary"] = summary_line

    if args.format == "json":
        text = json.dumps(results, indent=2)
    elif args.format == "md":
        text = render_markdown(results)
    elif args.format == "csv":
        text = render_csv(results)
    else:
        text = render_text(results)

    write_output(text, args.out)

    if args.exit_code:
        sys.exit(exit_code_for(results))


if __name__ == "__main__":
    main()

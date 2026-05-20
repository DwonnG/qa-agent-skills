"""Collect CloudWatch metrics for Lambda functions and (optionally) API Gateways
across two time windows, then compare them.

Uses CloudWatch GetMetricData (batched) so a 21-function/5-metric run is two
API calls (one per window) instead of ~210 sequential get-metric-statistics calls.

Usage (positional pairs are illustrative; see argparse for full surface):
    collect-metrics --profile P [--region R]
                    --functions "fn1,fn2,..."
                    [--apis "ApiName1,ApiName2,..."]
                    [--baseline-start ... --baseline-end ...]
                    [--current-start ... --current-end ...]
                    [--threshold 25] [--min-baseline 10]
                    [--format json|md|text|csv] [--out FILE]
                    [--quiet] [--exit-code]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from _lib import (
    ERROR_METRICS,
    PERF_METRICS,
    VOLUME_METRICS,
    compute_change,
    daily_rate,
    detect_region,
    exit_code_for,
    fetch_metric_data,
    iso,
    log,
    parse_iso,
    render_csv,
    render_markdown,
    render_text,
    safe_query_id,
    select_period,
    severity_for,
    summary_status,
    write_output,
)


LAMBDA_METRICS = [
    {"name": "Invocations", "stat": "Sum"},
    {"name": "Errors", "stat": "Sum"},
    {"name": "Throttles", "stat": "Sum"},
    {"name": "ConcurrentExecutions", "stat": "Maximum"},
    {"name": "Duration", "stat": "p99"},
]

APIGW_METRICS = [
    {"name": "Count", "stat": "Sum"},
    {"name": "5XXError", "stat": "Sum"},
    {"name": "4XXError", "stat": "Sum"},
    {"name": "Latency", "stat": "p99"},
]


def _build_queries(functions, apis, period):
    """Build (queries, mapping) for GetMetricData.

    mapping[id] -> {"resource": str, "type": "Lambda"|"ApiGateway",
                    "metric": str, "stat": str}
    """
    queries = []
    mapping = {}
    idx = 0
    for fn in functions:
        for m in LAMBDA_METRICS:
            qid = safe_query_id("q", idx)
            idx += 1
            queries.append({
                "Id": qid,
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/Lambda",
                        "MetricName": m["name"],
                        "Dimensions": [{"Name": "FunctionName", "Value": fn}],
                    },
                    "Period": period,
                    "Stat": m["stat"],
                },
                "ReturnData": True,
            })
            mapping[qid] = {
                "resource": fn,
                "type": "Lambda",
                "metric": m["name"],
                "stat": m["stat"],
            }
    for api in apis:
        for m in APIGW_METRICS:
            qid = safe_query_id("q", idx)
            idx += 1
            queries.append({
                "Id": qid,
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/ApiGateway",
                        "MetricName": m["name"],
                        "Dimensions": [{"Name": "ApiName", "Value": api}],
                    },
                    "Period": period,
                    "Stat": m["stat"],
                },
                "ReturnData": True,
            })
            mapping[qid] = {
                "resource": api,
                "type": "ApiGateway",
                "metric": m["name"],
                "stat": m["stat"],
            }
    return queries, mapping


def _round(v, n=2):
    return round(float(v), n) if isinstance(v, (int, float)) else v


def main():
    parser = argparse.ArgumentParser(description="Compare CloudWatch metrics across two windows")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--region", default=None,
                        help="If omitted: AWS_REGION env, then profile config, then us-east-1.")
    parser.add_argument("--functions", default="", help="Comma-separated Lambda function names")
    parser.add_argument("--apis", default="", help="Comma-separated API Gateway names (ApiName dimension)")
    parser.add_argument("--baseline-start", required=True)
    parser.add_argument("--baseline-end", required=True)
    parser.add_argument("--current-start", required=True)
    parser.add_argument("--current-end", required=True)
    parser.add_argument("--threshold", type=float, default=25.0,
                        help="Percent change required to flag a metric (default 25).")
    parser.add_argument("--min-baseline", type=float, default=10.0,
                        help="Suppress flagging Sum-stat metrics whose baseline daily rate is below this. "
                             "Reduces noise from low-volume functions. Default 10.")
    parser.add_argument("--period-baseline", type=int, default=0,
                        help="CloudWatch period (s) for baseline window. 0 = auto by window length.")
    parser.add_argument("--period-current", type=int, default=0,
                        help="CloudWatch period (s) for current window. 0 = auto by window length.")
    parser.add_argument("--format", choices=["json", "md", "text", "csv"], default="json")
    parser.add_argument("--out", default=None,
                        help="Write output to file path (default stdout).")
    parser.add_argument("--quiet", action="store_true", help="Suppress stderr progress")
    parser.add_argument("--exit-code", action="store_true",
                        help="Set process exit code based on findings (0 clean, 1 med/high, 2 critical).")
    args = parser.parse_args()

    quiet = args.quiet
    region = detect_region(args.profile, args.region)
    functions = [f.strip() for f in args.functions.split(",") if f.strip()]
    apis = [a.strip() for a in args.apis.split(",") if a.strip()]

    if not functions and not apis:
        print("ERROR: --functions and/or --apis required (got neither)", file=sys.stderr)
        sys.exit(3)

    period_b = args.period_baseline or select_period(args.baseline_start, args.baseline_end)
    period_c = args.period_current or select_period(args.current_start, args.current_end)

    log(f"Region: {region}", quiet=quiet)
    log(f"Baseline: {args.baseline_start} -> {args.baseline_end} (period={period_b}s)", quiet=quiet)
    log(f"Current:  {args.current_start} -> {args.current_end} (period={period_c}s)", quiet=quiet)
    log(f"Lambdas: {len(functions)}  APIs: {len(apis)}  Threshold: {args.threshold}%  "
        f"Min baseline: {args.min_baseline}", quiet=quiet)

    baseline_seconds = (parse_iso(args.baseline_end) - parse_iso(args.baseline_start)).total_seconds()
    current_seconds = (parse_iso(args.current_end) - parse_iso(args.current_start)).total_seconds()

    queries_b, mapping_b = _build_queries(functions, apis, period_b)
    queries_c, mapping_c = _build_queries(functions, apis, period_c)

    try:
        baseline_data = fetch_metric_data(
            args.profile, region, queries_b, args.baseline_start, args.baseline_end, quiet=quiet
        )
        current_data = fetch_metric_data(
            args.profile, region, queries_c, args.current_start, args.current_end, quiet=quiet
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    notes = []
    if current_seconds < 3600:
        notes.append(
            f"Current window is short ({int(current_seconds)}s); samples may be sparse."
        )
    if baseline_seconds < 86400:
        notes.append(
            f"Baseline window is shorter than 1 day; per-day rates are extrapolated."
        )

    results = {
        "meta": {
            "region": region,
            "generated_at": iso(datetime.now(timezone.utc)),
            "baseline_window": f"{args.baseline_start} to {args.baseline_end}",
            "current_window": f"{args.current_start} to {args.current_end}",
            "baseline_start": args.baseline_start,
            "baseline_end": args.baseline_end,
            "current_start": args.current_start,
            "current_end": args.current_end,
            "baseline_period": period_b,
            "current_period": period_c,
            "threshold_pct": args.threshold,
            "min_baseline": args.min_baseline,
            "lambda_count": len(functions),
            "api_count": len(apis),
            "notes": notes,
        },
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
        suppressed = False
        if is_sum and baseline < args.min_baseline and status != "new_activity":
            suppressed = True

        if info["metric"] == "Errors":
            results["errors_summary"]["total_baseline_per_day"] += baseline
            results["errors_summary"]["total_current_per_day"] += current

        change_value = pct if pct != float("inf") else "new_activity"
        entry = {
            "resource": info["resource"],
            "type": info["type"],
            "metric": info["metric"],
            "statistic": info["stat"],
            "baseline": _round(baseline),
            "current": _round(current),
            "change_pct": _round(change_value, 1) if isinstance(change_value, float) else change_value,
            "status": status,
            "severity": severity_for(info["metric"], pct, status),
        }

        if suppressed:
            entry["suppressed_reason"] = f"baseline < min_baseline ({args.min_baseline})"
            results["low_volume"].append(entry)
            continue

        if status == "new_activity" or status == "stopped" or abs(pct) >= args.threshold:
            entry["exceeded"] = True
            results["exceeded"].append(entry)
        else:
            entry["exceeded"] = False
            results["within_threshold"].append(entry)

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

    def sort_key(e):
        change = e.get("change_pct")
        magnitude = abs(change) if isinstance(change, (int, float)) else 1e9
        return (severity_rank.get(e.get("severity", "low"), 9), -magnitude)

    results["exceeded"].sort(key=sort_key)
    results["errors_summary"]["total_baseline_per_day"] = round(
        results["errors_summary"]["total_baseline_per_day"], 2
    )
    results["errors_summary"]["total_current_per_day"] = round(
        results["errors_summary"]["total_current_per_day"], 2
    )

    status, summary_line = summary_status(results)
    results["meta"]["status"] = status
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

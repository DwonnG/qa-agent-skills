"""Shared helpers for the cloudwatch-metric-comparison skill scripts.

This module is imported by the underscore-prefixed entry-point modules
(`_collect_metrics.py`, `_discover_functions.py`, `_discover_apis.py`,
`_post_deploy.py`). It is not invoked directly.

Public surface:
    detect_region(profile, explicit=None) -> str
    run_aws(profile, region, *args, retries=5) -> dict | list | None
    select_period(start_iso, end_iso) -> int
    parse_iso(s) -> datetime (UTC)
    iso(dt) -> str
    daily_rate(values, stat, window_seconds) -> float
    compute_change(baseline, current) -> tuple[float, str]
    severity_for(metric_name, change_pct, status) -> str
    fetch_metric_data(profile, region, queries, start, end, ...) -> dict[id -> {timestamps, values}]
    render_markdown(results) -> str
    render_text(results) -> str
    render_csv(results) -> str
    log(msg, quiet=False)
    ERROR_METRICS, PERF_METRICS, VOLUME_METRICS  (sets)
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone


ERROR_METRICS = {"Errors", "Throttles", "5XXError"}
PERF_METRICS = {"Duration", "Latency"}
VOLUME_METRICS = {"Invocations", "Count"}

THROTTLE_MARKERS = (
    "Throttling",
    "ThrottlingException",
    "RequestLimitExceeded",
    "TooManyRequestsException",
    "Rate exceeded",
)


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def parse_iso(s: str) -> datetime:
    """Parse an RFC3339/ISO-8601 timestamp, assume UTC if naive, return aware UTC datetime."""
    raw = s.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_region(profile: str, explicit: str | None = None) -> str:
    """Resolve region: explicit > env > profile config > us-east-1 fallback."""
    if explicit:
        return explicit
    env = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if env:
        return env
    try:
        r = subprocess.run(
            ["aws", "--profile", profile, "configure", "get", "region"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return "us-east-1"


def _is_throttle(stderr: str) -> bool:
    return any(m in stderr for m in THROTTLE_MARKERS)


def run_aws(
    profile: str,
    region: str,
    *args: str,
    retries: int = 5,
    base_backoff: float = 1.0,
    quiet: bool = False,
):
    """Invoke aws CLI with retry/backoff on throttling. Returns parsed JSON or None on hard failure."""
    cmd = ["aws", "--profile", profile, "--region", region, "--output", "json"] + list(args)
    backoff = base_backoff
    for attempt in range(retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not result.stdout.strip():
                return {}
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return result.stdout
        if _is_throttle(result.stderr) and attempt < retries:
            sleep = backoff + random.random()
            log(f"  throttled, retrying in {sleep:.1f}s ({attempt + 1}/{retries})", quiet=quiet)
            time.sleep(sleep)
            backoff *= 2
            continue
        log(f"ERROR: aws {' '.join(args[:3])}... -> {result.stderr.strip()}", quiet=quiet)
        return None
    return None


def select_period(start_iso: str, end_iso: str) -> int:
    """Return CloudWatch period (seconds) appropriate for window length."""
    try:
        duration = (parse_iso(end_iso) - parse_iso(start_iso)).total_seconds()
    except Exception:
        return 3600
    if duration <= 3600:
        return 60
    if duration <= 6 * 3600:
        return 300
    if duration <= 24 * 3600:
        return 900
    if duration <= 7 * 86400:
        return 3600
    return 86400


def daily_rate(values: list[float], stat: str, window_seconds: float) -> float:
    """Aggregate raw datapoints into a comparable scalar.

    - Sum stats: total over window normalized to per-day rate.
    - Maximum: max across datapoints.
    - Other (percentiles, averages): arithmetic mean of datapoints.
    """
    if not values:
        return 0.0
    if stat == "Sum":
        days = window_seconds / 86400.0
        return sum(values) / days if days > 0 else 0.0
    if stat == "Maximum":
        return max(values)
    return sum(values) / len(values)


def compute_change(baseline: float, current: float) -> tuple[float, str]:
    if baseline == 0 and current == 0:
        return 0.0, "no_data"
    if baseline == 0 and current > 0:
        return float("inf"), "new_activity"
    if baseline > 0 and current == 0:
        return -100.0, "stopped"
    pct = ((current - baseline) / baseline) * 100
    return pct, "changed"


def severity_for(metric_name: str, change_pct, status: str) -> str:
    """Severity label based on metric type, direction, and status."""
    if status == "new_activity":
        is_increase = True
    elif status == "stopped":
        is_increase = False
    elif isinstance(change_pct, (int, float)):
        is_increase = change_pct > 0
    else:
        is_increase = False

    if status == "stopped" and metric_name in VOLUME_METRICS:
        return "high"
    if metric_name in ERROR_METRICS:
        return "critical" if is_increase else "info"
    if metric_name in PERF_METRICS:
        return "high" if is_increase else "info"
    if metric_name in VOLUME_METRICS:
        return "medium"
    return "low"


_ID_SAFE_RE = re.compile(r"[^a-z0-9]")


def safe_query_id(prefix: str, idx: int) -> str:
    """Generate a CloudWatch GetMetricData Id (lowercase alnum/_ only, starts with letter)."""
    return f"{prefix}_{idx:04d}"


def fetch_metric_data(
    profile: str,
    region: str,
    queries: list[dict],
    start_iso: str,
    end_iso: str,
    quiet: bool = False,
):
    """Fetch a set of GetMetricData queries for one window. Returns {id: {"timestamps": [...], "values": [...]}}."""
    out: dict[str, dict] = {}
    BATCH = 500
    for batch_idx in range(0, len(queries), BATCH):
        batch = queries[batch_idx : batch_idx + BATCH]
        next_token = None
        page = 0
        while True:
            page += 1
            payload = json.dumps(batch)
            args = [
                "cloudwatch",
                "get-metric-data",
                "--start-time",
                start_iso,
                "--end-time",
                end_iso,
                "--metric-data-queries",
                payload,
            ]
            if next_token:
                args += ["--next-token", next_token]

            log(
                f"  get-metric-data batch={batch_idx // BATCH + 1} "
                f"page={page} queries={len(batch)} window={start_iso}..{end_iso}",
                quiet=quiet,
            )
            data = run_aws(profile, region, *args, quiet=quiet)
            if data is None:
                raise RuntimeError("get-metric-data failed (see stderr)")

            for result in data.get("MetricDataResults", []):
                rid = result.get("Id")
                if not rid:
                    continue
                slot = out.setdefault(rid, {"timestamps": [], "values": []})
                slot["timestamps"].extend(result.get("Timestamps", []))
                slot["values"].extend(result.get("Values", []))

            next_token = data.get("NextToken")
            if not next_token:
                break
    return out


SEVERITY_ORDER = ("critical", "high", "medium", "low")


def _count_severities(results: dict) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for entry in results.get("exceeded", []):
        sev = entry.get("severity", "low")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def summary_status(results: dict) -> tuple[str, str]:
    """Return (status_label, full_summary_line) suitable for headlines and notifications."""
    counts = _count_severities(results)
    exceeded = sum(counts.values())
    within = len(results.get("within_threshold", []))
    low_vol = len(results.get("low_volume", []))
    tracked = exceeded + within + low_vol

    if counts["critical"]:
        status = "CRITICAL"
    elif counts["high"]:
        status = "HIGH"
    elif counts["medium"]:
        status = "MEDIUM"
    elif counts["low"]:
        status = "LOW"
    else:
        status = "OK"

    parts = [f"{counts[s]} {s}" for s in SEVERITY_ORDER if counts[s]]
    breakdown = ", ".join(parts) if parts else "no exceeded metrics"
    line = (
        f"STATUS: {status} -- {breakdown}"
        f" (exceeded: {exceeded} / within: {within} / low-volume: {low_vol}"
        f" / tracked: {tracked})"
    )
    return status, line


def _esc_cw(s: str) -> str:
    """CloudWatch console URL escape (custom encoding used in metricsV2 hashes).

    Order matters: '*' must be escaped first so that subsequent escapes (which
    introduce '*XX' sequences) are not re-escaped on a second pass.
    """
    return (
        s.replace("*", "*2a")
         .replace("(", "*28")
         .replace(")", "*29")
         .replace("~", "*7e")
         .replace("/", "*2f")
         .replace(":", "*3a")
         .replace(".", "*2e")
         .replace("-", "*2d")
         .replace("'", "*27")
    )


def cloudwatch_metric_url(
    region: str,
    namespace: str,
    metric_name: str,
    dim_name: str,
    dim_value: str,
    start_iso: str | None = None,
    end_iso: str | None = None,
) -> str:
    """Build a CloudWatch console URL that opens a chart for one metric.

    The console uses an undocumented pseudo-URL syntax in the URL fragment.
    This generates a single-metric link with optional explicit time range.
    """
    metric = (
        f"~(~'{_esc_cw(namespace)}~'{metric_name}~'{dim_name}~'{_esc_cw(dim_value)})"
    )
    parts = [
        "~(view~'timeSeries",
        "~stacked~false",
        f"~region~'{region}",
        f"~metrics~(~{metric})",
    ]
    if start_iso and end_iso:
        parts.append(f"~start~'{_esc_cw(start_iso)}")
        parts.append(f"~end~'{_esc_cw(end_iso)}")
    parts.append(")")
    graph = "".join(parts)
    return (
        f"https://{region}.console.aws.amazon.com/cloudwatch/home"
        f"?region={region}#metricsV2?graph={graph}"
    )


def lambda_console_url(region: str, function_name: str) -> str:
    return (
        f"https://{region}.console.aws.amazon.com/lambda/home"
        f"?region={region}#/functions/{function_name}?tab=monitoring"
    )


def apigateway_console_url(region: str) -> str:
    return (
        f"https://{region}.console.aws.amazon.com/apigateway/home?region={region}"
    )


def _resource_link(region: str, entry: dict) -> str:
    """Resolve a dashboard URL for the resource (function/api) -- multi-metric view."""
    if entry.get("type") == "Lambda":
        return lambda_console_url(region, entry["resource"])
    return apigateway_console_url(region)


def _metric_link(region: str, entry: dict, meta: dict) -> str:
    """Resolve a CloudWatch chart URL pointing at this exact metric over the full
    baseline+current span."""
    if entry.get("type") == "Lambda":
        namespace = "AWS/Lambda"
        dim_name = "FunctionName"
    elif entry.get("type") == "ApiGateway":
        namespace = "AWS/ApiGateway"
        dim_name = "ApiName"
    else:
        return _resource_link(region, entry)
    return cloudwatch_metric_url(
        region=region,
        namespace=namespace,
        metric_name=entry.get("metric", ""),
        dim_name=dim_name,
        dim_value=entry.get("resource", ""),
        start_iso=meta.get("baseline_start"),
        end_iso=meta.get("current_end"),
    )


def _format_change(change) -> str:
    if isinstance(change, (int, float)):
        return f"{change:+.1f}%"
    return str(change)


def render_markdown(results: dict) -> str:
    meta = results["meta"]
    region = meta.get("region", "us-east-1")
    status, summary_line = summary_status(results)

    lines = [
        "# CloudWatch Metric Comparison",
        "",
        f"**{summary_line}**",
        "",
    ]

    if meta.get("generated_at"):
        lines.append(f"- Generated: {meta['generated_at']}")
    lines += [
        f"- Region: `{region}`",
        f"- Baseline window: {meta['baseline_window']}",
        f"- Current window:  {meta['current_window']}",
        f"- Threshold: {meta['threshold_pct']}%   |   "
        f"Min baseline: {meta.get('min_baseline', 0)}",
        f"- Lambdas: {meta.get('lambda_count', 0)}   |   "
        f"APIs: {meta.get('api_count', 0)}",
    ]
    if meta.get("release_time"):
        lines.append(f"- Release time: `{meta['release_time']}` "
                     f"({meta.get('release_time_source', 'n/a')})")
    if meta.get("prev_release_time"):
        lines.append(f"- Previous release: `{meta['prev_release_time']}`")
    if meta.get("mode"):
        lines.append(f"- Mode: `{meta['mode']}`")
    lines.append("")

    err = results.get("errors_summary") or {}
    base_err = err.get("total_baseline_per_day")
    cur_err = err.get("total_current_per_day")
    if base_err is not None and cur_err is not None and (base_err or cur_err):
        if base_err > 0:
            err_pct = ((cur_err - base_err) / base_err) * 100
            err_pct_str = f"{err_pct:+.1f}%"
        elif cur_err > 0:
            err_pct_str = "new errors"
        else:
            err_pct_str = "0%"
        lines.append(
            f"**Errors per day (across all tracked Lambdas):** "
            f"{base_err:.2f} -> {cur_err:.2f} ({err_pct_str})"
        )
        lines.append("")

    if meta.get("notes"):
        lines.append("Notes:")
        for n in meta["notes"]:
            lines.append(f"- {n}")
        lines.append("")

    by_sev: dict[str, list] = {s: [] for s in SEVERITY_ORDER}
    for entry in results.get("exceeded", []):
        by_sev.setdefault(entry.get("severity", "low"), []).append(entry)

    if not results.get("exceeded"):
        lines.append("All metrics within threshold.")
    else:
        for sev in SEVERITY_ORDER:
            items = by_sev.get(sev, [])
            if not items:
                continue
            lines.append(f"## {sev.upper()} ({len(items)})")
            lines.append("")
            lines.append("| Resource | Metric | Stat | Baseline | Current | Change |")
            lines.append("|---|---|---|---|---|---|")
            for it in items:
                metric_url = _metric_link(region, it, meta)
                lines.append(
                    f"| `{it['resource']}` | [{it['metric']}]({metric_url}) | "
                    f"{it['statistic']} | {it['baseline']} | {it['current']} | "
                    f"{_format_change(it['change_pct'])} |"
                )
            lines.append("")

        # By Resource rollup -- same exceeded items, regrouped by resource
        by_resource: dict[str, list] = {}
        for entry in results.get("exceeded", []):
            by_resource.setdefault(entry["resource"], []).append(entry)

        # Order resources by worst-severity-first, then alphabetically
        sev_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}

        def resource_sort_key(name):
            entries = by_resource[name]
            worst = min(sev_rank.get(e.get("severity", "low"), 99) for e in entries)
            return (worst, name)

        if len(by_resource) >= 1:
            lines.append(f"## By Resource ({len(by_resource)} resources affected)")
            lines.append("")
            for name in sorted(by_resource, key=resource_sort_key):
                entries = by_resource[name]
                sev_summary = ", ".join(
                    f"{sum(1 for e in entries if e.get('severity') == s)} {s}"
                    for s in SEVERITY_ORDER
                    if any(e.get("severity") == s for e in entries)
                )
                first = entries[0]
                url = _resource_link(region, first)
                lines.append(
                    f"### [`{name}`]({url}) -- {sev_summary}"
                )
                lines.append("")
                lines.append("| Metric | Stat | Baseline | Current | Change | Severity |")
                lines.append("|---|---|---|---|---|---|")
                for e in entries:
                    metric_url = _metric_link(region, e, meta)
                    lines.append(
                        f"| [{e['metric']}]({metric_url}) | {e['statistic']} | "
                        f"{e['baseline']} | {e['current']} | "
                        f"{_format_change(e['change_pct'])} | "
                        f"{e.get('severity', 'low')} |"
                    )
                lines.append("")

    if results.get("low_volume"):
        lv_critical = sum(
            1 for it in results["low_volume"] if it.get("severity") == "critical"
        )
        lv_high = sum(
            1 for it in results["low_volume"] if it.get("severity") == "high"
        )
        lines.append(
            f"## Low volume (suppressed by --min-baseline) -- {len(results['low_volume'])} items"
            + (f"; would-be: {lv_critical} critical, {lv_high} high" if (lv_critical or lv_high) else "")
        )
        lines.append("")
        lines.append("| Resource | Metric | Baseline | Current | Would-be Severity |")
        lines.append("|---|---|---|---|---|")
        for it in results["low_volume"][:20]:
            lines.append(
                f"| `{it['resource']}` | {it['metric']} | "
                f"{it['baseline']} | {it['current']} | {it.get('severity', 'low')} |"
            )
        if len(results["low_volume"]) > 20:
            lines.append(f"| ... | ({len(results['low_volume']) - 20} more) | | | |")
        lines.append("")

    return "\n".join(lines)


def render_text(results: dict) -> str:
    """Plain-text version (no markdown table syntax or links)."""
    md = render_markdown(results)
    md = re.sub(r"\[`?([^\]`]+)`?\]\([^)]+\)", r"\1", md)
    return re.sub(r"[`|]", "", md)


def render_csv(results: dict) -> str:
    _, summary_line = summary_status(results)
    meta = results.get("meta", {})
    header_comment = (
        f"# {summary_line}\n"
        f"# region={meta.get('region', '')} "
        f"baseline={meta.get('baseline_window', '')} "
        f"current={meta.get('current_window', '')}\n"
    )
    rows = ["bucket,severity,resource,type,metric,statistic,baseline,current,change_pct,status"]
    for bucket in ("exceeded", "within_threshold", "low_volume"):
        for it in results.get(bucket, []):
            change = it.get("change_pct", "")
            if isinstance(change, float):
                change = f"{change:.2f}"
            rows.append(
                ",".join(
                    str(x)
                    for x in [
                        bucket,
                        it.get("severity", ""),
                        it.get("resource", ""),
                        it.get("type", ""),
                        it.get("metric", ""),
                        it.get("statistic", ""),
                        it.get("baseline", ""),
                        it.get("current", ""),
                        change,
                        it.get("status", ""),
                    ]
                )
            )
    return header_comment + "\n".join(rows) + "\n"


def write_output(text: str, out_path: str | None) -> None:
    if not out_path or out_path == "-":
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def exit_code_for(results: dict) -> int:
    """0 = clean, 1 = medium/high exceeded, 2 = critical exceeded."""
    sev_seen = {entry.get("severity", "low") for entry in results.get("exceeded", [])}
    if "critical" in sev_seen:
        return 2
    if "high" in sev_seen or "medium" in sev_seen:
        return 1
    return 0

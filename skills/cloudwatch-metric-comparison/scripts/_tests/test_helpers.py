"""Unit tests for cloudwatch-metric-comparison helpers.

Run with:
    nix shell nixpkgs#python3Packages.pytest --command pytest \
        skills/cloudwatch-metric-comparison/scripts/_tests/

These tests have no AWS dependency.
"""
from __future__ import annotations

import math
import sys
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _lib import (  # noqa: E402
    apigateway_console_url,
    cloudwatch_metric_url,
    compute_change,
    daily_rate,
    exit_code_for,
    iso,
    lambda_console_url,
    parse_iso,
    render_csv,
    render_markdown,
    render_text,
    select_period,
    severity_for,
    summary_status,
)


# ---- compute_change ----

def test_compute_change_normal_increase():
    pct, status = compute_change(100, 150)
    assert status == "changed"
    assert math.isclose(pct, 50.0)


def test_compute_change_decrease():
    pct, status = compute_change(200, 100)
    assert status == "changed"
    assert math.isclose(pct, -50.0)


def test_compute_change_no_data():
    pct, status = compute_change(0, 0)
    assert status == "no_data"
    assert pct == 0.0


def test_compute_change_new_activity():
    pct, status = compute_change(0, 5)
    assert status == "new_activity"
    assert pct == float("inf")


def test_compute_change_stopped():
    pct, status = compute_change(10, 0)
    assert status == "stopped"
    assert pct == -100.0


# ---- select_period ----

def test_select_period_one_hour():
    assert select_period("2026-05-06T10:00:00Z", "2026-05-06T11:00:00Z") == 60


def test_select_period_six_hours():
    assert select_period("2026-05-06T00:00:00Z", "2026-05-06T05:00:00Z") == 300


def test_select_period_one_day():
    assert select_period("2026-05-05T00:00:00Z", "2026-05-06T00:00:00Z") == 900


def test_select_period_one_week():
    assert select_period("2026-04-29T00:00:00Z", "2026-05-06T00:00:00Z") == 3600


def test_select_period_one_month():
    assert select_period("2026-04-06T00:00:00Z", "2026-05-06T00:00:00Z") == 86400


# ---- daily_rate ----

def test_daily_rate_sum_normalizes_to_per_day():
    one_week_seconds = 7 * 86400
    rate = daily_rate([100, 200, 300, 400, 500, 600, 700], "Sum", one_week_seconds)
    assert math.isclose(rate, 2800 / 7)


def test_daily_rate_max_returns_max():
    assert daily_rate([5, 12, 3, 8], "Maximum", 86400) == 12


def test_daily_rate_p99_returns_average():
    assert math.isclose(daily_rate([100, 200, 300], "p99", 86400), 200.0)


def test_daily_rate_empty_returns_zero():
    assert daily_rate([], "Sum", 86400) == 0.0


# ---- severity_for ----

def test_severity_errors_increase_is_critical():
    assert severity_for("Errors", 100.0, "changed") == "critical"


def test_severity_errors_decrease_is_info():
    assert severity_for("Errors", -50.0, "changed") == "info"


def test_severity_duration_increase_is_high():
    assert severity_for("Duration", 80.0, "changed") == "high"


def test_severity_invocations_change_is_medium():
    assert severity_for("Invocations", 200.0, "changed") == "medium"


def test_severity_new_activity_is_critical_for_errors():
    assert severity_for("Errors", "new_activity", "new_activity") == "critical"


def test_severity_stopped_invocations_is_high():
    assert severity_for("Invocations", -100.0, "stopped") == "high"


def test_severity_concurrent_executions_is_low():
    assert severity_for("ConcurrentExecutions", 50.0, "changed") == "low"


# ---- exit_code_for ----

def test_exit_code_clean():
    assert exit_code_for({"exceeded": []}) == 0


def test_exit_code_critical_wins():
    results = {"exceeded": [
        {"severity": "low"},
        {"severity": "critical"},
        {"severity": "medium"},
    ]}
    assert exit_code_for(results) == 2


def test_exit_code_high_or_medium_yields_one():
    results = {"exceeded": [{"severity": "high"}, {"severity": "low"}]}
    assert exit_code_for(results) == 1


# ---- iso / parse_iso roundtrip ----

def test_iso_roundtrip_z_suffix():
    dt = parse_iso("2026-05-06T14:30:00Z")
    assert dt.tzinfo == timezone.utc
    assert iso(dt) == "2026-05-06T14:30:00Z"


def test_iso_roundtrip_offset_normalizes_to_utc():
    dt = parse_iso("2026-05-06T10:30:00-04:00")
    assert iso(dt) == "2026-05-06T14:30:00Z"


# ---- formatters smoke tests ----

def _sample_results():
    return {
        "meta": {
            "region": "us-east-1",
            "baseline_window": "2026-04-06T00:00:00Z to 2026-05-06T00:00:00Z",
            "current_window": "2026-05-06T00:00:00Z to 2026-05-06T15:00:00Z",
            "threshold_pct": 25,
            "min_baseline": 10,
            "lambda_count": 2,
            "api_count": 0,
            "notes": ["release time = 2026-05-06T00:00:00Z"],
        },
        "exceeded": [
            {
                "resource": "app_x", "type": "Lambda", "metric": "Errors",
                "statistic": "Sum", "baseline": 1.0, "current": 5.0,
                "change_pct": 400.0, "status": "changed", "severity": "critical",
            }
        ],
        "within_threshold": [],
        "low_volume": [],
    }


def test_render_markdown_smoke():
    out = render_markdown(_sample_results())
    assert "CloudWatch Metric Comparison" in out
    assert "app_x" in out
    assert "CRITICAL" in out


def test_render_csv_smoke():
    out = render_csv(_sample_results())
    lines = out.splitlines()
    assert lines[0].startswith("# STATUS:")
    assert "bucket,severity" in lines[2]
    assert "app_x" in out


def test_render_text_strips_links():
    out = render_text(_sample_results())
    assert "(http" not in out
    assert "app_x" in out


# ---- summary_status ----

def test_summary_status_ok_when_no_exceeded():
    status, line = summary_status({"exceeded": []})
    assert status == "OK"
    assert "no exceeded metrics" in line


def test_summary_status_picks_worst():
    res = {"exceeded": [{"severity": "low"}, {"severity": "critical"}, {"severity": "high"}]}
    status, line = summary_status(res)
    assert status == "CRITICAL"
    assert "1 critical" in line
    assert "1 high" in line
    assert "1 low" in line


def test_summary_status_includes_within_and_low_volume_counts():
    res = {
        "exceeded": [{"severity": "high"}],
        "within_threshold": [1, 2, 3, 4, 5],
        "low_volume": [1, 2],
    }
    _, line = summary_status(res)
    assert "exceeded: 1" in line
    assert "within: 5" in line
    assert "low-volume: 2" in line
    assert "tracked: 8" in line


# ---- console URL helpers ----

def test_lambda_console_url_basic():
    url = lambda_console_url("us-east-1", "app_piam_action_container")
    assert url.startswith("https://us-east-1.console.aws.amazon.com/lambda/home")
    assert "app_piam_action_container" in url
    assert "tab=monitoring" in url


def test_apigateway_console_url_basic():
    url = apigateway_console_url("us-west-2")
    assert "us-west-2" in url
    assert "apigateway/home" in url


def test_cloudwatch_metric_url_contains_metric_and_dimension():
    url = cloudwatch_metric_url(
        "us-east-1", "AWS/Lambda", "Errors", "FunctionName", "app_x",
        "2026-05-06T14:00:00Z", "2026-05-06T16:00:00Z",
    )
    assert url.startswith("https://us-east-1.console.aws.amazon.com/cloudwatch/home")
    assert "metricsV2" in url
    assert "AWS*2fLambda" in url   # AWS/Lambda escaped
    assert "Errors" in url
    assert "FunctionName" in url
    assert "app_x" in url
    # start/end appear escaped (no raw ':')
    assert ":00:00Z" not in url.split("#")[1]


def test_cloudwatch_metric_url_without_time_range():
    url = cloudwatch_metric_url(
        "us-east-1", "AWS/Lambda", "Errors", "FunctionName", "app_x",
    )
    assert "metricsV2" in url
    assert "start" not in url.split("#")[1]


def test_cloudwatch_metric_url_for_apigateway():
    url = cloudwatch_metric_url(
        "us-east-1", "AWS/ApiGateway", "5XXError", "ApiName", "app_internal_api",
    )
    assert "AWS*2fApiGateway" in url
    assert "5XXError" in url
    assert "ApiName" in url


def test_esc_cw_escapes_meta_chars():
    # imported via the local helper test module path
    from _lib import _esc_cw
    assert _esc_cw("a/b") == "a*2fb"
    assert _esc_cw("a:b") == "a*3ab"
    assert _esc_cw("a~b") == "a*7eb"
    assert _esc_cw("(x)") == "*28x*29"
    # '*' must be escaped first so subsequent escapes don't double-escape it
    assert _esc_cw("a*b") == "a*2ab"
    assert _esc_cw("AWS/Lambda") == "AWS*2fLambda"


# ---- markdown report content ----

def test_render_markdown_includes_summary_line():
    out = render_markdown(_sample_results())
    assert "STATUS: CRITICAL" in out
    assert "1 critical" in out


def test_render_markdown_includes_by_resource_section():
    out = render_markdown(_sample_results())
    assert "## By Resource" in out
    assert "app_x" in out


def test_render_markdown_severity_tables_link_the_metric():
    out = render_markdown(_sample_results())
    # Metric column is the clickable link (resource appears as plain code)
    assert "`app_x` | [Errors](https://" in out
    assert "metricsV2" in out


def test_render_markdown_by_resource_header_links_dashboard():
    out = render_markdown(_sample_results())
    assert "### [`app_x`](https://us-east-1.console.aws.amazon.com/lambda/home" in out


def test_render_markdown_metric_link_includes_time_window():
    res = _sample_results()
    res["meta"]["baseline_start"] = "2026-04-06T14:00:00Z"
    res["meta"]["current_end"] = "2026-05-06T16:00:00Z"
    out = render_markdown(res)
    # encoded ':' -> '*3a'
    assert "2026*2d04*2d06T14*3a00*3a00Z" in out
    assert "2026*2d05*2d06T16*3a00*3a00Z" in out


def test_render_markdown_errors_callout():
    res = _sample_results()
    res["errors_summary"] = {"total_baseline_per_day": 5.5, "total_current_per_day": 10.0}
    out = render_markdown(res)
    assert "Errors per day" in out
    assert "5.50 -> 10.00" in out


# ---- _parse_release_pair / _choose_baseline_start ----

from datetime import timedelta  # noqa: E402

from _post_deploy import _choose_baseline_start, _parse_release_pair  # noqa: E402


def test_parse_release_pair_returns_two_most_recent_descending():
    events = [
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "2026-05-01T10:00:00Z"},
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "2026-05-06T14:30:00Z"},
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "2026-04-15T09:00:00Z"},
    ]
    ts = _parse_release_pair(events)
    assert len(ts) == 3
    assert iso(ts[0]) == "2026-05-06T14:30:00Z"
    assert iso(ts[1]) == "2026-05-01T10:00:00Z"
    assert iso(ts[2]) == "2026-04-15T09:00:00Z"


def test_parse_release_pair_filters_non_code_updates():
    events = [
        {"EventName": "UpdateFunctionConfiguration20150331v2", "EventTime": "2026-05-06T14:30:00Z"},
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "2026-05-01T10:00:00Z"},
        {"EventName": "PublishLayerVersion", "EventTime": "2026-04-30T08:00:00Z"},
    ]
    ts = _parse_release_pair(events)
    assert len(ts) == 1
    assert iso(ts[0]) == "2026-05-01T10:00:00Z"


def test_parse_release_pair_accepts_v1_event_name():
    events = [
        {"EventName": "UpdateFunctionCode", "EventTime": "2026-05-06T14:30:00Z"},
        {"EventName": "UpdateFunctionCode20150331", "EventTime": "2026-05-01T10:00:00Z"},
    ]
    ts = _parse_release_pair(events)
    assert len(ts) == 2


def test_parse_release_pair_handles_empty_or_missing():
    assert _parse_release_pair([]) == []
    assert _parse_release_pair(None) == []  # type: ignore[arg-type]


def test_parse_release_pair_ignores_malformed_timestamps():
    events = [
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "2026-05-06T14:30:00Z"},
        {"EventName": "UpdateFunctionCode20150331v2", "EventTime": "not-a-timestamp"},
        {"EventName": "UpdateFunctionCode20150331v2"},  # missing EventTime
    ]
    ts = _parse_release_pair(events)
    assert len(ts) == 1
    assert iso(ts[0]) == "2026-05-06T14:30:00Z"


def test_choose_baseline_start_normal_release_keeps_prev():
    prev = parse_iso("2026-04-22T10:00:00Z")
    cur = parse_iso("2026-05-06T10:00:00Z")  # 14 days later
    start, widened, gap = _choose_baseline_start(prev, cur, min_baseline_days=7)
    assert start == prev
    assert widened is False
    assert math.isclose(gap, 14 * 24, rel_tol=1e-6)


def test_choose_baseline_start_hotfix_widens_baseline():
    prev = parse_iso("2026-05-06T08:00:00Z")
    cur = parse_iso("2026-05-06T14:00:00Z")  # 6h later (hotfix)
    start, widened, gap = _choose_baseline_start(prev, cur, min_baseline_days=7)
    assert widened is True
    assert math.isclose(gap, 6.0, rel_tol=1e-6)
    assert start == cur - timedelta(days=7)


def test_choose_baseline_start_exactly_at_threshold_does_not_widen():
    prev = parse_iso("2026-04-29T10:00:00Z")
    cur = parse_iso("2026-05-06T10:00:00Z")  # exactly 7 days later
    start, widened, _gap = _choose_baseline_start(prev, cur, min_baseline_days=7)
    assert widened is False
    assert start == prev


def test_choose_baseline_start_respects_custom_min_days():
    prev = parse_iso("2026-04-30T10:00:00Z")
    cur = parse_iso("2026-05-06T10:00:00Z")  # 6 days later
    # default 7d -> widens
    start_default, widened_default, _ = _choose_baseline_start(prev, cur, min_baseline_days=7)
    assert widened_default is True
    # but with min=3, the 6d gap is enough -> keeps prev
    start_custom, widened_custom, _ = _choose_baseline_start(prev, cur, min_baseline_days=3)
    assert widened_custom is False
    assert start_custom == prev
    assert start_default == cur - timedelta(days=7)

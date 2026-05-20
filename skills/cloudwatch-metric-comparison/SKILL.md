---
name: cloudwatch-metric-comparison
description: Compare AWS CloudWatch metrics across release windows to detect behavioral drift in Lambda functions and API Gateways. Use when the user asks to compare metrics, check for metric drift, detect behavioral changes after a deployment, or analyze CloudWatch metric trends.
allowed-tools: Read, Bash(scripts/aws-cli:*), Bash(scripts/post-deploy:*), Bash(scripts/collect-metrics:*), Bash(scripts/discover-functions:*), Bash(scripts/discover-apis:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Environment

```bash
scripts/aws-cli <command>            # raw AWS CLI shim (read-only ops)
scripts/post-deploy <args>           # PRIMARY: one-shot post-deploy comparison
scripts/discover-functions <args>    # list Lambda function names
scripts/discover-apis <args>         # list API Gateway names
scripts/collect-metrics <args>       # explicit two-window comparison
```

The shims provide `aws` CLI and Python via nix shell. All `scripts/` paths are relative to this skill's installation directory.

The Claude CLI session sets `AWS_*` environment variables for Bedrock. To avoid using Bedrock credentials, you **must** pass `--profile` on every command.

**Before running any commands**, ask the user which AWS profile to use. List available profiles:

```bash
scripts/aws-cli configure list-profiles
```

Default to a read-only profile when available since this skill only reads metrics.

If credentials are expired (AccessDenied / ExpiredToken), tell the user to re-authenticate (e.g., `your SSO CLI`).

## Quick start (recommended)

For a typical post-deploy check, **call `post-deploy` directly** — it handles discovery, anchor detection, window math, batched metric collection, severity ranking, and rendering in one command:

```bash
scripts/post-deploy --profile <PROFILE> --format md
```

Defaults baked in:

| Default | Value | Override flag |
|---|---|---|
| Region | `AWS_REGION` env > profile config > `us-east-1` | `--region` |
| Lambda scope | prefix `app_`, no tag filter | `--prefix`, `--tag K=V` (repeatable; AND across keys; e.g. `--tag ResourceOwner=<team>` to scope to one team) |
| Anchor function | `<prefix>_api_handler` | `--anchor`, or `--release-time <ISO>` |
| Baseline | `release_time − 30 days` → `release_time` | `--baseline-days N`, or `--compare-releases` for prev-release → current-release |
| Current | `release_time` → now | `--release-time`, or `--compare-releases` |
| Threshold | 25% | `--threshold` |
| Noise floor | suppress Sum metrics with baseline daily rate < 10 | `--min-baseline N` |
| Output | markdown to stdout | `--format json|md|text|csv`, `--out FILE` |
| Exit code | always 0 | `--exit-code` (0 clean, 1 medium/high, 2 critical) |

Use `--quiet` to silence stderr progress (helpful in Jenkins).

### Release-vs-release (e.g. "compare 3.8.0 to 3.7.0")

```bash
scripts/post-deploy --profile <PROFILE> --prefix staging_ --compare-releases
```

Finds the two most recent `UpdateFunctionCode` events for the anchor in CloudTrail (default lookback 30 days, override with `--lookback-days N`) and uses them as the window boundaries: baseline = `prev_release → current_release`, current = `current_release → now`. The report header shows both timestamps and the gap. If fewer than two deploys are visible, the script errors out with a hint to widen `--lookback-days` or fall back to `--baseline-days`.

**Hotfix-aware baseline.** If the gap between the two releases is shorter than `--min-baseline-days` (default 7), the baseline is automatically widened back to `current_release − N days` so you compare against real pre-hotfix behavior instead of the brief inter-release window. The report's Notes section calls this out (`Hotfix detected (gap < 7d). Widened baseline back to ...`) and `meta.baseline_widened` is `true` in the JSON.

**Fallback when CloudTrail is empty.** If the profile lacks `cloudtrail:LookupEvents` for Lambda, or the anchor function has no `UpdateFunctionCode` events in the lookback window, `--compare-releases` automatically falls back to `release_time = anchor.LastModified` + `--baseline-days N`. The report Notes section explains exactly why and `meta.mode` becomes `"release-vs-baseline (fallback from --compare-releases)"`. Pass `--no-compare-releases-fallback` if you want a hard failure instead (e.g. in a Jenkins gate).

## Workflow

1. **Select AWS profile** (only required input). List profiles via `scripts/aws-cli configure list-profiles` and confirm with the user.

2. **Run `post-deploy`** with the chosen profile and any overrides the user mentioned (different env prefix, custom threshold, alternate anchor, etc.).

3. **Interpret the output**:
   - The markdown report already groups by severity (CRITICAL → HIGH → MEDIUM → LOW) and includes a low-volume bucket suppressed by the noise floor.
   - Severity rules: Errors/Throttles/5XXError increase = CRITICAL. Duration/Latency p99 increase = HIGH. Invocations/Count change or Lambda stopped = MEDIUM/HIGH. ConcurrentExecutions/4XXError = LOW.
   - Explain the most impactful changes, suggest likely causes, and recommend next steps.

4. **Optional follow-ups** (only if the user asks):
   - Pull recent error log samples for a flagged function: `scripts/aws-cli --profile <P> logs filter-log-events --log-group-name /aws/lambda/<fn> --start-time <ms> --filter-pattern ERROR --max-items 20`.
   - Check related CloudWatch alarms: `scripts/aws-cli --profile <P> cloudwatch describe-alarms-for-metric --namespace AWS/Lambda --metric-name <Metric> --dimensions Name=FunctionName,Value=<fn>`.
   - Open a Jira ticket (jira-issues skill).
   - Cross-check recent merged PRs (github-manager skill).
   - Update a Confluence page (confluence-pages skill).

## Advanced: explicit windows or custom scope

When the user wants full control (different release boundaries, comparing arbitrary windows, or scoping to non-default tags), use the building blocks directly:

```bash
# 1) discover scope
scripts/discover-functions --profile <P> --prefix app_ [--tag ResourceOwner=<team>]
scripts/discover-apis --profile <P> --prefix app_ [--tag ResourceOwner=<team>]

# 2) determine release time T (anchor or CloudTrail)
scripts/aws-cli --profile <P> lambda get-function-configuration \
  --function-name app_api_handler --query LastModified

# 3) collect across two explicit windows
scripts/collect-metrics --profile <P> \
  --functions "fn1,fn2,fn3" --apis "api1,api2" \
  --baseline-start <ISO> --baseline-end <ISO> \
  --current-start <ISO> --current-end <ISO> \
  --threshold 25 --min-baseline 10 --format md
```

`collect-metrics` uses CloudWatch `GetMetricData` (batched, 500 queries/call), so the whole comparison is **two API calls** total regardless of fleet size. Period is auto-selected per window length (60s for ≤1h, 300s ≤6h, 900s ≤1d, 1h ≤7d, else 1d) — override with `--period-baseline`/`--period-current`.

## Filtering reference

`discover-functions` and `discover-apis` accept:

- `--prefix STR` — name prefix
- `--tag K=V` — repeatable; AND across keys
- `--names "a,b,c"` (functions only) — skip discovery, use exact list

Output is JSON with a `functions` (or `apis`) array you can splat into `collect-metrics --functions "$(...)"`.

For deeper guidance see `references/filtering.md`, `references/metrics-catalog.md`, `references/comparison-modes.md`, and the workflow guides in `references/workflows/`.

## Comparison modes

See `references/comparison-modes.md`. The primary mode used by `post-deploy` is **release-to-release with a 30-day baseline** anchored on the policy API function's `LastModified`. Fall back to **rolling baseline** (last 7d vs last 24h) for environments with frequent deploys.

## Output

`post-deploy` and `collect-metrics` produce the same JSON schema:

```json
{
  "meta": { "region": "...", "release_time": "...", "baseline_window": "...", "current_window": "...", "threshold_pct": 25, "min_baseline": 10, "lambda_count": 21, "api_count": 0, "notes": [...] },
  "exceeded": [ { "resource": "app_x", "type": "Lambda", "metric": "Errors", "statistic": "Sum", "baseline": 1.0, "current": 5.0, "change_pct": 400.0, "status": "changed", "severity": "critical", "exceeded": true } ],
  "within_threshold": [ ... ],
  "low_volume": [ ... ]
}
```

Note: `baseline` and `current` are **per-day rates** for Sum metrics so the two windows are comparable even when their lengths differ.

## Jenkins / CI usage

```bash
scripts/post-deploy --profile <PROFILE> --quiet --exit-code \
  --format md --out post-deploy-report.md
```

Exit codes: `0` clean, `1` medium/high findings, `2` critical findings, `3` script error. The report file becomes a build artifact.

## Discovery

```bash
ls references/*.md
ls references/workflows/*.md
ls scripts/_tests/
```

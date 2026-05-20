# Comparison Modes

Two modes for defining the "before" and "after" windows.

## Release-to-Release

Best for environments with distinct, infrequent deployments (QA, beta, staging, production).

### Anchor function (e.g. policy API) for release time

If every release updates a known Lambda (often **`app_api_handler`** or your env’s policy API name), you can treat **that function’s last code/configuration change** as the release clock instead of scanning all Lambdas in CloudTrail.

**Option A — one API call (fast, good default)**

`LastModified` changes on *any* configuration update (code, env, memory, layers), not only code pushes. For most teams it still tracks “when this service last shipped.”

```bash
scripts/aws-cli --profile <PROFILE> --region <region> \
  lambda get-function-configuration \
  --function-name app_api_handler \
  --output json
```

Read `LastModified` (RFC3339). Compare with the **previous** value from an earlier run, or ask the user “was there a deploy since X?” Use the two most recent meaningful timestamps to set Window A / Window B boundaries (same rules as below).

**Option B — CloudTrail, only this function (code updates only)**

Same CloudTrail `lookup-events` as below, but when scanning raw JSON keep only events whose `Resources[0].ResourceName` equals your anchor (e.g. `app_api_handler`). That isolates **code deploy** times and ignores unrelated config edits.

**When not to use an anchor**

Skip a single-function anchor if that Lambda is **not** deployed on every release (hotfix-only deploys, partial rollouts). Then use multi-function CloudTrail batching or ask the user for the deploy time.

### How to detect deployment times (full fleet)

Query CloudTrail for Lambda code updates. **Use a simple query with no JMESPath filtering** -- complex filters fail silently and return empty results. Get all events, then filter yourself:

```bash
scripts/aws-cli --profile <PROFILE> cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateFunctionCode20150331v2 \
  --start-time <7-days-ago-ISO8601> \
  --end-time <now-ISO8601> \
  --region <region> \
  --output json
```

**Do NOT use `--query` with JMESPath** on CloudTrail commands. The nested structure causes silent failures. Instead:
1. Fetch the raw JSON
2. Look at the `Resources[0].ResourceName` field in each event
3. Match resource names against your target function list yourself

### Extracting resource names from the output

Each event in the `Events` array has this structure:
```json
{
  "EventTime": "2026-04-29T14:35:04-04:00",
  "EventName": "UpdateFunctionCode20150331v2",
  "Resources": [{"ResourceName": "app_bulk_action_container", ...}]
}
```

Scan the output for your target function names. Any event where `Resources[0].ResourceName` matches a function in your target list is a deployment of that function.

### Grouping into deployment batches

Multiple Lambdas are typically deployed together. Group events into batches:
- Events occurring within 30 minutes of each other belong to the same deployment
- Sort all events by time
- Walk through chronologically, starting a new batch when the gap exceeds 30 minutes
- Each batch represents one release

### Defining windows (default)

Let `T` be the latest detected release timestamp (anchor `LastModified` or most recent CloudTrail batch):

- **Window A — Baseline**: `T - 30 days` → `T`
- **Window B — Current**: `T` → **now**

This is the default for all release-to-release runs. It gives a stable 30-day baseline of normal behavior right before the deploy and a fresh post-deploy window that grows as time passes.

If zero deployments are found, fall back to Rolling Baseline mode.

### Example

```
T - 30d                                          T (release)             now
|---------------- Window A (Baseline) -----------|---- Window B ---------|
            30 days of pre-release behavior         post-release behavior
```

### Overrides

The user can override at any time:

- "compare to previous release" → use `scripts/post-deploy --compare-releases` (looks up the two most recent `UpdateFunctionCode` events for the anchor in CloudTrail and sets Window A = `t_prev` → `T`, Window B = `T` → now). Tune the lookback via `--lookback-days N` (default 30).
- "use 14 day baseline" → Window A = `T - 14d` → `T` via `--baseline-days 14`.
- Explicit timestamps → drop down to `scripts/collect-metrics` and pass `--baseline-start/--baseline-end/--current-start/--current-end`.

## Rolling Baseline

Best for environments with frequent deployments (integration, dev) or when CloudTrail shows no clear release boundaries.

### Defining windows

- **Baseline**: daily averages over the past 7 days (configurable; user can say "use 14 days")
- **Current**: last 24 hours (configurable; user can say "last 6 hours")

No CloudTrail query needed. Windows are always relative to now.

### When to use

- Integration environments with multiple deploys per day
- When CloudTrail shows deployments closer than 24h apart
- When the user wants a quick drift check without caring about specific releases
- As a fallback when release-to-release has insufficient data

## Auto-detection

If the user doesn't specify a mode:

1. Query CloudTrail for recent deployments (no JMESPath filtering)
2. Scan the raw output for target function names
3. If target function deployments are found and the two most recent batches are more than 24h apart: use **release-to-release**
4. If deployments are very frequent (< 24h apart) or none found for target functions: use **rolling baseline**
5. Tell the user which mode was selected and why

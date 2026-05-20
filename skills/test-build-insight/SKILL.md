---
name: test-build-insight
description: Test build visibility and analysis -- check pipeline status, E2E test results, build failure investigation, deployment versions, Dependabot alerts, and PR traceability. Use when the user asks about build status, test results, deployment versions, pipeline health, flaky tests, Dependabot alerts, PR info, or wants to trigger E2E runs. Composes jenkins-manager, jira-issues, and github-manager skills.
allowed-tools: Read, Bash(~/.claude/skills/jira-issues/scripts/*), Bash(~/.claude/skills/jenkins-manager/scripts/jenkins-cli:*), Bash(~/.claude/skills/github-manager/scripts/gh:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Prerequisites

This skill composes existing CLI skills. Load each skill to get the correct invocation pattern.

- **jenkins-manager** -- build status, logs, test results, trigger builds. Read `~/.claude/skills/jenkins-manager/SKILL.md` for commands.
- **jira-issues** -- link failures back to tickets. Read `~/.claude/skills/jira-issues/SKILL.md` for the nix shell command.
- **github-manager** -- PR info, commit lookup, Dependabot alerts. Read `~/.claude/skills/github-manager/SKILL.md` for commands. Use `~/.claude/skills/github-manager/scripts/gh` for all `gh` commands.

## Project Configuration

Default project key: **PROJ** (product platform / PRODUCT). When the user says "PRODUCT", use project key `PROJ`.
Default GitHub host for PRODUCT repos: **github.com**, org **your-org**.

## Pipeline Status

### Check Recent Builds for a Repo
Look up the job path in `references/jenkins-jobs.md`, then:
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format toon --toon-max-items 12 builds <JOB-PATH> 10
```

### Get Build Details
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format toon --toon-max-items 12 build-info <JOB-PATH> <BUILD-NUMBER>
```

### Get Build Logs (filtered)
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format toon --toon-max-items 12 logs <JOB-PATH> <BUILD-NUMBER> 'ERROR|WARN|FAIL'
```

### Get Full Console Output
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format text logs <JOB-PATH> <BUILD-NUMBER> --full-logs
```

### Trigger a Build
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli trigger <JOB-PATH> <BRANCH_PARAM>=<branch>
```

## E2E Test Status

Check whether E2E tests are passing, failing, or running for a repo. See `references/workflows/e2e-test-status.md` for full steps.

Quick check:
1. Resolve the e2e job path from `references/jenkins-jobs.md`.
2. Fetch latest build: `jenkins-cli --format json builds <JOB-PATH> 1`.
3. Report result using the interpretation table (SUCCESS=passed, FAILURE=failed, UNSTABLE=some failures, null=running).

For failure details, filter logs:
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format toon logs <JOB-PATH> <BUILD-NUMBER> 'FAIL|ERROR|AssertionError'
```

## Deployment Tracking

### Check Deployment Status
Verify which version is deployed to an environment by checking AWS Lambda timestamps. See `references/workflows/deployment-check.md`.

Uses `references/deployment-config.md` to map repos to Lambda function names per environment, then checks each function's `LastModified` via AWS CLI. Always use `AWS_PROFILE=app_engineer` for all `aws lambda` calls.

### Compare Environments
Compare deployed versions between two environments to identify drift. Collect Lambda timestamps for all functions in both environments and diff.

## GitHub Integration

### Dependabot Alerts
Check open security vulnerabilities for a repo. See `references/workflows/dependabot-alerts.md`.
```
~/.claude/skills/github-manager/scripts/gh api 'repos/<OWNER>/<REPO>/dependabot/alerts?state=open' \
  --hostname github.com \
  --jq '.[] | {number, severity: .security_advisory.severity, package: .dependency.package.name, summary: .security_advisory.summary}'
```

### Find PR for a Commit
Trace a commit SHA back to its originating PR. See `references/workflows/pr-lookup.md`.
```
~/.claude/skills/github-manager/scripts/gh api 'repos/<OWNER>/<REPO>/commits/<SHA>/pulls' \
  --hostname github.com \
  --jq '.[0] | {number, title, state, html_url}'
```

### Get PR Details
```
~/.claude/skills/github-manager/scripts/gh pr view <PR-NUMBER> \
  --repo github.com/<OWNER>/<REPO> \
  --json number,title,state,mergedAt,mergeCommit,headRefOid,headRefName,baseRefName,url
```

## Aggregation Workflow

To build a cross-repo dashboard view:

1. List target repos from `references/jenkins-jobs.md`.
2. For each repo, fetch recent builds: `jenkins-cli --format json builds <JOB-PATH> 5`.
3. Summarize pass/fail/skip per repo and branch.
4. Identify failing tests and map to Jira tickets where possible.
5. Flag flaky tests (tests that alternate pass/fail across recent builds).
6. Report KPIs: overall pass rate, failure trends, repos with degrading health.

## KPI Tracking

Key metrics to report:
- Pass/fail rate per repo and per branch
- Defect density (failures per build)
- Flaky test count and quarantine status
- Deployment version consistency across environments
- Open Dependabot alerts by severity

## Reference Files

- `references/jenkins-jobs.md` -- repo-to-Jenkins-job mapping (paths and branch params)
- `references/deployment-config.md` -- repo-to-Lambda mapping per environment
- `references/workflows/e2e-test-status.md` -- E2E result interpretation workflow
- `references/workflows/deployment-check.md` -- Lambda deployment verification steps
- `references/workflows/dependabot-alerts.md` -- Dependabot alert checking via GitHub API
- `references/workflows/pr-lookup.md` -- PR lookup and commit traceability workflows

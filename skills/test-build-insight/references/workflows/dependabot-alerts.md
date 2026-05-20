# Dependabot Alert Check

Check open Dependabot vulnerability alerts for a repository using the GitHub API.

## Prerequisites

Compose **github-manager** skill. Read `~/.claude/skills/github-manager/SKILL.md` if not yet loaded.

Determine the correct host:
- Internal repos: `github.com`
- Public repos: `github.com`

## Steps

1. **Verify GitHub auth**:
   ```
   scripts/gh auth status --hostname <HOST>
   ```

2. **List open alerts**:
   ```
   scripts/gh api 'repos/<OWNER>/<REPO>/dependabot/alerts?state=open' \
     --hostname <HOST> \
     --jq '.[] | {number, severity: .security_advisory.severity, package: .dependency.package.name, summary: .security_advisory.summary, created_at: .created_at}'
   ```
   Use `~/.claude/skills/github-manager/scripts/gh` as the `scripts/gh` path.

3. **Summarize**:
   - Total open alerts
   - Breakdown by severity (critical, high, medium, low)
   - Package names and advisory summaries
   - Oldest unresolved alert date

## View Single Alert

```
scripts/gh api repos/<OWNER>/<REPO>/dependabot/alerts/<NUMBER> \
  --hostname <HOST> \
  --jq '{number, ghsa: .security_advisory.ghsa_id, package: .dependency.package.name, severity: .security_advisory.severity, patched: .security_vulnerability.first_patched_version.identifier, manifest: .dependency.manifest_path}'
```

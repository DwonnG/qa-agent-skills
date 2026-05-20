# PR Discovery

Scan team repos for merged PRs that are missing both `qa-e2e-complete` and `qa-e2e-skipped` labels.

## Repos to Scan

- `frontend-app`
- `api-service`
- `directory-data`
- `policy-service`

## Discovery Command

For each repo, run:

```bash
~/.claude/skills/github-manager/scripts/gh pr list \
  --repo github.com/your-org/<REPO> \
  --state merged \
  --search "-label:qa-e2e-complete -label:qa-e2e-skipped" \
  --json number,title,mergedAt,headRefName,mergeCommit,url,labels \
  --limit 10
```

## Processing Order

1. Sort results by `mergedAt` descending (most recent first).
2. For each PR, proceed to diff analysis (Step 2).
3. Present a summary table to the user before processing:

```
| # | Repo | PR | Title | Merged |
|---|------|----|-------|--------|
| 1 | api-service | #423 | [PROJ-51944]: Add relay config validation | 2 days ago |
| 2 | frontend-app | #891 | [PROJ-52100]: Update remediation page | 3 days ago |
```

4. In interactive mode, ask the user which PRs to process (or "all").

## Single PR Mode

When given a specific PR (URL or repo + number), skip discovery and go directly to diff analysis. Still check if the PR already has `qa-e2e-complete` or `qa-e2e-skipped` -- if so, inform the user and stop.

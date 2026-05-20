# PR Lookup Workflows

Find and inspect pull requests related to builds, commits, or issues.

## Prerequisites

Compose **github-manager** skill. Read `~/.claude/skills/github-manager/SKILL.md` if not yet loaded. Use `~/.claude/skills/github-manager/scripts/gh` for all `gh` commands.

## Find PR for a Commit

Given a commit SHA, find which PR introduced it:
```
~/.claude/skills/github-manager/scripts/gh api 'repos/<OWNER>/<REPO>/commits/<SHA>/pulls' \
  --hostname github.com \
  --jq '.[0] | {number, title, state, html_url}'
```

If the result is empty, no PR is associated with the commit.

## Get PR Details

Given a PR number, fetch full details:
```
~/.claude/skills/github-manager/scripts/gh pr view <PR-NUMBER> \
  --repo github.com/your-org/<REPO> \
  --json number,title,state,mergedAt,mergeCommit,headRefOid,headRefName,baseRefName,url
```

Key fields to report:
- PR number, title, and state
- Whether merged and merge timestamp
- Head branch and base branch
- Merge commit SHA (useful for deployment tracing)

## Find PRs for a Jira Ticket

Search PRs that reference a Jira issue key. Use `gh pr list` (not `gh search prs` which returns 401 on GHE):
```
~/.claude/skills/github-manager/scripts/gh pr list \
  --repo github.com/<OWNER>/<REPO> \
  --search "<ISSUE-KEY>" \
  --state all \
  --json number,title,state,url \
  --limit 10
```
Note: `gh pr list --json` does not support `mergedAt`. To get merge details, follow up with `gh pr view <NUMBER>` for each matched PR.

## Trace: Commit to Build to Deployment

1. Find the PR for the commit (above).
2. Get the merge commit SHA from the PR details.
3. Find the first build after the merge timestamp using `jenkins-cli builds`.
4. Check if that build succeeded.
5. Cross-reference with deployment config to verify the code is live.

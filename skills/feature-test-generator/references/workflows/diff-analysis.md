# Diff Analysis

Read and analyze a merged PR to understand what changed and determine the appropriate E2E test strategy.

## Steps

### 1. Fetch the PR Diff

```bash
~/.claude/skills/github-manager/scripts/gh pr diff <NUMBER> \
  --repo github.com/your-org/<REPO>
```

If the diff is very large (>500 lines), focus on the file list first:

```bash
~/.claude/skills/github-manager/scripts/gh pr view <NUMBER> \
  --repo github.com/your-org/<REPO> \
  --json files --jq '.files[].path'
```

### 2. Extract the Jira Ticket

Look for `PROJ-XXXXX` in:
1. PR title (most common: `[PROJ-51944]: description`)
2. Branch name (e.g., `PROJ-51944/feature-name`)
3. PR body

If found, fetch ticket details for acceptance criteria:

```bash
jira-cli --format json view <ISSUE-KEY>
```

### 3. Classify the Change

Apply the classification prompt (`references/prompts/change-classification.md`) to the diff.

The classification determines:
- Whether a test is needed (or the PR should be skipped)
- Where the test goes (same repo or cross-repo for `frontend-app`)
- What kind of test (API E2E, UI E2E, or both)

### 4. Output

Present a summary:

```
PR: api-service #423 -- [PROJ-51944]: Add relay config validation
Jira: PROJ-51944 (Story, priority: Medium)
Classification: API behavior change
Changed areas: lambda/policy_api/handler.py, lambda/policy_api/validators.py
E2E target: api-service/end_to_end_tests/tests/policy/
Action: Generate new E2E test
```

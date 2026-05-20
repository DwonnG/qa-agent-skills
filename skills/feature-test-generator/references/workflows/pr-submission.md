# PR Submission

Create a test PR, link it to Jira, and apply the coverage label to the source PR.

## Prerequisites

- Test code has been generated and approved by the user
- Target repo identified (same repo for most, `qa-repo` for `frontend-app` PRs)

## Steps

### 1. Set Up Worktree

Find or clone the target repo, then create an isolated worktree:

```bash
cd <repo-path>
git fetch origin
git checkout main && git pull
git worktree add ../<repo>-PROJ-XXXXX -b PROJ-XXXXX
cd ../<repo>-PROJ-XXXXX
```

### 2. Write the Test

Create or modify the test file(s) in the worktree. If extending an existing file, apply only the additions.

### 3. Commit

Stage specific files only (never `git add -A` or `git add .`):

```bash
git add <test-file-path>
git commit -m "[PROJ-XXXXX]: add E2E test for <feature>

### Summary of the change
Add E2E test covering <what the test verifies>.
Triggered by <source-repo>#<PR-number>.

### Jira ticket
[PROJ-XXXXX](https://jira.example.com/browse/PROJ-XXXXX)
"
```

### 4. Push and Create PR

```bash
git push -u origin PROJ-XXXXX
```

Create the PR using `gh`:

```bash
~/.claude/skills/github-manager/scripts/gh pr create \
  --repo github.com/your-org/<TARGET-REPO> \
  --title "[PROJ-XXXXX]: add E2E test for <feature>" \
  --body "## Summary
E2E test for <feature description>.

Triggered by: <source-repo>#<PR-number> (<source PR URL>)
Jira: [PROJ-XXXXX](https://jira.example.com/browse/PROJ-XXXXX)

## Test Coverage
- <list of scenarios covered>
"
```

### 5. Link to Jira

Add a comment to the Jira ticket linking to the new test PR:

```bash
jira-cli comment PROJ-XXXXX "E2E test PR created: <test PR URL>"
```

### 6. Label the Source PR

Apply `qa-e2e-complete` to the original merged PR:

```bash
~/.claude/skills/github-manager/scripts/gh pr edit <SOURCE-PR-NUMBER> \
  --repo github.com/your-org/<SOURCE-REPO> \
  --add-label "qa-e2e-complete"
```

### 7. Clean Up

Remove the worktree when done:

```bash
cd <repo-path>
git worktree remove ../<repo>-PROJ-XXXXX
```

## Skipped PRs

For PRs classified as `infra`, `docs`, or `refactor`, skip test generation and apply the skip label with a comment:

```bash
~/.claude/skills/github-manager/scripts/gh pr edit <NUMBER> \
  --repo github.com/your-org/<REPO> \
  --add-label "qa-e2e-skipped"

~/.claude/skills/github-manager/scripts/gh pr comment <NUMBER> \
  --repo github.com/your-org/<REPO> \
  --body "QA E2E: skipped -- <reason>. No user-facing behavior change detected."
```

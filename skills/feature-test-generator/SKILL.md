---
name: feature-test-generator
description: Monitors merged PRs across team repos and generates E2E test PRs. Scans for merged PRs missing E2E coverage labels, analyzes the diff, checks for existing tests, and creates test PRs following each repo's established conventions. Use when asked to generate E2E tests for merged PRs, check test coverage gaps, or scan repos for untested changes.
skills:
  - github-manager
  - jira-issues
  - test-generation
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(~/.claude/skills/github-manager/scripts/gh:*), Bash(nix shell "git+https://github.com/your-org/your-jira-cli" -c jira-cli *)
---

Progressive disclosure: keep responses short, expand only on request.

## Dry Run (Default)

All runs are **dry run by default**. Complete Steps 1-4 (discovery, analysis, duplicate check, test generation) and present the proposed test code to the user, but do NOT create worktrees, commit, push, or apply labels. Show the proposed test code, target file path, and target repo, then ask for confirmation.

Only write to repos and apply labels when the user explicitly confirms (e.g., "submit it", "create the PR", "go ahead").

## Prerequisites

This skill composes existing CLI skills for data access:

- **github-manager** -- PR discovery, diff reading, PR creation, label management. Read `~/.claude/skills/github-manager/SKILL.md` for the `gh` command pattern.
- **jira-issues** -- ticket context and comment linking. Read `~/.claude/skills/jira-issues/SKILL.md` for the `jira-cli` command pattern.
- **test-generation** -- reuse test case generation prompts for acceptance criteria analysis.

Default GitHub host: **github.com**, org **your-org**.

## Label Strategy (Opt-Out)

No developer action required. All merged PRs are assumed to need E2E tests.

Labels:
- `qa-e2e-complete` -- applied after a test PR is created or existing coverage is confirmed
- `qa-e2e-skipped` -- applied when no test is needed (infra, docs, pure refactor), with a comment explaining why

## Workflow (5 Steps)

### Step 1: PR Discovery

Scan repos for merged PRs missing both labels. See `references/workflows/pr-discovery.md`.

When the user says "scan for untested PRs" or "check coverage", run discovery across all repos. When given a specific PR, skip discovery and go directly to Step 2.

### Step 2: Diff Analysis and Classification

For each PR, read the diff and classify the change. See `references/workflows/diff-analysis.md` and `references/prompts/change-classification.md`.

Extract the Jira ticket from the PR title or branch name (`PROJ-XXXXX`). Fetch Jira details for acceptance criteria context.

| Classification | Action | Label |
|---------------|--------|-------|
| API or UI behavior change | Generate E2E test | `qa-e2e-complete` |
| Both API + UI | Generate tests in both locations | `qa-e2e-complete` |
| Pure infra (Terraform, CI, Dockerfile) | Skip | `qa-e2e-skipped` |
| Docs only (README, comments) | Skip | `qa-e2e-skipped` |
| Pure refactor (no behavior change) | Skip | `qa-e2e-skipped` |

### Step 3: Duplicate Check

Search the target E2E test directory for existing coverage. See `references/prompts/duplicate-check.md`.

- **No existing test** -- generate new test file
- **Existing test, missing new scenarios** -- extend existing file
- **Fully covered** -- add `qa-e2e-complete` + comment, no new PR

### Step 4: Test Generation

Generate the test using the "read before you write" approach. See `references/prompts/test-scaffolding.md`.

For routing to the correct repo/directory, see `references/repo-test-map.md`. Most repos keep E2E tests in-repo; the agent finds the test directory by exploring. Only `frontend-app` requires cross-repo routing to `qa-repo`.

### Step 5: PR Submission

Create the test PR and apply labels. See `references/workflows/pr-submission.md`.

## Reference Files

- `references/prompts/change-classification.md` -- how to classify a PR diff
- `references/prompts/duplicate-check.md` -- how to check for existing E2E coverage
- `references/prompts/test-scaffolding.md` -- "read before you write" test generation
- `references/workflows/pr-discovery.md` -- scanning repos for unprocessed merged PRs
- `references/workflows/diff-analysis.md` -- reading and analyzing PR diffs
- `references/workflows/pr-submission.md` -- worktree, commit, PR creation, labeling
- `references/repo-test-map.md` -- cross-repo routing rules

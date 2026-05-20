---
name: qa-workflow
description: QA operational workflows -- claim tickets, mark pass/fail, transition through statuses, verify vulnerabilities, check version bumps, validate UI versions, clone release epics, track release testing progress, bulk update test results, and view the QA queue. Use when the user asks to claim a ticket, resolve/fail QA, verify a fix is deployed, check a version bump, set up release testing, check release progress, bulk pass/fail tickets, or see the QA queue. Composes jira-issues, jenkins-manager, and github-manager skills.
allowed-tools: Read, Bash(~/.claude/skills/jira-issues/scripts/*), Bash(~/.claude/skills/jenkins-manager/scripts/jenkins-cli:*), Bash(~/.claude/skills/github-manager/scripts/gh:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Dry Run (Default)

All write operations (transitions, comments, field updates, bulk operations) require **explicit user confirmation** before executing. Present the proposed action and wait for approval. Read-only operations (verification checks, status lookups, queue views, progress reports) run immediately.

## Prerequisites

This skill composes existing CLI skills. All CLI commands must be invoked via their nix shell wrappers or absolute shim paths. Load each skill to get the correct invocation pattern.

- **jira-issues** -- ticket operations (update, transition, comment, search). Read `~/.claude/skills/jira-issues/SKILL.md` for the nix shell command.
- **jenkins-manager** -- build and test status. Read `~/.claude/skills/jenkins-manager/SKILL.md` for commands. Use `~/.claude/skills/jenkins-manager/scripts/jenkins-cli`.
- **github-manager** -- PR merge status, commit lookup. Read `~/.claude/skills/github-manager/SKILL.md` for commands. Use `~/.claude/skills/github-manager/scripts/gh`.

## Project Configuration

Default project key: **PROJ** (product platform / PRODUCT). When the user says "PRODUCT", use project key `PROJ`.
All PROJ tickets belong to the your organization. Sub-teams are identified by sprint name prefixes: TeamA, TeamB, TeamE, TeamC, TeamD.

## Ticket Lifecycle

### Claim a Ticket
Claiming a ticket does three things: assigns you, sets you as Validator, and sets Test Result to In Progress.

```
jira-cli update <ISSUE-KEY> --assignee <USERNAME> --field '<VALIDATOR_FIELD_ID>={"name":"<USERNAME>"}' --field '<TEST_RESULT_FIELD_ID>={"id":"<IN_PROGRESS_OPTION_ID>"}'
```

- Validator (<VALIDATOR_FIELD_ID>): user picker, requires `{"name":"<USERNAME>"}`
- Test Result (<TEST_RESULT_FIELD_ID>): option field, In Progress = id `<IN_PROGRESS_OPTION_ID>`

### Mark QA Pass
1. Set Test Result to Pass.
2. Transition ticket to Resolved.
3. Add a structured pass comment using wiki markup (see `references/comment-templates.md`).
```
jira-cli update <ISSUE-KEY> --field '<TEST_RESULT_FIELD_ID>={"id":"<PASS_OPTION_ID>"}'
jira-cli transition <ISSUE-KEY> --to resolved
jira-cli comment <ISSUE-KEY> "<PASS-COMMENT>"
```

### Mark QA Fail
1. Set Test Result to Fail.
2. Transition ticket to Reopened.
3. Add a structured fail comment with environment, issue, repro steps, expected/actual (see `references/comment-templates.md`).
```
jira-cli update <ISSUE-KEY> --field '<TEST_RESULT_FIELD_ID>={"id":"23520"}'
jira-cli transition <ISSUE-KEY> --to reopened
jira-cli comment <ISSUE-KEY> "<FAIL-COMMENT>"
```

### Transition Ticket
Available transitions: backlog, grooming, open, in_progress, resolved, blocked, pr_pending_review, reopened, closed, qa, staging_qa.
```
jira-cli transition <ISSUE-KEY> --to <STATUS>
```
See `references/jira-transitions.md` for when to use each.

## QA Queue Overview

View the current QA queue: unclaimed tickets, active validations, recently failed, and incoming from dev. See `references/workflows/qa-queue.md`.

Quick check for unclaimed tickets:
```
jira-cli search --jql 'project = PROJ AND status in (QA, "Beta QA") AND Sprint in openSprints() AND Validator is EMPTY ORDER BY fixVersion ASC'
```

## Release Testing

### Release Epic Setup
Clone a release testing template epic for a new version. See `references/workflows/release-epic.md`.

### Release Testing Progress
Track QA validation progress for all tickets linked to a release epic. See `references/workflows/release-testing-progress.md`.

Reports total issues, breakdown by status (passed, failed, in QA, not started, blocked, in dev), and percentage complete.

### Bulk Test Result Update
Update test results for multiple tickets at once. See `references/workflows/bulk-test-results.md`.

Supports bulk pass, bulk fail, and bulk claim operations. Always presents a dry run summary before executing.

## Verification Workflows

### Vulnerability Verification
End-to-end verification that a vulnerability fix is deployed and working. See `references/workflows/vulnerability-verification.md`.

Steps:
1. Fetch issue details and linked PRs.
2. Confirm PR is merged via `gh pr view`.
3. Check code is deployed to target environment via `jenkins-cli`.
4. Verify E2E tests pass.
5. Optionally resolve the ticket with a verification comment.

### Version Bump Verification
Verify a version bump is deployed across repos. See `references/workflows/version-bump-verification.md`.

### UI Version Verification
Validate the deployed UI shows the expected version. See `references/workflows/ui-version-verification.md`.

## Jira Custom Fields

These custom field IDs are specific to the PROJ project:

| Field | Custom Field ID | Values |
|-------|----------------|--------|
| Test Result | <TEST_RESULT_FIELD_ID> | Pass `{"id":"<PASS_OPTION_ID>"}`, Fail `{"id":"23520"}`, In Progress `{"id":"<IN_PROGRESS_OPTION_ID>"}` |
| Validator | <VALIDATOR_FIELD_ID> | User picker: `{"name":"<USERNAME>"}` |
| Team(s) | <JIRA_CUSTOM_FIELD> | Not reliably populated; use sprint name prefix to identify sub-team |

## Reference Files

- `references/workflows/` -- step-by-step verification and operational procedures
- `references/comment-templates.md` -- wiki markup pass/fail comment formats
- `references/jira-transitions.md` -- transition names and usage guidance
- `references/jql-templates.md` -- reusable JQL queries for queue, progress, and search

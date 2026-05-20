---
name: bug-triage
description: Triage Jira bugs using a 3-step analysis workflow -- keyword extraction, related issue search and ranking, and structured triage with priority/team/root-cause assignment. Use when the user asks to triage bugs, analyze defects, find root causes, generate reproduction steps, or scan the QA queue. Composes jira-issues, jenkins-manager, and github-manager skills for data access.
allowed-tools: Read, Bash(~/.claude/skills/jira-issues/scripts/*), Bash(~/.claude/skills/github-manager/scripts/gh:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Dry Run (Default)

All triage runs are **dry run by default**. Complete Steps 1-3 (discovery, search, analysis) and present results to the user, but do NOT write anything to Jira. Show the proposed comment and field updates, then ask for confirmation before proceeding.

Only write to Jira when the user explicitly confirms or requests a live run (e.g., "apply it", "write it back", "go ahead").

## Prerequisites

This skill composes existing CLI skills for data access. All CLI commands must be invoked via their nix shell wrappers as documented in those skills. Load the jira-issues skill to get the correct nix shell invocation pattern.

- **jira-issues** -- search bugs, fetch details, update fields, add comments. Read `~/.claude/skills/jira-issues/SKILL.md` for the nix shell command pattern.
- **jenkins-manager** -- fetch test failure context
- **github-manager** -- fetch related PRs and code context

## Project Configuration

Default project key: **PROJ** (product platform / PRODUCT). See `references/jira-config.md` for custom fields and priority mappings. When the user says "PRODUCT", use project key `PROJ`.

## Triage Workflow (3 Steps)

### Step 1: Bug Discovery

Scan for untriaged bugs using the jira-issues skill's nix shell command:
```
jira-cli --format json search --jql 'project = <PROJECT> AND issuetype = Bug AND (labels NOT IN ("ai-triaged-bug") OR labels is EMPTY) AND created >= "-1d" ORDER BY created DESC'
```

For a single bug, fetch full details:
```
jira-cli --format json view <ISSUE-KEY>
```

Collect: summary, description, component, reporter, labels, versions, recent comments.

### Step 2: Related Issue Search and Ranking

Extract keywords from the bug (see `references/prompts/keyword-extraction.md`):
- Exact identifiers: service names, error codes, API names
- Keywords: broader technical terms
- Concepts: functional area phrases

Run up to 5 JQL search strategies (see `references/workflows/dynamic-search.md`):
1. Summary terms AND-ed on Stories/Tasks/Epics
2. Resolved bugs matching summary terms
3. Open bugs matching summary terms
4. Same component
5. Linked or epic-related keys

Deduplicate results. Cap candidate pool at 25.

Rank candidates by relevance (see `references/prompts/relevance-ranking.md`). Keep only scores 7+, max 8 results.

### Step 3: Structured Triage

Perform the triage analysis (see `references/prompts/bug-triage.md`):
- Chain-of-thought priority reasoning (P1-P4)
- Team assignment with confidence score
- Root cause area identification
- Investigation hints and recommended actions
- Duplicate detection

Team resolution order:
1. Existing Team(s) field on the bug
2. Assignment patterns from related issues
3. Analysis inference
4. Component map fallback (see `references/team-mappings.md`)

### Write Back to Jira

Post a wiki-markup triage comment (see `references/comment-templates.md`):
```
jira-cli comments add <ISSUE-KEY> "<COMMENT>"
```

Update fields:
```
jira-cli update <ISSUE-KEY> --priority "<PRIORITY>" --labels "ai-triaged-bug"
```

## Additional Analysis

For deeper investigation on a specific bug:
- **Root cause analysis** -- see `references/prompts/root-cause-analysis.md`
- **Reproduction steps** -- see `references/prompts/reproduction-steps.md`
- **Comment summary** -- see `references/prompts/comment-summary.md`

## Reference Files

- `references/prompts/` -- analysis prompt patterns
- `references/workflows/dynamic-search.md` -- 5-strategy JQL search
- `references/team-mappings.md` -- team/PO/QA assignments
- `references/jql-templates.md` -- JQL query patterns
- `references/comment-templates.md` -- wiki markup comment formats
- `references/jira-config.md` -- custom fields and priority definitions

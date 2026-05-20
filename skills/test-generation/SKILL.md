---
name: test-generation
description: Generate and update test plans and test cases from Jira epics/stories and Confluence feature docs. Use when the user asks to create a test plan, update a test plan, generate test cases, or add QA checks to a ticket. Composes jira-issues, confluence-pages, and github-manager skills.
allowed-tools: Read, Bash(nix shell "git+https://github.com/your-org/your-jira-cli" -c jira-cli *), Bash(nix shell "git+https://github.com/your-org/your-jira-cli" -c confluence-cli *), Bash(scripts/gh:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Dry Run (Default)

All write operations require **explicit user confirmation** before executing. For test plans, present a summary (objective, scope, test case count) before uploading to Confluence. For test cases, show the proposed QA section before updating the ticket.

## Prerequisites

This skill composes existing CLI skills for data access. All CLI commands must be invoked via their nix shell wrappers. Load each skill to get the correct nix shell invocation pattern.

- **jira-issues** -- fetch epics, stories, and linked issues. Read `~/.claude/skills/jira-issues/SKILL.md` for the nix shell command.
- **confluence-pages** -- fetch Feature Canvas and Test Plan Template. Read `~/.claude/skills/confluence-pages/SKILL.md` for the nix shell command.
- **github-manager** -- fetch PRs for code context. Read `~/.claude/skills/github-manager/SKILL.md` for the nix shell command.

## Test Plan Workflow

Generate a full test plan as a Confluence page. The page body must be **Confluence storage format** (XHTML with Confluence macros). See `references/workflows/test-plan-workflow.md` for the full format spec.

1. Identify the epic or story to plan. Fetch via `jira-cli --format json view <EPIC-KEY>`.
2. Fetch linked stories: `jira-cli --format json search --jql '"Epic Link" = <EPIC-KEY>'`.
3. Extract Confluence URLs from descriptions and comments. Fetch each via `confluence-cli --format json view <PAGE-ID>`.
4. Fetch the **live Test Plan Template** from Confluence space `ENG`, title `Test Plan Template`. Use the fetched template structure as the output format -- do NOT use the local template file.
5. Extract acceptance criteria from stories and analyze requirements.
6. Generate test cases in Confluence expand macros (see `references/prompts/test-cases.md` -- "Test Plan Format" section). Each scenario in its own expand panel with a Given/When/Then table.
7. Generate a Mermaid flow diagram wrapped in a Confluence code macro if the feature has conditional logic (see `references/prompts/flow-diagram.md`).
8. Present the completed plan summary for review.
9. Upload to Confluence after user confirms. Default space: `ENG` (same as the template). If the user specifies a different space or parent page, use that instead. **Important**: Write the HTML body to a temp file first (`/tmp/testplan-body.html`), then use `--body "$(cat /tmp/testplan-body.html)"` to avoid shell argument length limits. See `references/workflows/test-plan-workflow.md` step 8 for the exact pattern. After upload, let the user know they can move the page in Confluence if needed.
10. **Required**: Add a comment on the epic linking to the new test plan page: `jira-cli comment <EPIC-KEY> "Test Plan: <CONFLUENCE-URL>"`.

## Test Plan Update

Update an existing test plan when the epic has changed (new stories, updated acceptance criteria, scope changes).

1. Fetch the epic and linked stories (same as Test Plan Workflow steps 1-2).
2. Search Confluence for an existing test plan: `confluence-cli --format json search "Test Plan <EPIC-KEY>" --space <SPACE>`.
3. If found, fetch the existing plan content via `confluence-cli --format json view <PAGE-ID>`.
4. Compare the current Jira state against the existing plan:
   - New stories not covered in the plan
   - Updated acceptance criteria
   - Removed or closed stories still listed
   - Missing test cases for new scope
5. Present a summary of proposed changes (added, updated, removed sections).
6. After user confirms, update the Confluence page via `confluence-cli pages update --id <PAGE-ID> --body "<HTML>"`.

If no existing plan is found, fall back to the full Test Plan Workflow.

## Test Case Generation (Single Ticket)

Generate concise test cases and add them to the Jira ticket description.

1. Fetch ticket details via `jira-cli --format json view <ISSUE-KEY>`.
2. Check if the description already contains a QA section (`*QA*`, `h2. QA`, or `## QA` from a previous run).
   - If yes, treat as an **update**. Show the existing checks, then show only what changed: added lines prefixed with `+`, removed lines prefixed with `-`. Do NOT regenerate the full section -- show a diff.
   - If no, treat as a **create** -- generate a new `*QA*` section.
3. Enrich context when available:
   - Extract Confluence URLs from description/comments and fetch linked docs.
   - Search for related PRs via `gh pr list --search "<ISSUE-KEY>"` and review changed files.
4. Generate ONLY a flat concise checklist (5-8 items). Rules:
   - No sub-headers, no categories, no grouping -- just a flat list under the QA heading.
   - No Gherkin, no scenarios.
   - Consolidate repetitive checks (e.g., "Verify feature works in all 11 environments" instead of one item per environment).
   - Each item is one clear, independently verifiable check.
   - Use **Jira wiki markup**, not markdown. Jira does not render `##` or `- [ ]`.
   - Use `*QA*` (bold) as the section label, not a heading.
   ```
   *QA*
   * Verify <check>
   * Verify <check>
   ```
5. Present the proposed `*QA*` section (or diff) for review.
6. After user confirms, update the ticket description using `jira-cli update`.

## Reference Files

- `references/prompts/test-cases.md` -- test case format (concise for tickets, Confluence expand macros for plans)
- `references/prompts/flow-diagram.md` -- Mermaid diagram generation
- `references/prompts/risk-analysis.md` -- risk assessment (used in test plans)
- `references/prompts/epic-analysis.md` -- epic scope analysis (used in test plans)
- `references/workflows/test-plan-workflow.md` -- end-to-end plan generation
- `references/workflows/feature-ingestion.md` -- Jira + Confluence data gathering

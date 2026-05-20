# What This Skill Can Do

This skill generates scenario-level or detailed end-to-end test plans by combining Confluence, Jira, GitHub, and optional local code context.

Use this skill when you need to:

- build a test plan for a feature or system change
- combine design pages, Jira work items, and code examples
- generate detailed testcase bodies for execution planning

## Common Things You Can Ask For

- Generate a high-level system test plan.
- Generate a full detailed test plan with testcase bodies.
- Use Jira-linked PR artifacts as implementation context.
- Include local codebase patterns when a repo path is available.

## Typical Outputs

- scenario matrix
- execution-ready testcase sections
- assumptions and source gaps
- saved markdown output when requested

## If You Are Not Sure Where To Start

- Provide at least one Confluence page or Jira key.
- Add GitHub examples when similar automation already exists.
- Add a local repo path only if local code should shape the plan.

## Recommended Prompt Shape

```text
@testplan-generator Generate a full detailed end-to-end test plan with testcase bodies.

Confluence: <page-url> [repeatable]
Jira: <issue-url-or-key> [repeatable]
GitHub: <repo-or-path-url>
Local codebase path: <optional-local-path>
Save it to: <optional-output-file.md>
```

If you want one combined plan in a single pass, say that explicitly:

```text
Coverage rules:
- preserve all source-backed scenarios from Confluence and Jira
- use local codebase only to enrich automation mapping and regression hotspots
- do not drop source-backed scenarios just because they are not present in local tests
- if scenarios are merged, explain what was merged and why
```

If the provided Jira items have tagged PRs or commits, the skill can recover:
- PR title and URL
- changed repositories
- commit SHAs and headlines
- changed file paths

Those artifacts are used to improve:
- regression scope
- integration coverage
- changed-component hotspot detection

## Quick Examples

Scenario-level only:

```text
@testplan-generator Generate a scenario-level test plan.

Confluence: https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401923270/FE+SystemTest
Jira: PROJ-50974
```

Detailed plan with all sources:

```text
@testplan-generator Generate a full detailed end-to-end test plan with testcase bodies.

Confluence: https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401923270/FE+SystemTest
Confluence: https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401924000/FE+Rollout
Jira: https://jira.example.com/browse/PROJ-50974
Jira: https://jira.example.com/browse/PROJ-51058
GitHub: https://github.com/your-org/qa-repo/tree/main/e2e_api_tests/tests/inline_mode
Local codebase path: /path/to/repo/tests
Save it to: generated-testplan-filter-engine.md
```

Detailed plan with preserved source coverage plus local automation mapping:

```text
@testplan-generator Generate a full detailed end-to-end test plan with testcase bodies.

Coverage rules:
- preserve all source-backed scenarios from Confluence and Jira
- use the local codebase path only to improve automation grouping, fixture reuse, assertions, and regression hotspots
- do not reduce or compress source-backed coverage because local tests are narrower
- if scenarios are merged, explain what was merged and why

Confluence: <page-url>
Jira: <issue-url-or-key>
Local codebase path: /path/to/repo/tests
Save it to: generated-testplan.md
```

Jira artifact-driven example:

```text
@testplan-generator Generate a full detailed end-to-end test plan with testcase bodies.

Jira: PROJ-51684
Jira: PROJ-51873
GitHub: https://github.com/your-org/example-service/tree/main
```

In that mode, the skill should try to recover linked PR and commit artifacts from the Jira keys and use changed files as additional regression evidence.

When only partial inputs are available:

```text
@testplan-generator Generate a draft test plan with testcase bodies.

Confluence: <page-url>
Jira: missing
GitHub: missing
```

## Important Rules

- GitHub URL and local codebase path are separate inputs.
- Multiple Confluence pages and Jira items are allowed.
- Jira-linked PR and commit artifacts may be used as additional evidence when they can be resolved.
- Commit artifacts improve regression and changed-component coverage, but they do not override Confluence or Jira product intent.
- Local codebase evidence should enrich automation mapping, not replace Confluence/Jira product coverage.
- Do not assume local repo access from a GitHub URL.
- If details are missing from sources, the output should say `Unknown`.
- The skill should still attempt a useful draft when some inputs are missing.

## Setup

- `config.md` - prerequisite setup and verification for Confluence, Jira, and GitHub access

## Common Read-Only Commands

```bash
# Confluence
@confluence-pages View page <PAGE-ID> in markdown

# Jira
@jira-issues View <KEY>
@jira-issues Search with a specific JQL query

# GitHub Enterprise auth
@github-manager auth status --hostname github.com

# GitHub contents API
@github-manager Read a repository path or PR context on github.com

# Jira-linked PR and commit artifacts
scripts/jira-commit-artifacts <KEY> [<KEY> ...]
```

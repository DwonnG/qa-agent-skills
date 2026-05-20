# Commit Artifacts

Use this guidance when the provided Jira items appear to have linked pull requests or implementation commits.

## Goal

Recover implementation artifacts that improve test planning:
- changed files
- touched components or services
- commit messages that mention the Jira key
- PR titles and URLs

Treat commit artifacts as regression and integration evidence, not as product truth.

## How To Extract

Run the helper on one or more Jira keys:

```bash
scripts/jira-commit-artifacts PROJ-51684 PROJ-51058
```

The helper:
- reads the Jira item
- tries to infer the target repo from Jira fields such as `Repo_Url`
- falls back to host-level PR search when Jira does not expose a repo URL
- searches GitHub PRs for the Jira key
- fetches commit and file metadata from matching PRs

## What To Extract

- PR title and URL
- repo name
- merged or open state
- commit SHAs and commit headlines
- changed file paths
- changed modules, packages, or services implied by those paths

## How To Use In The Plan

- add regression cases for touched modules
- add integration coverage where commit artifacts show cross-component edits
- strengthen configuration, migration, or dependency scenarios when infra or requirements files changed
- call out areas where code changed but no automated tests were provided as examples

## Guardrails

- Do not let commit artifacts override Confluence feature intent.
- If commit artifacts conflict with Jira acceptance criteria, call out the conflict.
- If no matching PRs are found, say so and continue without them.

# GitHub Patterns

Use GitHub examples to learn how similar tests are organized and automated. Treat this as implementation evidence, not product truth.
Use this only for the GitHub repo or path the user provides. Do not replace it with local filesystem inspection unless the user separately provides a local codebase path.

## Typical Inputs

The user may provide:
- a repo URL
- a tree path URL
- a directory path within a known repo

Example:
- `https://github.com/your-org/qa-repo/tree/main/e2e_api_tests/tests/inline_mode`

## Repo And Path Extraction

From a GitHub tree URL, extract:
- host
- owner
- repo
- ref
- path

Then inspect contents:

Use the shared `github-manager` skill to inspect repository contents.

For enterprise hosts that need it:

Use the shared `github-manager` skill against your GitHub host (github.com or GitHub Enterprise).

## What To Look For

- naming conventions for tests
- suite granularity
- setup and fixture patterns
- environment variables
- assertions and expected outputs
- neighboring tests for related flows

## How To Use GitHub Evidence

- borrow structure, not behavior
- identify which scenarios are already automated in nearby areas
- propose new automation in the same style as existing suites
- call out reuse opportunities such as fixtures, helpers, or data builders

## Red Flags

- tests that reflect outdated behavior
- tests from a different flow mode than the requested feature
- directory names that look similar but belong to another subsystem

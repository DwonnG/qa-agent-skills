# Repo Test Map

Most repos keep their E2E tests in-repo. The agent finds the E2E test directory by exploring the repo structure. This file only documents the cases that need explicit routing.

## Cross-Repo: frontend-app -> qa-repo

PRs in `frontend-app` do NOT have E2E tests in the same repo. UI E2E tests live in:

```
qa-repo/e2e-test-suite/tests/functional/<area>/
```

The agent must clone/pull `qa-repo` (from `github.com/your-org/qa-repo`) and write the test there.

To determine `<area>`, match the frontend-app page path to the functional test directory:
- `pages/messages` -> `tests/functional/messages/`
- `pages/configuration` -> `tests/functional/configuration/`
- `pages/impacts`, `pages/trends` -> `tests/functional/insights/`
- `pages/remediation` -> `tests/functional/remediation/`
- `pages/administration` -> `tests/functional/administration/`
- `pages/policy` -> `tests/functional/provisioning_and_policy/`

If unsure, list the subdirectories under `tests/functional/` and pick the best match.

## Dual Directory: directory-data

`directory-data` has two E2E test directories:

- `test/end_to_end_tests/` -- API E2E tests (pytest, API client fixtures)
- `test/ui_tests/test_cases/` -- UI E2E tests (Playwright, page objects in `test/ui_tests/pages/`)

The agent picks the right one based on the PR diff. If the change affects both API and UI behavior, generate a test in each.

Note: `test/etd/` contains API client wrapper classes used by fixtures. Do NOT generate tests there.

# Coverage Heuristics

Rules for flagging inadequate unit/integration test coverage in source PRs.

## File Classification

Classify each changed file in the PR diff:

| Pattern | Classification |
|---------|---------------|
| `test_*.py`, `*_test.py`, `*_test.go`, `*.spec.ts`, `*.spec.js` | Test file |
| `*.robot` | Test file (Robot) |
| `conftest.py`, `*_fixture*` | Test infrastructure |
| `*.md`, `*.txt`, `*.rst`, `CHANGELOG*`, `LICENSE*` | Documentation |
| `Dockerfile*`, `Jenkinsfile*`, `Makefile`, `*.yaml`, `*.yml` (CI/infra) | Infrastructure |
| `.gitignore`, `CODEOWNERS`, `*.lock` | Configuration |
| Everything else | Production code |

## Heuristics

### Flag: No Tests for Production Changes

If the PR modifies **2+ production files** and **0 test files**, flag it.

Exception: single-line config changes, version bumps, or import-only changes.

### Flag: Test-to-Code Ratio

If the PR adds/modifies significantly more production lines than test lines (rough ratio > 5:1), note it as a concern.

### Flag: New Functions Without Tests

If the diff adds new public functions/methods/endpoints and no corresponding test functions, flag it.

### Pass: Adequate Coverage Signals

- PR includes test files alongside production changes
- PR status checks show test stages passed
- Changes are purely to existing tested code paths (refactor)

## PR Status Checks

Use the GitHub API to check PR status:
```bash
gh pr view <PR_NUMBER> --repo <REPO> --json statusCheckRollup
```

Look for test-related checks:
- `ci/product-api-e2e-tests-pr-gate` (API Robot tests)
- Build/test stages in the repo's CI

A passing test check is a positive signal but does not replace the diff analysis.

## Output Format

When flagging, be specific about which files lack coverage:

```
⚠️ Unit/Integration Test Coverage Gap

PR #123 in api-service modifies 5 production files but adds no unit tests.

Files changed without test coverage:
- src/handlers/remediation.py (42 lines added)
- src/services/policy_engine.py (18 lines modified)

PR status checks: ✅ Build passed, ⚠️ No test stage found

Dev team should review test coverage before QA sign-off.
```

When coverage is adequate:

```
✅ Unit/Integration Test Coverage: Adequate
PR #123 includes test changes alongside production modifications.
Test stages: ✅ All passing
```

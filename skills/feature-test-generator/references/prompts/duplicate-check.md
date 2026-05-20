# Duplicate Check

Before generating a test, verify whether existing E2E tests already cover the change.

## Search Strategy

Search the target E2E test directory using two approaches:

### 1. Jira Ticket Search

```bash
grep -r "PROJ-XXXXX" <target-e2e-dir>/
```

If the ticket key appears in a test file docstring, that test was written for this feature.

### 2. Feature Keyword Search

Extract 2-3 key terms from the PR title and changed file names, then search:

```bash
grep -r "<keyword>" <target-e2e-dir>/
```

Look for test functions, class names, or comments that reference the same feature area.

### 3. File Path Matching

If the PR changes `lambda/policy_api/validators.py`, look for test files in the corresponding test area (e.g., `tests/policy/`).

## Decision

After searching, decide:

- **No matches found** -- Generate a new test file. Proceed to test scaffolding.
- **Partial match** -- An existing test file covers the same feature area but not the specific scenarios from this PR. Extend the existing file by adding new test functions.
- **Full match** -- An existing test already exercises the exact behavior changed in this PR. Skip generation. Apply `qa-e2e-complete` and add a comment noting the existing test file and function.

## Output

Report to the user:

```
Duplicate check: <target-e2e-dir>/
- Jira ticket search: [found/not found] -- <file if found>
- Keyword search: [N matches] -- <files if found>
- Decision: [new file / extend existing / skip]
```

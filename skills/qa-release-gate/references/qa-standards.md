# QA Coding Standards

These standards apply to both evaluating existing tests and generating new tests.

## Read Before You Write (Mandatory)

Before generating any test code, you MUST do all of the following:

1. **Read the target directory's `conftest.py`** (pytest) or `__init__.robot` / suite setup (Robot Framework). Note every fixture, parametrization, and CLI option (e.g., `--source`, `--env`, `--browser`, `--role`).
2. **Read at least one existing test file** in the same functional area as the feature being tested.
3. **Read every helper definition you plan to call.** Apply the [Definition-Read Rule](#definition-read-rule) to every imported symbol the new test will use (`generate_bearer_token_for_user`, `GET`, `POST`, `PATCH`, `DELETE`, `enable_feature_toggle`, `get_secret`, etc.).
4. **Read the page-object file** the new test will rely on (e.g., `tests/application/app/cmd_pages/<page>.py` for `e2e-test-suite`). Apply the [Page-Object Readiness Rule](#page-object-readiness-rule) to confirm every method you plan to call already exists.
5. **Read `tox.ini` / `pyproject.toml`** for the registered marker list. Apply the [Marker Registration Rule](#marker-registration-rule) if you need a new marker.

Rules:
- Match the style exactly: class-based vs function-based, import ordering, assertion patterns, fixture usage
- Reuse existing conftest fixtures for general infrastructure (`app`, `env_consts`, role-based logins). For per-test cleanup, prefer a file-local fixture over `try/finally` inside the test body — see [Cleanup via Fixtures](#cleanup-via-fixtures)
- Do NOT assume conventions — let the existing code teach you
- Do NOT generate code that imports symbols you have not opened and read

## Definition-Read Rule

For every function, class, fixture, or method the new test imports or calls, you must have read its definition in this session before pushing. Pattern-matching against test names in another file is not enough — helper signatures and side effects matter.

Apply this rule to:
- API helpers (`GET`, `POST`, `PATCH`, `DELETE`, `generate_bearer_token_for_user`, etc.) — keyword names and positional order vary
- Login / setup helpers (`enable_feature_toggle`, `get_secret`, `app.login`, etc.) — many require a logged-in UI before running
- Page-object methods (every `page_object.method(...)` call site)
- Conftest fixtures referenced as parameters

If the helper's source is not on disk in a workspace you can read (e.g., installed from pip), grep for usages in existing tests and copy a working call exactly.

## Page-Object Readiness Rule

For UI E2E tests, the test PR must be runnable on its own. Page-object methods are part of the test PR — they are never deferred to a follow-up PR or to the human reviewer.

Before generating a UI test:

1. List every `page_object.method()` call you plan to make.
2. `Grep` the page-object file for each method name.
3. For any method that does not exist, add it to the page-object file in the same PR, modeled on adjacent methods. Selector strategy, in order of preference:
   - `data-testid` from the source-repo PR (mirror the identifier exactly).
   - A stable composition of ARIA role + accessible name, label association, or unique CDS slot.
   - As a last resort, a tight CSS/XPath relative to a stable parent. Add a brief comment explaining the selector choice.

   If selectors are genuinely brittle, *also* post a Jira comment asking the dev team to add a `data-testid` so the test can be tightened later — but still ship the test using the best available selector.

A draft PR whose body says "review and implement page object methods before merging" is not acceptable — it is a misleading artifact, not a test.

## Marker Registration Rule

If you need a new `@pytest.mark.<name>` (or a Robot tag not previously used), register it in the same PR:
- pytest: add to `[pytest] markers` in `tox.ini` or `markers` in `pyproject.toml`.
- Robot: add to suite-level `Test Tags` or document in the suite header.

Otherwise reuse an existing marker. Pytest will warn (`PytestUnknownMarkWarning`) for unregistered markers and CI may fail if `--strict-markers` is enabled.

## Hard Sleep Budget

`time.sleep` is a last-resort tool, not a first instinct. The default budget for a new test file is **0**. Always start with an explicit wait (`WebDriverWait`, page-object `wait_until_…` helper, Robot `Wait Until …` keyword).

A `time.sleep` call is permitted only when:
1. An explicit-wait approach was tried and proved insufficient (the agent must be able to name the API or helper that was tried).
2. The synchronization target is an async operation with no observable end-state — a fire-and-forget animation, a settle window for which no DOM signal exists, etc.

Each `time.sleep` call must have an inline comment naming (a) the specific async operation it is waiting on, and (b) the explicit-wait API that was tried first.

Hard cap: **2** `time.sleep` calls per file. More than two is a code smell — refactor with explicit waits or move the synchronization into the page object before pushing.

## Cleanup via Fixtures

Per-test state restoration (feature flags off, tenant policy reset, files deleted, modals closed, etc.) belongs in a pytest fixture, not in a `try/finally` wrapper inside the test body. The test body should read as a linear sequence of "act and assert" — scaffolding belongs in fixtures.

If conftest does not already provide the cleanup you need, define a file-local fixture in the test module. This does not violate the "do not invent new fixtures unless truly necessary" guidance from [Read Before You Write](#read-before-you-write-mandatory) — per-test cleanup *is* the truly-necessary case. Reuse existing fixtures (`app`, `env_consts`, role-based logins) for general infrastructure; create file-local fixtures for cleanup that is specific to this test file.

A `try/finally` block inside a test body is a code smell. Reviewers should see assertions, not error handling. The one exception is when a single test needs ordered cleanup of multiple things and a single fixture is harder to read than the inline ordering — and even then, prefer a fixture with a stack-based teardown.

## File Layout

Test files should read top-to-bottom in this order:

1. Module docstring (with the Jira ticket link).
2. Imports.
3. Module-level constants.
4. Module-level helper functions (login, navigation, custom waits, verification helpers).
5. File-local fixtures.
6. Test class.

Within those sections, helpers must be defined **above** their first call site. Python class methods do not require this for execution, but linear reading order matters for reviewers.

Helpers that do not use `self` belong at module scope, not as methods on the test class. A "method" that takes `self` only because it lives inside a class is misleading — make it a module-level function. Reserve class-method status for helpers that genuinely need `self` (shared mutable state across tests in the class, which is itself a smell — prefer fixtures).

## Correctness

- Does the test cover the ticket's scenario and acceptance criteria?
- Are assertions validating actual behavior (not just "page loaded" or "no error")?
- Are negative/edge cases covered?

## Test Design

- Page Object Model followed (Selenium)?
- Keywords properly abstracted (Robot Framework)?
- No raw selectors/locators in test files?
- Per-test cleanup uses a fixture, not `try/finally` inside the test body? See [Cleanup via Fixtures](#cleanup-via-fixtures).
- File layout follows the order in [File Layout](#file-layout) (helpers above tests, no `self`-less methods on the test class)?
- Tests independent and idempotent?

## Reliability

- Hard sleeps (`time.sleep`) vs explicit waits (`WebDriverWait`, Sleep with condition in Robot)? Enforce the [Hard Sleep Budget](#hard-sleep-budget).
- Flaky patterns — race conditions, brittle XPath/CSS, order-dependent tests?
- Retry/rerun markers (`@pytest.mark.flaky`, `--reruns`) used appropriately?

## Maintainability

- Hard-coded URLs, credentials, or environment-specific values that should come from `constants/` or env config?
- Duplicated selectors or flows across tests?
- Naming conventions followed per the sub-project?

## Code Quality

- No unnecessary comments
- No flake8 or autopep8 violations
- No soft asserts — all assertions must be hard asserts that fail the test immediately

## Security

- No real credentials or tokens in test data
- Sensitive data pulled from `constants/env/secrets`, not inline
- No accidental logging of auth tokens

## Framework Conventions

- Correct pytest markers (per `tox.ini` marker list); apply the [Marker Registration Rule](#marker-registration-rule) for any new ones
- Robot tags match suite conventions
- `xdist` loadgroup markers for tests that need serial execution
- Allure annotations where expected

## Data Management

- Test data setup and teardown handled properly
- No leftover state (policies, users, config) between tests
- Fixtures scoped appropriately (`session` vs `function`)

## Scope

- Is the change expanding beyond the ticket?
- Are unnecessary files being modified?

## AC Traceability

Before generating tests, build an acceptance-criteria → test mapping:

1. Extract every bullet from the ticket's `Acceptance Criteria` (or equivalent) section.
2. For each AC, name the test method (or specific assertion within a test) that will cover it.
3. If an AC has no covering test, you must use one of these specific resolutions — no others are permitted:
   - **Add a test for it.** This is the default.
   - **Cite an existing test that already covers it.** Name the file path and test method (e.g., `tests/functional/configuration/test_dlp_configuration.py::test_dlp_widget_visible`), and read that test in this session to confirm it actually covers the AC. A guess does not count.
   - **Mark it skipped with one of these allowed rationales** (each must include the named existing test or pipeline that covers the AC, where applicable):
     - `backend-only behavior, covered by API E2E in <repo>/<path>::<test>`
     - `infra/config-only AC with no executable behavior`
     - `manual-only AC (e.g., visual design review) — not automatable`

   The bare phrase "out of scope" is **not acceptable**. If you cannot fit an AC into one of the three resolutions above, you have not finished the AC analysis — go back to step 1.
4. Include the mapping in the PR body under an `### AC coverage` section.

This step is mandatory. "Generate one test per AC bullet I happen to remember" is exactly how ACs get missed.

## Pre-Push Validation (Mechanical Gate)

Every touched file must pass these checks before you push. Fix every error — do not push anything that fails any of these.

```bash
# Syntax: file parses as valid Python
python3 -c "import ast, sys; ast.parse(open(sys.argv[1]).read())" <file>

# Unused imports / undefined names
python3 -m pyflakes <file>

# Style + import ordering
python3 -m flake8 --import-order-style=google <file>

# (pytest test files only) Test must be collectible
python3 -m pytest --collect-only -q <test-file>
```

`pytest --collect-only` is the most important of these — it executes module-level code, so import-time bugs (missing helpers, wrong fixture names, unregistered markers in `--strict-markers` mode) surface immediately.

`pytest --collect-only` is **mandatory**. If your sandbox does not have the test repo's environment installed, install it first using the repo's documented setup:
- `tox -e <env> --notest` — installs deps without running tests
- `devbox install` — if the repo uses devbox
- `pip install -r requirements*.txt` in a venv
- whatever the repo's `README.md` / `CONTRIBUTING.md` / `Makefile` documents

"I can't install" is not an acceptable answer when the test repo has a documented environment. Setting up the environment is part of running the gate.

The `python3 -m py_compile <file>` + grep-resolve fallback is permitted **only** when the environment genuinely cannot be reproduced (e.g., it requires production credentials your agent does not have). When you take that fallback, document it explicitly in the PR body under a `### Validation` section so reviewers know to re-run collection locally before merging.

A test that does not collect is not a test. It is a draft that wastes the reviewer's time.

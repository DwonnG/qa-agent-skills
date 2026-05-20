# Test Conventions

Framework-specific conventions for TeamA team test suites.

## e2e-test-suite (pytest + Selenium)

**Location**: `qa-repo/e2e-test-suite/`

### Structure
- `tests/functional/<domain>/` — test files organized by feature area
- `tests/application/` — page objects (Page Object Model)
- `tests/constants/` — timeout constants, selector patterns (`GET_BY_TEST_ID`)
- `tests/helper/` — env, user, and AWS helpers
- `conftest.py` (root) — fixtures: `app`, `session`, `env_consts`, CLI options (`--source`, `--env`, `--browser`, `--role`)

### Markers (from tox.ini)
`first`, `last`, `smoke`, `ces`, `blocked_connections`, `remediation`, `automatic_remediation`, `bulk_remediation`, `reclassification`, `bulk_reclassification`, `dlp`, `dkim`, `message_rules`, `provisioning`, `insights`, `user_flow`, `login`, `rbac`, `download_files`, `send_email`, `permissions`, `securex`, `policy_exception_rules`, `message_modification`

### Parallel Execution
- `@pytest.mark.xdist_group(name="policy-sensitive")` for tests that modify policies
- `@pytest.mark.xdist_group(name="policy-insensitive")` for others
- Tests MUST be independent and not depend on execution order

### Reporting
- Allure: `@allure.title(...)`, `@allure.story(...)`, screenshot on failure (via conftest)
- File logs under `test_reports/`

### Key Patterns
- `BasePage` class for common Selenium operations
- `DriverWrapper` from `selen-kaa` for element interaction
- `GET_BY_TEST_ID` for `data-testid` selectors
- Timeout constants: `ONE_SEC_TIMEOUT`, `TWENTY_SEC_TIMEOUT`, etc.

## e2e_api_tests (Robot Framework)

**Location**: `qa-repo/e2e_api_tests/`

### Structure
- `tests/<domain>/` — `.robot` suite files
- `etd/application/` — Python libraries and keywords

### Tags
- Suite-level: `Test Tags` in `.robot` files
- Common: `smoke`, `sanity`, `regression`, `wip`, `BATS`, `inline_mode`, `gov`, `trajectory`
- Feature-specific: `PROJ-XXXXX_...` for traceability
- Excluded by default: `wip`, `external_api`, `auto_remediation_policy`

### Execution
- `pabot` for parallel execution with `RetryFailed:2`
- Default tag inclusion: `regression` (configurable via Jenkins params)
- Gov cloud: `-v gov_cloud:True`

### Reporting
- `RobotPublisher` in Jenkins
- Posts to csdashboard via `apirobot3.py`

### Linting
- `robocop` for Robot Framework linting
- `robotidy` for formatting
- `black`, `flake8`, `mypy` for Python libraries (via tox)

## directory-data (Dual — in-repo)

**Location**: `directory-data/`

### API Tests
- `test/end_to_end_tests/` — pytest with API client fixtures
- `test/etd/` — API client wrappers (do NOT put tests here)

### UI Tests
- `test/ui_tests/test_cases/` — Playwright tests
- `test/ui_tests/pages/` — page objects

## docs-repo (in-repo)

**Location**: `docs-repo/tests/`

Explore the test directory to discover conventions before generating.

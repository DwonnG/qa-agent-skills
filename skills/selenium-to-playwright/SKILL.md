---
name: selenium-to-playwright
description: Convert Selenium 3 page objects and pytest tests into pytest-playwright code, with test segmentation analysis to split bulky tests into smaller, parallelizable flows. Use when asked to convert, migrate, modernize, or segment E2E tests.
allowed-tools: Read, Edit, Bash(find:*), Bash(rg:*), Bash(git:*), Bash(gh:*)
---

# Selenium-to-Playwright Converter

Progressive disclosure: keep responses short, expand only on request.

## Two Workflows

### 1. Convert a file

```
Convert <file_path> to Playwright
```

### 2. Analyze a file for segmentation

```
Segment <file_path>
```

Both can be combined: `Convert and segment <file_path>`.

## Convert Workflow

1. Read the target file.
2. Classify it:
   - **Page object** (under `tests/application/`) — convert class methods per [references/base-page-equivalents.md](references/base-page-equivalents.md).
   - **Test file** (under `tests/functional/`) — run segmentation first, then convert per [references/mapping-guide.md](references/mapping-guide.md).
   - **Conftest** (any `conftest.py`) — convert fixtures per [references/fixture-model.md](references/fixture-model.md).
3. Apply transformations:
   - Replace Selenium imports with Playwright imports.
   - Replace `BasePage` / `DriverWrapper` / legacy driver-wrapper patterns with Playwright `page` object — see [references/base-page-equivalents.md](references/base-page-equivalents.md).
   - Convert selectors per [references/selector-strategy.md](references/selector-strategy.md).
   - Eliminate `time.sleep`, `WebDriverWait`, `expected_conditions` per [references/common-patterns.md](references/common-patterns.md).
   - Convert fixtures per [references/fixture-model.md](references/fixture-model.md).
4. Preserve: class/method names, test names, pytest markers, `xdist_group` annotations, docstrings.
5. Flag anything that cannot be auto-converted (complex JS executions, wrapper methods without clear equivalents, API-only fixtures).
6. **Dry run by default** — show the converted code for review. Only write the file when the user confirms.
7. After the user confirms and files are written, optionally create a **draft PR**:
   - Ask the user for a ticket key if not already provided.
   - Branch: `<TICKET>-playwright-migration-<feature-area>` (e.g. `PROJ-1234-playwright-migration-checkout`).
   - Commit message: `refactor(<area>): migrate <file(s)> from Selenium to Playwright`.
   - PR description: what was converted, segmentation changes, and items needing manual review.
   - If the user declines the draft PR, skip this step.

## Segment Workflow

1. Read the target test file (or all test files in a directory).
2. Apply heuristics from [references/test-segmentation.md](references/test-segmentation.md):
   - Size: >50 lines or >10 assertions per test function.
   - Multiple flows: tests that login, navigate to multiple pages, or validate unrelated features.
   - Setup-heavy: >40% of the test body is setup/teardown that should be a fixture.
   - Sequential dependency: tests relying on execution order or shared mutable state.
   - xdist opportunity: tests missing `xdist_group` that could parallelize, or tests in a group that don't need coordination.
   - Redundancy: tests overlapping significantly with others in the same file/directory.
3. Output a segmentation report:
   - Which tests to split and proposed function names for each piece.
   - Which setup to extract into fixtures.
   - Which tests to add/change `xdist_group` on.
   - Which tests are candidates for removal.
4. If converting at the same time, apply the splits in the converted output.

## Typical Layout (pytest + Selenium 3)

Adapt paths to your repository; this skill targets the common enterprise pattern:

- `tests/application/base_page.py` — shared `BasePage` with Selenium helpers.
- `tests/application/driver_wrapper.py` — wrapper around the raw WebDriver.
- `tests/application/application.py` — facade: login, navigation, page factory methods.
- `tests/application/session.py` — browser session setup (Chrome/Firefox via `webdriver-manager`).
- `tests/application/app/pages/` — concrete page objects.
- `tests/application/app/elements/` — widget/component objects.
- `tests/functional/` — feature-area tests.
- `tests/conftest.py` — root fixtures: `app`, `session`, env constants, CLI options, xdist setup.
- `tests/constants/constants.py` — timeouts and `GET_BY_TEST_ID = '[data-testid="{}"]'`.

## Key dependencies being replaced

| Current | Replacement |
|---|---|
| `selenium~=3.141.0` | `playwright` (via `pytest-playwright`) |
| Legacy driver wrapper | Removed — Playwright `page` object |
| `webdriver-manager` | Removed — Playwright bundles browsers |
| `WebDriverWait` + `expected_conditions` | Removed — Playwright auto-waits |
| `time.sleep` | Removed — Playwright auto-waits |

## What stays the same

- `pytest` as test runner (with `pytest-playwright` plugin).
- `pytest-xdist` for parallelism.
- `allure-pytest` for reporting (if already in use).
- Existing pytest markers and API helper modules where they are not WebDriver-specific.

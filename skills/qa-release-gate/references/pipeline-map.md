# Pipeline Map

Maps TeamA source repos to QA-owned Jenkins pipelines for regression scanning and deployment verification.

## Jenkins Base URL

`https://jenkins.example.com/jenkins/etd`

## Pipeline Mapping

### e2e-test-suite (Cross-repo UI E2E — pytest + Selenium) — QA-owned

| Environment | Jenkins Job Path | Trigger |
|-------------|-----------------|---------|
| Integration | `team_platform/platform-testing/e2e-python-integration` | Scheduled |
| Integration (CES) | `team_platform/platform-testing/e2e-python-integration-ces` | Scheduled |
| Integration PR Gate | `team_platform/platform-testing/e2e-python-integration-pr-gate` | PR merge |
| QA (CES) | `team_platform/platform-testing/e2e-python-qa-ces` | Scheduled |
| QA Qualifier Smoke | `team_platform/platform-testing/e2e-python-app_qualifier-smoke-test` | Scheduled |

Uses `qaTestPipeline(...)` from your-jenkins-shared-library. Results via Allure.

### api-service E2E (in-repo — pytest)

| Environment | Jenkins Job Path | Trigger |
|-------------|-----------------|---------|
| Integration | `team_platform/api-service/python-end-to-end-tests` | Scheduled / PR |

Runs `end_to_end_tests/` in the api-service repo.

### directory-data E2E (in-repo — pytest + Playwright)

| Environment | Jenkins Job Path | Trigger |
|-------------|-----------------|---------|
| Integration | `team_platform/directory-data/end-to-end-test` | Scheduled / PR |

Runs `test/end_to_end_tests/` (API) and `test/ui_tests/` (UI) in the directory-data repo.

### docs-repo E2E (in-repo)

| Environment | Jenkins Job Path | Trigger |
|-------------|-----------------|---------|
| Integration | `team_platform/docs-repo/end-to-end-test` | Scheduled / PR |

Runs `tests/` in the docs-repo repo.

### jurrassic-ui-tests (Robot Framework) — QA-owned

| Environment | Jenkins Job Path | Trigger |
|-------------|-----------------|---------|
| Integration | `team_platform/platform-testing/jurassic-robo-e2e-python-integration` | Scheduled |
| QA | `team_platform/platform-testing/jurassic-robo-e2e-python-qa` | Scheduled |

Uses Robot Framework with `RobotPublisher`.

## Repo to Pipeline Relevance

| Source Repo | E2E Pipelines to Check |
|-------------|------------------------|
| api-service | `team_platform/api-service/python-end-to-end-tests`, `team_platform/platform-testing/e2e-python-integration`, `team_platform/platform-testing/e2e-python-integration-ces` |
| policy-service | `team_platform/platform-testing/e2e-python-integration`, `team_platform/platform-testing/e2e-python-integration-ces` |
| frontend-app | `team_platform/platform-testing/e2e-python-integration`, `team_platform/platform-testing/e2e-python-integration-ces` |
| directory-data | `team_platform/directory-data/end-to-end-test`, `team_platform/platform-testing/e2e-python-integration`, `team_platform/platform-testing/e2e-python-integration-ces` |
| docs-repo | `team_platform/docs-repo/end-to-end-test` |

The two cross-repo UI E2E pipelines (`e2e-python-integration` and `e2e-python-integration-ces`) should **always** be checked when any deployment hits integration that could affect the UI.

## Pipeline Ownership

| Owner | Pipelines |
|-------|-----------|
| **QA** | All `platform-testing/*` pipelines (e2e-python-integration, e2e-python-integration-ces, jurassic). The "integration" in the name refers to the **integration environment**, not integration-level testing. |
| **Dev** | In-repo pipelines (`api-service/python-end-to-end-tests`, `directory-data/end-to-end-test`, `docs-repo/end-to-end-test`) |

When reporting action items for pipeline failures, attribute them to the correct owner.

## Querying Pipeline Results

Use the `jenkins-manager` skill:

```bash
# Get recent builds
jenkins-manager: builds <job-path> 10

# Get build logs filtered for failures
jenkins-manager: logs <job-path> <build-number> 'FAIL|ERROR|Exception'
```

When checking for regressions, compare the most recent build result to the 3-5 builds before it. A test that was passing and is now failing is a regression signal.

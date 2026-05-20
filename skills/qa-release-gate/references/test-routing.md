# Test Routing

Maps TeamA source repos and change types to the correct target test suite and repo.

## Routing Table

| Source Repo | Change Type | Target Repo | Target Directory | Framework |
|-------------|-------------|-------------|------------------|-----------|
| api-service | API changes | api-service | `end_to_end_tests/` | pytest |
| api-service | UI-impacting changes | qa-repo | `e2e-test-suite/tests/functional/<area>/` | pytest + Selenium/Playwright |
| policy-service | API/backend changes | api-service | `end_to_end_tests/tests/<area>/` | pytest |
| policy-service | UI-impacting changes | qa-repo | `e2e-test-suite/tests/functional/<area>/` | pytest + Selenium/Playwright |
| frontend-app | Any | qa-repo | `e2e-test-suite/tests/functional/<area>/` | pytest + Selenium/Playwright |
| directory-data | API changes | directory-data | `test/end_to_end_tests/` | pytest |
| directory-data | UI changes | directory-data | `test/ui_tests/test_cases/` | Playwright |
| docs-repo | Any | docs-repo | `tests/` | In-repo |

## policy-service Routing Decision

policy-service is a backend API service. Route based on what the change affects:

- **API/backend changes** (Lambda handlers, API logic, data processing, bulk operations, trajectory): Route to `api-service/end_to_end_tests/` — these are API-level E2E tests that hit the endpoints directly without a browser. Faster, more stable, and pinpoint the exact failure.
- **UI-impacting changes** (changes that alter what the user sees in the frontend-app — response shapes consumed by UI, new UI-facing features): Route to `qa-repo/e2e-test-suite/` — browser-based tests that validate the end-to-end user experience.

When in doubt, prefer the API E2E test — it provides faster, more reliable regression detection for backend changes.

## policy-service Area Mapping (api-service/end_to_end_tests/)

Match the changed policy-service module to the api-service API E2E test area:

- Bulk remediation → `tests/email_actions/bulk_remediation/`
- Bulk reclassification → `tests/email_actions/bulk_reclassification/`
- Remediation → `tests/email_actions/remediation/`
- Reclassification → `tests/email_actions/reclassification/`
- Calendar remediation → `tests/email_actions/calendar_remediation/`
- Trajectory / message counting → `tests/email_actions/` (or matching sub-area)
- Auth / token handling → `tests/auth/`
- Policy evaluation → `tests/policy/`
- Admin operations → `tests/admin/`
- Provisioning → `tests/provisioning/`
- XDR integration → `tests/xdr/`

If unsure, list subdirectories under `end_to_end_tests/tests/` and pick the best match.

## api-service Area Mapping

Match the changed module to the test area:

For API tests (api-service/end_to_end_tests/):
- Policy-related changes → `tests/policy/`
- Email actions (remediation, reclassification, bulk) → `tests/email_actions/<sub-area>/`
- Auth changes → `tests/auth/`
- Admin operations → `tests/admin/`
- Provisioning → `tests/provisioning/`
- XDR integration → `tests/xdr/`

For UI-impacting tests (e2e-test-suite):
- Match to `tests/functional/<domain>/` based on the feature area affected

If unsure, list subdirectories under the target test path and pick the best match.

## frontend-app Area Mapping

All frontend-app changes route to `qa-repo/e2e-test-suite/tests/functional/<area>/`. Match the changed component to the test area:

- Policy configuration UI → `tests/functional/configuration/`
- Remediation UI → `tests/functional/remediation/`
- Reclassification UI → `tests/functional/reclassification/`
- Inline mode UI → `tests/functional/configuration/inline/`
- Dashboard / insights → `tests/functional/insights/`
- Login / auth UI → `tests/functional/login/`
- Provisioning UI → `tests/functional/provisioning/`
- DLP UI → `tests/functional/dlp/`

If unsure, list subdirectories under `e2e-test-suite/tests/functional/` and pick the best match.

## directory-data Dual Directory

`directory-data` has two E2E test directories:

- `test/end_to_end_tests/` — API E2E tests (pytest, API client fixtures)
- `test/ui_tests/test_cases/` — UI E2E tests (Playwright, page objects in `test/ui_tests/pages/`)

Pick based on the PR diff. If the change affects both API and UI, generate a test in each.

Note: `test/etd/` contains API client wrapper classes used by fixtures. Do NOT generate tests there.

## Skip Conditions

Skip E2E test generation (noted in the summary comment) for:
- Pure infrastructure changes (Terraform, CI, Dockerfile) with no behavior change
- Documentation-only changes (README, comments)
- Pure refactors with no behavior change
- Version bump / release tracking tickets
- Dependabot vulnerability fixes (dependency version bumps)

For all skip conditions, still perform **deployment verification** — confirm terraform applied and the repo's E2E pipelines passed after deployment.

## Deployment Verification (for infra/release/Dependabot tickets)

Even when E2E test generation is skipped, verify the deployment succeeded by checking terraform status and repo-mapped E2E pipelines:

### 1. Terraform deployment
- Confirm the terraform apply completed (see `terraform-check.md`)

### 2. E2E tests — did the deployed code pass end-to-end tests?

Check the E2E pipelines mapped to the affected repo:

| Source Repo | E2E Pipelines to Check |
|-------------|------------------------|
| api-service | `api-service/python-end-to-end-tests`, `platform-testing/e2e-python-integration`, `platform-testing/e2e-python-integration-ces` |
| policy-service | `platform-testing/e2e-python-integration`, `platform-testing/e2e-python-integration-ces` |
| frontend-app | `platform-testing/e2e-python-integration`, `platform-testing/e2e-python-integration-ces` |
| directory-data | `directory-data/end-to-end-test`, `platform-testing/e2e-python-integration`, `platform-testing/e2e-python-integration-ces` |
| docs-repo | `docs-repo/end-to-end-test` |

All paths are under `team_platform/`.

Find the most recent build **after the deployment date** and check pass/fail.

### 3. Report status
- **VERIFIED**: Terraform applied + all mapped E2E pipelines passed after deployment
- **PARTIAL**: Terraform applied + E2E pipelines have pre-existing failures (not caused by this deploy)
- **FAILED**: New E2E failures appeared after deployment

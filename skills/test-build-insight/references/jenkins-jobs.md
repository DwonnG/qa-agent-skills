# Jenkins Job Mapping

Maps repositories to their Jenkins job paths on the PRODUCT Jenkins instance.

## Job Paths

| Repo | Job Type | Jenkins Path | Branch Param |
|------|----------|-------------|--------------|
| api-service | e2e | team_platform/api-service/python-end-to-end-tests | service_branch |
| api-service | integration | team_platform/api-service/python-integration-tests | service_branch |
| api-service | pr_gate | team_platform/api-service/api-service-pr-gate | service_branch |
| directory-data | e2e | team_platform/directory-data/end-to-end-test | directory_data_branch |
| directory-data | pr_gate | team_platform/directory-data/pr-gate | directory_data_branch |
| policy-service | pr_gate | team_platform/policy-service/policy-service-pr-gate | service_branch |
| qa-repo | e2e | team_platform/platform-testing/e2e-python-integration | app_branch |
| qa-repo | api_e2e | team_platform/platform-testing/api-e2e-integration-nightly | app_branch |
| qa-repo | api_e2e_qa | team_platform/platform-testing/api-e2e-qa-nightly | app_branch |
| qa-repo | e2e_staging | team_platform/platform-testing/e2e-python-staging-manual | app_branch |
| qa-repo | e2e_qa | team_platform/platform-testing/e2e-python-qa-manual | app_branch |
| qa-repo | pr_gate | team_platform/platform-testing/e2e-python-integration-pr-gate | app_branch |
| qa-repo | api_pr_gate | team_platform/platform-testing/api-e2e-pr-gate | app_branch |
| qa-repo | sanity | team_platform/platform-testing/api-e2e-sanity-test | app_branch |

## Notes

- **policy-service** does not have a dedicated E2E test job. The policy-service E2E path from the legacy MCP config (`team_platform/policy-service/end-to-end-test`) no longer exists. Use `policy-service-prgate` for build checks.
- **platform-testing** is the primary test automation folder. It contains environment-specific jobs (integration, qa, beta) and inline-mode variants.
- All paths are relative to the Jenkins PRODUCT instance root.

## Usage

Pass the Jenkins Path directly to `jenkins-cli builds` or `jenkins-cli build-info`:
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli builds team_platform/api-service/python-end-to-end-tests 10
```

To trigger a build with a specific branch:
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli trigger team_platform/api-service/python-end-to-end-tests service_branch=feature-branch
```

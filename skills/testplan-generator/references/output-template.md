# Output Template

Use this structure for the generated plan.

## Feature Summary

- what the feature does
- who it affects
- major dependencies

## Sources Used

- Confluence: list each materially used page title and URL, or `missing`
- Jira: list each materially used epic/issue key and URL, or `missing`
- Jira-linked commit artifacts: PR URLs and changed repos, or `missing`
- GitHub: repo/path URL or `missing`
- Local codebase path: user-provided path or `missing`

## Assumptions and Missing Inputs

- list assumptions explicitly
- note which missing source would most improve confidence

## Test Scope

- core functional scenarios
- negative cases
- permission and role cases
- integration and dependency cases
- regression-sensitive areas

## Out of Scope

- separate deferred coverage from unsupported behavior

## Test Scenarios

For each scenario include:
- `ID`
- `Title`
- `Why`
- `Priority`
- `Source`
- `Manual/Automation`

When the source material supports it, organize scenarios into meaningful groups such as:
- policy lifecycle and persistence
- request and response contract
- rule-type coverage
- action-type coverage
- persistence and metadata validation
- mailbox-visible end-to-end validation
- negative and resilience validation
- logging, auditability, and observability

## Test Data and Environment Needs

- tenants, policies, roles, fixtures, mail samples, or provider setup

## Automation Candidates

- immediate candidates
- follow-up candidates
- reusable helpers or suites

## Risks and Open Questions

- missing requirements
- ambiguous behavior
- operational or environment blockers

## Detailed Test Cases

- required whenever the user asks for a full detailed end-to-end plan
- expand every materially distinct scenario, not just a representative subset
- use the exact Confluence test-template testcase structure:
  - `Title`
  - `Pre-condition`
  - `Test Case Steps`
  - `Expected Behaviour`
  - `Pass/Fail Criterion`
  - `Teardown`
- detailed testcases must be execution-ready, not generic expansions
- if the evidence supports it, testcase steps should name the configured rule or policy, the message send or API action, and the observable validations in mailbox, journal, stored-message, delivery-status, API, or logs
- for mail-processing features, include mailbox-visible end-to-end cases rather than only component-level cases

## Confluence Page Body

- always include a final Confluence storage-format body ready for upload
- preserve the same scope and testcase coverage as the generated plan
- keep testcase sections aligned to the Confluence test-template structure

## Saved File

- include only when the user asked for local file output
- report the final workspace path

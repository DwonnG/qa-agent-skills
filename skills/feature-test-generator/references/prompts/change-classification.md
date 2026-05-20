# Change Classification

Given a PR diff, classify the change to determine if an E2E test is needed and where it should go.

## Input

- List of changed files with their diffs
- PR title and description
- Jira ticket details (if available)

## Classification Rules

Analyze the changed files and their content. Assign ONE primary classification:

**API behavior change** -- New or modified endpoints, request/response handling, business logic in lambdas or services. Indicators: changes to handler files, API route definitions, request validators, response formatters, database queries that affect API output.

**UI feature/page change** -- New or modified user-facing pages, components, or interactions. Indicators: changes to pages/, components/, containers/, CSS/styles, UI test selectors.

**Both API + UI** -- Changes span both backend logic and frontend presentation. Common in full-stack features.

**Pure infra** -- Only CI/CD, Terraform, Docker, build configs, deployment scripts. No application logic changes. Indicators: only files in jenkins/, terraform/, .github/, Dockerfile, Makefile, deployment-configs/.

**Docs only** -- Only README, comments, docstrings, changelog entries. No functional code changes.

**Pure refactor** -- Code restructuring with no behavior change. Indicators: renames, moves, import reorganization, type annotations, linting fixes, dead code removal. No new functionality, no changed API contracts, no modified UI behavior.

## Output

Return:
- `classification`: one of `api`, `ui`, `both`, `infra`, `docs`, `refactor`
- `skip`: true if `infra`, `docs`, or `refactor`; false otherwise
- `skip_reason`: brief explanation if skipping (used in the label comment)
- `affected_areas`: list of functional areas touched (e.g., "policy validation", "remediation page")
- `test_target`: which E2E directory the test should go to (see repo-test-map.md for cross-repo cases)

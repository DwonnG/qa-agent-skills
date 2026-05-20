---
name: testplan-generator
description: Generate feature test plans by combining one or more Confluence design or feature-canvas pages, one or more Jira items such as an epic plus child or related issues, and GitHub evidence such as similar automated tests, implementation code, README files, or adjacent docs. Use when the user wants a test plan, system test plan, regression scope, scenario matrix, or automation plan for a feature even if some of those inputs are missing.
skills: confluence-pages, jira-issues, github-manager
allowed-tools: Read, Edit, Bash(scripts/jira-commit-artifacts:*), Bash(find:*), Bash(rg:*), Bash(sed:*)
---

Progressive disclosure: keep responses short, expand only on request.

## Dry Run (Default)

All write operations require **explicit user confirmation** before executing. For test plans, present a summary (objective, scope, test case count) before uploading to Confluence. For test cases, show the proposed QA section before updating the ticket. For test plan updates, show the diff of changes before writing.

## Critical Constraint

**`jira-commit-artifacts` is the only local entrypoint this skill owns.** Confluence, Jira, and GitHub access come from the shared `confluence-pages`, `jira-issues`, and `github-manager` skills rather than duplicated local wrappers.

If the user asks `help`, `usage`, or `@testplan-generator help`, return a short usage guide first. Point to `references/commands/README.md` for copy-paste examples, then continue only if the user provides inputs or asks for generation.

Use this skill to generate a test plan from up to five evidence sources:
- one or more Confluence design docs or feature canvas pages
- one or more Jira items such as an epic, story, child issues, or related issues
- Jira-linked PR and commit artifacts when they can be resolved from the provided Jira items
- GitHub paths with similar prior automated tests, implementation code, README files, or adjacent docs
- Optional local codebase path with similar tests or implementation context
- Detailed testcase bodies using a consistent Confluence-ready test-template structure when requested

This skill should still attempt a useful test plan when one or more sources are missing.
When multiple evidence sources are provided, preserve the full source-backed product/system coverage first, then layer automation mapping and implementation hints on top. Do not narrow or compress Confluence/Jira coverage just because GitHub or local codebase evidence is present.

## Environment

```bash
scripts/jira-commit-artifacts <KEY> [<KEY> ...]
```

The shim handles nix shell startup automatically. No separate `nix shell` command is needed.
All `scripts/` paths are relative to this skill's installation directory.

Use the Confluence workflow from `confluence-pages`, the Jira workflow from `jira-issues`, and the GitHub workflow from `github-manager`.

## Credentials

This is a composite skill. It depends on separately configured Confluence, Jira, and GitHub CLI access.

- Use `references/commands/config.md` for the required setup order and safe verification commands.
- `@confluence-pages whoami` verifies Confluence access.
- `@jira-issues whoami` verifies Jira access.
- `@github-manager auth status --hostname github.com` verifies GitHub Enterprise access.

## Required Inputs

Ask for these inputs explicitly:

1. Confluence feature canvas or design page list
   Example:
   `https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401923270/FE+SystemTest`
   Multiple pages are allowed when the feature is split across design, system test, rollout, or dependency pages.

2. Jira epic or Jira list
   Example:
   `https://jira.example.com/browse/PROJ-50974`
   Multiple Jira items are allowed, such as an epic plus child stories or a primary Jira plus related issues.

3. GitHub path for similar existing tests, development code, README files, or adjacent docs
   Example:
   `https://github.com/your-org/qa-repo/tree/main/e2e_api_tests/tests/inline_mode`

GitHub input is not limited to test directories. It may also point to:
- a repo root
- a service or package directory
- a README or markdown doc path
- a code path that reveals behavior, dependencies, configuration, or request/response shapes

4. Local codebase path for similar existing tests or implementation context
   Example:
   `/path/to/repo/tests`

5. Output preference
   Ask whether the user wants:
   - scenario-level plan only
   - full detailed end-to-end plan with testcase bodies

If the user asks for a full detailed end-to-end plan with testcase bodies, treat that as an instruction to expand every materially distinct scenario in `Test Scenarios` into a full testcase body. Do not stop after a representative subset.

6. File output preference
   Ask whether the generated plan should also be written to a local markdown file in the workspace.
   If yes, ask for the target path. If the user does not care, propose a reasonable default filename.

If any input is missing:
- state what is missing
- continue with the available sources
- label assumptions clearly
- generate a draft test plan instead of blocking

## Usage Examples

Minimal usage:

```text
@testplan-generator Generate a scenario-level test plan.

Confluence: <page-url>
Jira: <issue-url-or-key>
```

Detailed usage with all sources:

```text
@testplan-generator Generate a full detailed end-to-end test plan with testcase bodies.

Confluence: https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401923270/FE+SystemTest
Confluence: https://your-org.atlassian.net/wiki/spaces/ENG/pages/1401924000/FE+Rollout
Jira: https://jira.example.com/browse/PROJ-50974
Jira: https://jira.example.com/browse/PROJ-51058
GitHub: https://github.com/your-org/qa-repo/tree/main/e2e_api_tests/tests/inline_mode
Local codebase path: /path/to/repo/tests
Save it to: generated-testplan-filter-engine.md
```

If the user wants better automation mapping or broader coverage, ask for the optional local codebase path explicitly instead of inferring it from a GitHub URL.

If the user provides both source material and a local codebase path, treat the local codebase as additive evidence only:
- preserve all materially distinct source-backed scenarios from Confluence and Jira
- use the local codebase to improve automation grouping, fixture reuse, assertion style, and regression hotspots
- do not replace or collapse source-backed scenarios merely because the local tests are narrower

If the user provides a GitHub path that is not a test directory:
- use it to improve scope discovery, dependency understanding, API and behavior inference, and regression hotspots
- inspect nearby README files, package structure, config files, and representative implementation files when relevant
- do not let implementation details override explicit Confluence or Jira behavior

## Workflow

1. Gather the available inputs and output mode.
   Ask for all missing source inputs in one prompt. Also ask whether the user wants to provide a local codebase path, whether they want a full detailed end-to-end plan, and whether the plan should be written to a local workspace file.

2. Read the Confluence source when available.
   Prefer the exact page URL or page id. Support multiple pages. If a page is a hub page, read useful child pages as needed.

Use the shared `confluence-pages` skill to read the relevant pages in markdown form.

3. Fetch the live Test Plan Template from Confluence.
   Retrieve the team template from the `ENG` space (title: `Test Plan Template`) via the shared `confluence-pages` skill. Use the fetched template structure as the output format. The Confluence version is the source of truth and may have been updated by the team. If the template cannot be fetched, fall back to the structure in `references/output-template.md`.

4. Read the Jira source when available.
   Support multiple Jira items. View the epic, issue, or provided Jira list first, then find child work items or linked scope items when needed.

Use the shared `jira-issues` skill to read the Jira issue and any related search results.

Use `references/jira-patterns.md` for candidate JQL patterns.

If multiple Confluence pages or Jira items are provided:
- read the user-supplied sources first
- merge overlapping requirements and deduplicate scenarios
- prefer the most specific source for behavior details
- call out conflicts explicitly in `Assumptions and Missing Inputs`
- keep all materially used pages and Jira items in `Sources Used`

5. Read Jira-linked PR and commit artifacts when available.
   If the provided Jira items have tagged pull requests or commit-linked implementation work, extract those artifacts and use them to sharpen regression scope, integration coverage, and changed-component awareness.

```bash
scripts/jira-commit-artifacts <KEY> [<KEY> ...]
```

Use `references/commit-artifacts.md` for what to extract and how to use it in the plan.

6. Read the GitHub source when available.
   Inspect the target repo, path, and nearby relevant files to learn both feature scope and automation patterns.
   If the provided GitHub path is a test path, use it for naming, fixture, suite, and assertion patterns.
   If the provided GitHub path is an implementation or docs path, use it for API shapes, behavior clues, dependencies, config knobs, and likely regression hotspots.
   Read nearby README or markdown docs when they materially clarify feature scope.
   Do not substitute local filesystem inspection here. GitHub input is only for the explicitly provided repo URL or repo path.

Use `gh api` against repository contents when possible:

Use the shared `github-manager` skill to read GitHub repository content when needed.

Use `references/github-patterns.md` for repo/path extraction and analysis guidance.

7. Read the local codebase path when available.
   Only use a local codebase path when the user explicitly provides one. Treat it as a fourth evidence source for test structure, neighboring suites, helpers, fixtures, and implementation hints.

Use generic Bash file discovery only on the user-provided path. Prefer lightweight inspection such as `find`, `rg --files`, and representative `sed -n` reads over broad scans.

Use `references/local-codebase-patterns.md` for local path analysis guidance.

When both local codebase evidence and richer Confluence/Jira scope are present:
- do not let the local codebase reduce the scenario count by default
- retain separate source-backed scenarios unless they are true duplicates
- if two scenarios are merged, call out what was merged and why
- add a `Local Codebase Mapping` subsection under `Automation Candidates` when the local path materially contributes
- if the local path shows real end-to-end runtime validation patterns such as sender mailbox setup, message send, journal verification, recipient mailbox verification, delivery-status validation, stored-message retrieval, or policy toggles, reuse those patterns to make testcase steps concrete and observable

8. Build a unified feature model.
   Extract:
   - feature intent
   - user roles and personas
   - happy paths
   - failure paths
   - configuration knobs
   - dependencies and integrations
   - environments and data setup
   - automation candidates
   - changed components and regression hotspots from commit artifacts when available
   - feature behavior and dependency clues from GitHub docs or implementation paths when explicitly provided

9. Generate the test plan even if coverage is partial.
   Prefer:
   - exact source-backed scenarios first
   - inferred boundary cases second
   - explicit gaps last

Preserve breadth before optimization:
- keep broad source-backed product/system coverage even when local test code is narrower
- treat local codebase evidence as an automation-enrichment layer, not a replacement lens
- if the user asked for a combined plan in one go, generate the broadest consolidated plan you can from all provided sources in a single pass

Before writing detailed testcases, synthesize an execution model from the evidence:
- what is configured before runtime
- how the message or API request enters the system
- which observable runtime artifacts prove behavior
- what the final user-visible outcome is

If the evidence supports true end-to-end validation, prefer end-to-end scenarios over abstract component-only restatements.
Examples of strong observable evidence include:
- sender mailbox or sender identity
- recipient mailbox or folder outcome
- journal visibility
- delivery-status visibility
- stored-message retrieval or modified-message retrieval
- policy retrieval path
- Enforcer or Filter Engine logs, metrics, or correlation identifiers

10. Generate detailed testcase bodies when requested.
   If the user asks for detailed testcases, expand every materially distinct scenario using the template in `references/testcase-template.md`.
   Do not provide only a sample set or representative subset when the user asked for a full detailed plan.
   Do not use generic placeholders such as `execute the relevant flow`, `validate expected behavior`, or `observe outputs as applicable` when the evidence provides a more concrete runtime path.
   When the sources support it, detailed testcases should explicitly describe:
   - what rule or policy is configured
   - how the message is sent or request is invoked
   - what is validated in journal, mailbox, delivery-status, stored-message, API, or log artifacts
   - what final end-user-visible outcome proves the scenario

11. Generate a flow diagram when the feature involves conditional logic.
   If the feature has multi-step workflows, decision branches, or conditional behavior, generate a Mermaid flow diagram. Use `references/flow-diagram.md` for syntax and Confluence rendering guidance.

12. Convert the generated plan into Confluence-ready structure every time.
   Even when the user did not explicitly ask to upload, format the testcase section using the Confluence test-template structure and produce a final Confluence page body for upload.
   The generated response should therefore include:
   - the analytical plan sections in chat-friendly markdown
   - full testcase bodies in the Confluence test-template structure
   - a flow diagram if applicable (wrapped in a Confluence code macro)
   - a final Confluence storage-format page body that can be uploaded after review

13. Write the output to a local file when requested.
   If the user asked for file output, create a markdown file in the workspace using the structure from `references/output-template.md`. Confirm the path used.

14. Call out missing evidence.
   If a source is absent, say how that affects confidence and what would most improve the plan.

15. Link the test plan to the epic.
   After a successful Confluence upload, add a comment on the Jira epic with the new page URL using the shared `jira-issues` skill. This step is mandatory -- do not skip it.

## Test Plan Update

Update an existing test plan when the epic has changed (new stories, updated acceptance criteria, scope changes).

1. Fetch the epic and linked stories (same as Workflow steps 1-3).
2. Search Confluence for an existing test plan: use the shared `confluence-pages` skill to search for a page matching the epic key in the target space.
3. If found, fetch the existing plan content.
4. Compare the current Jira state against the existing plan:
   - New stories not covered in the plan
   - Updated acceptance criteria
   - Removed or closed stories still listed
   - Missing test cases for new scope
5. Present a summary of proposed changes (added, updated, removed sections).
6. After user confirms, update the Confluence page.

If no existing plan is found, fall back to the full test plan Workflow.

## Test Case Generation (Single Ticket)

Generate concise test cases and add them to a Jira ticket description. This is a lighter workflow for individual tickets that do not need a full test plan.

1. Fetch ticket details via the shared `jira-issues` skill.
2. Check if the description already contains a QA section (`*QA*`, `h2. QA`, or `## QA` from a previous run).
   - If yes, treat as an **update**. Show the existing checks, then show only what changed: added lines prefixed with `+`, removed lines prefixed with `-`. Do NOT regenerate the full section -- show a diff.
   - If no, treat as a **create** -- generate a new `*QA*` section.
3. Enrich context when available:
   - Extract Confluence URLs from description/comments and fetch linked docs.
   - Search for related PRs via the shared `github-manager` skill and review changed files.
4. Generate ONLY a flat concise checklist (5-8 items). Rules:
   - No sub-headers, no categories, no grouping -- just a flat list under the QA heading.
   - No Gherkin, no scenarios.
   - Consolidate repetitive checks (e.g., "Verify feature works in all 11 environments" instead of one item per environment).
   - Each item is one clear, independently verifiable check.
   - Use **Jira wiki markup**, not markdown. Jira does not render `##` or `- [ ]`.
   - Use `*QA*` (bold) as the section label, not a heading.
   ```
   *QA*
   * Verify <check>
   * Verify <check>
   ```
5. Present the proposed `*QA*` section (or diff) for review.
6. After user confirms, update the ticket description using the shared `jira-issues` skill.

## Output Format

Generate these sections in order:

1. `Feature Summary`
2. `Sources Used`
3. `Assumptions and Missing Inputs`
4. `Test Scope`
5. `Out of Scope`
6. `Test Scenarios`
7. `Test Data and Environment Needs`
8. `Automation Candidates`
9. `Risks and Open Questions`

Use a scenario table or flat bullet list with:
- scenario id
- scenario title
- why
- source basis
- priority
- manual or automation

When local codebase evidence is used, `Automation Candidates` should include a `Local Codebase Mapping` subsection with:
- relevant local files or suite areas
- reusable helpers, fixtures, or assertions
- suggested new test file or suite grouping names when useful

When the user asks for detailed testcases, also add:

10. `Detailed Test Cases`

Each detailed testcase should use the exact section structure from `references/testcase-template.md`.
Expand all scenarios when the user asked for a full detailed plan.

Always also add:

11. `Confluence Page Body`

This section should contain the final Confluence storage-format body ready for upload. It must preserve the same scenario coverage as the generated plan and testcase sections.

When the user asks for a local file:

12. `Saved File`

Include the workspace path where the markdown file was written.

## Source Priority

Use sources in this order:

1. Confluence design intent and feature behavior
2. Jira scope, acceptance criteria, and child issues
3. Jira-linked PR and commit artifacts
4. GitHub prior-test patterns and implementation clues
5. Local codebase path, when explicitly provided by the user
6. Explicitly labeled inference when the above are incomplete

## Quality Rules

- Do not wait for perfect inputs.
- Support multiple Confluence pages and multiple Jira items when the user provides them.
- Do not invent acceptance criteria that contradict the sources.
- If Jira and Confluence disagree, call out the conflict.
- If multiple Confluence pages disagree, prefer the most specific feature page and call out the conflict.
- If multiple Jira items disagree, prefer the primary feature Jira or epic acceptance criteria and call out the conflict.
- Use commit artifacts from Jira-linked PRs to identify changed components, integration touchpoints, and regression-sensitive areas, not as the sole source of product behavior.
- If GitHub examples reflect legacy behavior, use them as implementation hints, not product truth.
- If GitHub input points to implementation code or README files, use that evidence to improve scope, API understanding, dependencies, and regression coverage.
- Use GitHub implementation evidence to enrich the plan, but do not let it override explicit Confluence or Jira intent.
- Use a local codebase path only when the user explicitly provides it.
- Preserve Confluence/Jira source-backed coverage when GitHub or local codebase evidence is also provided.
- Use GitHub and local codebase evidence to enrich automation mapping, fixture reuse, and regression hotspots, not to shrink product/system scenario coverage.
- Do not drop a source-backed scenario solely because a matching test does not exist in the local codebase.
- If scenarios are merged, explain the merge explicitly in `Assumptions and Missing Inputs` or near `Test Scenarios`.
- Keep generic Bash usage scoped to the user-provided path and the output file path.
- Do not silently fill unknown values. If something is not known from sources, write `Unknown` or add an explicit open question.
- Prefer test scenarios that map to user-visible outcomes.
- Separate feature behavior tests from resilience, permissions, migration, telemetry, and regression coverage.
- Prefer execution-ready testcases over abstract paraphrases of the source.
- When runtime evidence exists, write testcase steps around actual observability points such as sender action, recipient mailbox state, PRODUCT journal state, delivery status, stored-message content, policy retrieval, API response, and logs or metrics.
- If local or GitHub test evidence shows concrete end-to-end validation patterns, reuse that structure in the generated testcase steps and expected behavior.
- For mail-processing features, include mailbox-visible end-to-end scenarios whenever the evidence supports them. A good testcase should make it clear what mail is sent, how it is processed, and what is verified in the final recipient-visible outcome.
- Distinguish between API/component coverage and end-to-end system coverage. Do not let API-level scenarios crowd out mailbox-visible or policy-visible system tests when those are materially supported by the sources.
- Use common preconditions and teardown patterns from the evidence when they exist rather than inventing generic boilerplate.
- If the available evidence supports grouped coverage such as policy lifecycle, request/response contract, rule coverage, action coverage, persistence/metadata, end-to-end mailbox validation, resilience, and observability, preserve that grouping in the generated plan.
- If file output is requested, write markdown to the workspace and preserve the same section structure as the chat response.
- When the user asks for a full detailed plan, expand all materially distinct scenarios into testcase bodies.
- Use the Confluence test-template testcase structure every time detailed testcases are produced:
  - `Title`
  - `Pre-condition`
  - `Test Case Steps`
  - `Expected Behaviour`
  - `Pass/Fail Criterion`
  - `Teardown`
- Always produce a final Confluence storage-format page body for upload, even if the user has not yet asked to publish it.

## Additional Resources

- `references/commands/README.md` - capability overview, setup notes, and copy-paste examples
- `references/commands/config.md` - configure and verify Confluence, Jira, and GitHub prerequisites
- `references/input-strategy.md` - how to proceed when one or more inputs are missing
- `references/jira-patterns.md` - Jira epic and child-issue lookup patterns
- `references/commit-artifacts.md` - how to extract and use PR/commit artifacts from Jira items
- `references/github-patterns.md` - GitHub path parsing and prior-test analysis
- `references/local-codebase-patterns.md` - guidance for analyzing an explicitly provided local codebase path
- `references/output-template.md` - recommended structure for the generated plan
- `references/testcase-template.md` - template for fully written testcase bodies
- `references/file-output.md` - rules for naming and saving the generated plan
- `references/flow-diagram.md` - Mermaid flow diagram generation and Confluence rendering
- `references/risk-analysis.md` - structured risk assessment template
- `references/epic-analysis.md` - epic scope analysis and planning template

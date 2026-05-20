# Input Strategy

This skill works with four optional-but-preferred source types:
- one or more Confluence design or feature-canvas pages
- one or more Jira items such as an epic, issue tree, or related issue list
- Jira-linked PR and commit artifacts
- GitHub evidence such as similar automated tests, implementation code, README files, or adjacent docs
- Optional local codebase path with similar tests or implementation context

## If Confluence, Jira, And GitHub Are Present

Use them together:
- Confluence for product behavior and design intent
- Jira for implementation scope and acceptance criteria
- Jira-linked PR and commit artifacts for changed-component and regression evidence
- GitHub for test structure, implementation clues, README context, dependency hints, and regression hotspots

If a local codebase path is also present:
- use it for neighboring suites, fixtures, helpers, and grouping patterns
- keep it separate from GitHub evidence in the plan narrative
- if it contains real end-to-end runtime validations, use those patterns to sharpen testcase steps, expected behavior, and pass criteria

If multiple Confluence pages or Jira items are present:
- merge overlapping requirements before generating scenarios
- keep all materially used inputs listed in `Sources Used`
- prefer the most specific design or acceptance source when conflicts exist
- call out unresolved conflicts explicitly

If Jira-linked commit artifacts are present:
- use them to refine regression scope and changed-component coverage
- do not let them override product behavior described by Confluence

## If Confluence Is Missing

Generate the plan from Jira plus GitHub:
- use Jira for scope and expected outcomes
- use GitHub to infer implementation behavior, configuration, dependencies, and automation style
- label product-behavior assumptions clearly

## If Jira Is Missing

Generate the plan from Confluence plus GitHub:
- use Confluence for behavior and scenarios
- use GitHub for existing suite structure, implementation clues, and docs-backed setup details
- identify missing traceability to issue scope

## If GitHub Is Missing

Generate the plan from Confluence plus Jira:
- focus on scenario quality and coverage
- include a separate `Automation Candidates` section
- note that framework-specific implementation examples and README/code-based context were unavailable

If a local codebase path is present:
- use it as an additional implementation-pattern source
- call out that the local path was user-provided and separate from GitHub
- do not just mention the local path in `Automation Candidates`; use it to improve concrete runtime validation detail when the evidence supports that

## If Local Codebase Path Is Missing

Continue normally from Confluence, Jira, and GitHub.
- do not inspect local repositories by implication
- do not treat GitHub input as permission to read local filesystem paths

## If Only One Source Is Present

Still generate:
- a feature summary
- core happy-path and negative scenarios
- data/setup needs
- open questions

Mark the result as a draft and list the most valuable missing source.

## If No Sources Are Present

Ask for Confluence page list, Jira list, GitHub, and the optional local codebase path in one prompt, then recover Jira-linked commit artifacts when possible and offer a scaffolded draft only if the user wants a generic template.

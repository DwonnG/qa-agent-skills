# Local Codebase Patterns

Use this guidance only when the user explicitly provides a local codebase path.

## Purpose

A local codebase path can improve test-plan quality by exposing:
- neighboring automated suites
- helper libraries and fixtures
- naming conventions
- scenario grouping patterns
- implementation details that suggest regression hotspots

Treat the local codebase as implementation evidence, not product truth.

## Input Examples

- `/path/to/repo/tests`
- `/path/to/repo/tests/inline_mode`
- `/path/to/service/src`

## What To Read

- suite directories near the provided path
- representative test files
- shared resources and fixtures
- helpers, utilities, or setup files

Prefer lightweight inspection first:
- file listing
- filenames
- representative samples from 1 to 3 files

## What To Extract

- testcase naming style
- grouping style by capability or risk area
- setup and teardown patterns
- reusable fixtures
- common assertions
- existing negative-test coverage
- real runtime validation flow, such as:
  - how mail is sent
  - how message ids are recovered
  - how journal state is validated
  - how recipient mailbox state is validated
  - how delivery status is validated
  - how stored-message content is validated
  - how policy is toggled or reset

## Guardrails

- Do not inspect arbitrary local repos unless the user supplied the path.
- Do not let local implementation details override Confluence product intent.
- If local tests contradict Confluence or Jira, call out the conflict explicitly.
- Use local automation evidence to make testcase steps and expected behavior more concrete and execution-ready when it exposes real end-to-end validation patterns.

# Epic Test Plan Lookup

When generating E2E tests, check whether the ticket's parent epic has a test plan. If it does, use the relevant scenarios as primary input for test generation.

## Step 1: Find the Parent Epic

From the ticket view output, extract the `Epic Link` field:

```
jira-issues: view <TICKET-KEY>
```

Look for the epic key in the response (e.g., `PROJ-50974`). If the ticket has no epic link, skip this lookup and proceed with diff-only test generation.

## Step 2: Read the Epic and Find the Test Plan Link

View the epic to find a Confluence test plan URL in its description or comments:

```
jira-issues: view <EPIC-KEY> --full
```

Look for Confluence URLs in the description or comments. Common patterns:
- `https://your-org.atlassian.net/wiki/spaces/ENG/pages/<ID>/...`
- Links with "Test Plan", "System Test", or "QA" in the title

If no Confluence link is found in the epic, try a fallback search:

```
confluence-pages: search-cql "space = ENG and type = page and text ~ '<EPIC-KEY>'" --limit 5
```

## Step 3: Extract Relevant Scenarios

If a test plan page is found, read it:

```
confluence-pages: view <PAGE-ID> --markdown
```

Extract the test scenarios section. Look for:
- Scenario tables (ID, title, priority)
- Test case lists with preconditions and expected results
- Acceptance criteria mapped to test cases

## Step 4: Filter to Ticket Scope

Not all scenarios from the epic test plan apply to the current ticket. Filter by:

1. **Ticket summary and description** -- match scenarios that cover the same feature area
2. **PR diff** -- match scenarios that test the code paths touched by the change
3. **Acceptance criteria** -- match scenarios that validate the ticket's specific criteria

Keep only scenarios that are relevant to the current ticket. Discard scenarios for other stories under the same epic.

## Step 5: Pass to Phase 5

Store the filtered scenarios as `test_plan_scenarios`. In Phase 5, these become the primary source for test generation:

- **Test plan scenarios** take priority -- generate tests for these first
- **Diff-based recommendations** fill gaps -- if the diff reveals testable behavior not covered by the plan, add additional tests

## When No Test Plan Exists

If no Confluence test plan is found for the epic:
- Note it in the Phase 6 summary: `Epic Test Plan: Not found`
- Proceed with diff-only test generation (current behavior)
- Do NOT block or fail the gate

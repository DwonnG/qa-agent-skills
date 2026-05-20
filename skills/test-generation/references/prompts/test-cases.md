# Test Case Generation

Cover these categories:

1. **Happy Path** -- main user flows and expected behavior.
2. **Edge Cases** -- boundaries, empty/invalid inputs, unusual conditions.
3. **Error Handling** -- invalid actions, system errors, fallback behavior.
4. **Integration / E2E** -- cross-system workflows and complete user journeys.

## Single Ticket Format (Jira wiki markup)

For individual tickets, generate a short checklist to append to the ticket description. Use **Jira wiki markup** (not markdown -- Jira does not render `##` or `- [ ]`). Use bold text for the label, not a heading:

```
*QA*
* Verify <happy path scenario>
* Verify <edge case>
* Verify <error handling scenario>
* Verify <integration scenario>
```

Keep it to 5-8 items. Each item should be one clear, verifiable check.

## Test Plan Format (Confluence storage)

For full test plans uploaded to Confluence, each test case group is a numbered heading, and each scenario is wrapped in a Confluence expand macro. The body must be valid Confluence storage format (XHTML).

### Structure per functional area

```html
<h3>1. API Validation (N scenarios)</h3>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Scenario: Enable feature on valid domain</ac:parameter>
  <ac:rich-text-body>
    <table>
      <tbody>
        <tr><th>Given</th><td>A valid domain with all prerequisites met</td></tr>
        <tr><th>When</th><td>PATCH /domains with featureEnabled=true</td></tr>
        <tr><th>Then</th><td>API returns 200, GET confirms featureEnabled=true</td></tr>
        <tr><th>Priority</th><td>High</td></tr>
      </tbody>
    </table>
  </ac:rich-text-body>
</ac:structured-macro>

<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Scenario: Reject feature when prerequisite missing</ac:parameter>
  <ac:rich-text-body>
    <table>
      <tbody>
        <tr><th>Given</th><td>A domain without the required prerequisite</td></tr>
        <tr><th>When</th><td>PATCH /domains with featureEnabled=true</td></tr>
        <tr><th>Then</th><td>API returns 400 with descriptive error</td></tr>
        <tr><th>Priority</th><td>High</td></tr>
      </tbody>
    </table>
  </ac:rich-text-body>
</ac:structured-macro>
```

Rules:
- Every scenario gets its own expand macro with the scenario title in the `title` parameter.
- Inside the expand, use a 2-column table: `<th>` for Given/When/Then/Priority, `<td>` for the value.
- Group scenarios under an `<h3>` heading per functional area with the count.
- Generate 8-12 scenarios per functional area.

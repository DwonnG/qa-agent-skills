# Test Plan Workflow

End-to-end workflow for generating a test plan from a Jira epic and uploading it to Confluence.

## 1. Context Gathering

For an epic:
```
jira-cli --format json search --jql '"Epic Link" = <EPIC-KEY>'
```

For a single issue:
```
jira-cli --format json view <ISSUE-KEY>
```

Extract Confluence URLs from ticket descriptions and comments. These are typically Feature Canvas or design docs.

## 2. Confluence Document Ingestion

Fetch each linked Confluence page:
```
confluence-cli --format json view <PAGE-ID>
```

Summarize each document focusing on:
- Functional requirements
- Technical constraints
- User workflows
- Acceptance criteria

## 3. Fetch Test Plan Template

Retrieve the live team template from Confluence:
```
confluence-cli --format json view --space ENG --title "Test Plan Template"
```

Use the fetched template structure as the output format. Do NOT use the local `assets/test-plan-template.md` -- the Confluence version is the source of truth and may have been updated by the team.

## 4. Requirements Analysis

Extract from the gathered context:
- Acceptance criteria from each story
- Functional areas and coverage gaps
- Technical constraints and dependencies

## 5. Test Plan Body

Generate the plan body following the template structure. The entire body must be valid **Confluence storage format** (XHTML with Confluence macros). Use these elements:

- `<h2>` for major sections (Introduction, Scope, Test Strategy, etc.)
- `<h3>` for subsections (In Scope, Out of Scope, test case groups)
- `<table>` with `<th>` and `<td>` for structured data (environments, resources, risks, schedule)
- `<ul>` / `<li>` for lists
- `<ac:structured-macro ac:name="expand">` for collapsible test case scenarios (see `references/prompts/test-cases.md`)
- `<ac:structured-macro ac:name="code">` for code blocks and diagrams (see step 7)
- `<ac:structured-macro ac:name="status">` for status labels (Completed, In Progress, Pending)

Do NOT use markdown syntax in the body. Do NOT use bare text paragraphs with bold labels.

Sections:
- Test Plan Metadata (table: creator, feature, epic, team, version)
- Introduction
- Scope (in-scope and out-of-scope as bulleted lists)
- Testing Strategy (entry/exit criteria)
- Automated Test Overview (table per test type: unit, integration, E2E, regression)
- Test Resources (environments table with columns: Environment, URL, Type, Status)
- Test Cases (expand macros per scenario, grouped by functional area -- see step 6)
- Resources & Responsibilities (table: role, name)
- Schedule (table: milestone, status, notes)
- Dependencies (bulleted list)
- Risks & Assumptions (tables split by Technical, Project, Quality with columns: Risk, Severity, Mitigation)
- Glossary (table: term, definition)

## 6. Test Case Generation

Generate test cases per `references/prompts/test-cases.md`. Each scenario must be wrapped in a Confluence expand macro with a Given/When/Then table inside. Group scenarios under `<h3>` headings by functional area with the count.

## 7. Flow Diagram

If the feature involves conditional logic or multi-step workflows, generate a Mermaid diagram per `references/prompts/flow-diagram.md`. Wrap it in a Confluence code macro so it renders as a code block:

```html
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">mermaid</ac:parameter>
  <ac:plain-text-body><![CDATA[flowchart TD
    A --> B
    B -->|Yes| C
    B -->|No| D
]]></ac:plain-text-body>
</ac:structured-macro>
```

Do NOT insert raw Mermaid text outside a code macro.

## 8. Upload to Confluence

Present the completed plan summary for user review. Only upload after explicit confirmation.

Default: upload to space `ENG` (same location as the template). If the user specifies a different space or parent page, use that instead.

**Important**: Test plan bodies are large. Do NOT pass the HTML directly as a `--body` shell argument -- it will exceed argument length limits and cause the command to abort. Instead, write the HTML to a temp file first:

```bash
# 1. Write the body to a temp file (use Write tool or cat heredoc)
cat > /tmp/testplan-body.html <<'EOFHTML'
<h2>Test Plan Metadata</h2>
...full HTML here...
EOFHTML

# 2. Upload using command substitution to read the file
confluence-cli pages create --space ENG --title "<TITLE>" --body "$(cat /tmp/testplan-body.html)"

# 3. Clean up
rm -f /tmp/testplan-body.html
```

Do not include a "Generated with" footer in the body.

After upload, inform the user they can move the page to a different location in Confluence if needed.

## 9. Link Test Plan to Epic (Required)

After a successful upload, add a comment to the Jira epic with the Confluence page URL:
```
jira-cli comment <EPIC-KEY> "Test Plan: <CONFLUENCE-URL>"
```

This step is mandatory. Do not skip it.

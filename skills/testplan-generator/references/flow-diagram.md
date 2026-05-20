# Flow Diagram Generation

Generate a high-level flow diagram for the system behavior or user interaction described in the ticket.

Focus on:
- Key steps, decisions, and outcomes
- System and user roles
- Error handling or conditional branches
- Logical flow from start to finish

## Output Format

Use Mermaid syntax for the diagram logic:

```
flowchart TD
    Step1 --> Step2
    Step2 -->|Condition A| Step3
    Step2 -->|Condition B| Step4
```

## Confluence Rendering

When embedding in a Confluence test plan, wrap the Mermaid syntax in a code macro:

```html
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">mermaid</ac:parameter>
  <ac:plain-text-body><![CDATA[flowchart TD
    Step1 --> Step2
    Step2 -->|Condition A| Step3
    Step2 -->|Condition B| Step4
]]></ac:plain-text-body>
</ac:structured-macro>
```

Do NOT insert raw Mermaid text directly into the page body.

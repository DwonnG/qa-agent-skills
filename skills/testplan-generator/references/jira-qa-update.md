# Jira QA Update

Use this guidance only when the user explicitly asks for a Jira QA section on a specific ticket.

## Goal

Generate or update a concise ticket-level QA section derived from the larger plan without pasting the full plan into Jira.

## Create Workflow

1. Read the ticket.
2. Generate a short QA checklist from the relevant scenarios.
3. Use Jira wiki markup.
4. Show the proposed QA section before any write.
5. Only after explicit user confirmation, update the ticket.

## Update Workflow

1. Detect whether a QA section already exists.
2. Compare the new proposed checklist against the existing checklist.
3. Show only the meaningful delta before any write:
   - added checks
   - removed checks
   - updated checks
4. Only after explicit user confirmation, update the ticket.

## Format Rules

Use a short flat checklist:

```text
*QA*
* Verify <check>
* Verify <check>
```

- Use Jira wiki markup, not markdown.
- Keep it concise and ticket-focused.
- Prefer 5-8 independently verifiable items.
- Consolidate repetitive checks when appropriate.

## Guardrails

- Do not paste the full test plan into the Jira description.
- Do not regenerate a full QA section blindly when a focused update is sufficient.
- Keep the ticket QA section narrower than the system-level test plan.

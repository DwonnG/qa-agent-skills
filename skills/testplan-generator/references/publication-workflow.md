# Publication Workflow

Use this guidance only when the user explicitly asks to publish or update artifacts after plan generation.

## Goal

Keep the planning flow unchanged, then convert the already-generated plan into the destination format.

- Planning comes first.
- Publication is a final optional phase.
- Do not let Confluence or Jira formatting constraints reduce scenario coverage that was already derived from the evidence.

## Confluence Create

1. Fetch the live test plan template from Confluence when the team uses one.
2. Convert the generated plan into Confluence storage format.
3. Present a short review summary before any write:
   - title
   - target space or parent
   - scope summary
   - approximate scenario count
4. Only after explicit user confirmation, create the page.
5. If a primary Jira item or epic was part of the input, add a Jira comment linking the Confluence page.

## Confluence Update

1. Search for the existing page first.
2. Fetch the current published content.
3. Compare the current plan draft against the published artifact.
4. Present a change summary before any write:
   - added sections or scenarios
   - updated sections or scenarios
   - removed sections or scenarios
5. Only after explicit user confirmation, update the page.

## Formatting Rules

- Use Confluence storage format for page bodies.
- Prefer the live team template over any static local template.
- Preserve existing team-specific structure when it does not conflict with correctness.
- Avoid truncating the plan just to fit an old page structure.

## Jira Backlink

After a successful Confluence create, add a Jira comment on the primary Jira item or epic with the published page URL when that linkage was part of the requested workflow.

## Guardrails

- Do not publish by default.
- Do not update an existing page without showing the delta first.
- Do not let write workflow details override the source-backed plan.

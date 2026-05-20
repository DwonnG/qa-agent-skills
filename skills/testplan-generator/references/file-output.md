# File Output

Use this guidance when the user wants the generated plan written to a local file.

## Ask First

Before writing a file, confirm:
- whether the user wants file output at all
- whether they want scenario-level only or a full detailed end-to-end plan
- the target file path, if they care about the location or filename

## Default Filename

If the user wants a file but does not specify a path, use a reasonable markdown filename in the workspace:

```text
testplan-<feature-slug>.md
```

If the feature slug is not obvious, use:

```text
generated-testplan.md
```

## File Content Rules

- Write markdown.
- Preserve the same section order as the chat response.
- If the user requested detailed testcases, include the `Detailed Test Cases` section.
- If something is unknown, write `Unknown` rather than inventing data.
- Include source URLs in the `Sources Used` section when available.

## Completion

After writing the file:
- report the final workspace path
- state whether the saved file is scenario-level only or fully detailed

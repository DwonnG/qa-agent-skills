# Keyword Extraction

Extract search terms from a bug report in three categories. Return structured output with:

**exact_identifiers** (up to 5): Precise, short technical names (1-3 words) that would appear in related issue summaries. Examples: service names, module names, error codes, API names, config keys.

**keywords** (up to 5): Broader technical terms for full-text search. Use only terms likely to appear in issue summaries.

**concepts** (1-2): Functional area phrases describing what the bug is about. Used for relevance ranking, not JQL search.

## Input

- Bug Title
- Bug Description

## Example Output

```
exact_identifiers: ["PolicyEngine", "SMTP-421", "relay_config"]
keywords: ["message processing", "delivery failure", "queue timeout"]
concepts: ["email relay configuration affecting outbound delivery"]
```

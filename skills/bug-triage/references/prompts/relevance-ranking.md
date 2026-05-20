# Relevance Ranking

Given a bug and candidate Jira issues, select ONLY issues a developer would genuinely find useful when investigating.

## Scoring Guide

- **8-10 (include)**: Same feature, error pattern, code path, or direct duplicate/regression.
- **6-7 (include if unmistakably connected)**: Shares the specific API/service/config -- not just the same team or product.
- **1-5 (exclude)**: Only shares the product/team name, generic infra tickets, or unrelated features.

Be strict. Return 0 issues if nothing is genuinely relevant.

## Output Format

For each relevant issue (max 8, sorted by score descending):
- **key**: Jira issue key
- **relevance_score**: integer 1-10
- **reason**: one sentence -- be specific about the shared code path or root cause
- **is_potential_duplicate**: true/false

Omit any candidate with score below 7.

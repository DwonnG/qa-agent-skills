---
name: qa-merge-guardrails
description: Guide agents through merge-readiness checks for QA and test automation PRs—coverage, regression, standards review, and safe self-healing—without bypassing human judgment.
allowed-tools: Read, Bash(git:*), Bash(gh:*)
---

# QA Merge Guardrails

Use when a PR is ready for review or merge and you need **structured quality gates**, not blind automation.

## Principles

- **Dry run first** — summarize findings before writing comments or changing CI config.
- **Never auto-merge** on agent output alone.
- **Prefer fixing root causes** (selectors, timing, test design) over reruns or sleeps.

## Checklist

1. **Scope** — Read the PR diff and linked ticket; list affected areas (UI, API, infra).
2. **Standards** — Compare against team conventions (naming, markers, fixture usage, no hardcoded secrets).
3. **Unit / integration** — Confirm new logic has fast tests where the repo supports them.
4. **E2E regression** — Identify which existing suites must run; note `xdist_group` or env requirements.
5. **Flakiness** — If failures look intermittent, classify: environment, data, selector drift, or product bug. Do not dismiss without evidence.
6. **Self-healing** — Selector/API drift fixes are allowed only when:
   - The product change is intentional and verified.
   - The updated locator is more resilient (`get_by_test_id`, `get_by_role`).
   - A human approves the commit message explaining the drift fix.
7. **Publish** — Post a short summary: pass/fail per gate, blockers, and suggested next steps.

## When not to use agents

- Security-sensitive changes (auth, crypto, PII handling).
- One-off production hotfixes without reproduction steps.
- Large refactors where the model lacks full repo context—pair with a human reviewer.

## Output format

```markdown
## Merge readiness

| Gate | Status | Notes |
|------|--------|-------|
| Standards | pass/fail | … |
| Unit/integration | pass/fail/skip | … |
| E2E regression | pass/fail | suites run |
| Flakiness review | pass/fail | … |

**Recommendation:** merge / hold / needs human
```

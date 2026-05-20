# qa-agent-skills

Public [Agent Skills](https://agentskills.io) for **platform QA**, **test automation**, and **agentic quality engineering**.

Skills in this repo are derived from work in internal agent-skills and QA agent monorepos, then **sanitized** (no employer service names, credentials, Jenkins job paths, or embedded repo checkouts).

## Skills

| Skill | Description |
|-------|-------------|
| [selenium-to-playwright](skills/selenium-to-playwright/) | Migrate Selenium 3 page objects/tests to pytest-playwright; segment bulky tests |
| [cloudwatch-metric-comparison](skills/cloudwatch-metric-comparison/) | Post-deploy CloudWatch drift checks for Lambda and API Gateway |
| [qa-merge-guardrails](skills/qa-merge-guardrails/) | Merge-readiness checklist for QA/test PRs |
| [testplan-generator](skills/testplan-generator/) | Test plans from Confluence + Jira + GitHub evidence |
| [test-generation](skills/test-generation/) | Test plans and cases from epics/stories and feature docs |
| [bug-triage](skills/bug-triage/) | Structured Jira bug triage with related-issue search |
| [qa-workflow](skills/qa-workflow/) | QA ticket lifecycle: claim, pass/fail, release testing, queue |
| [test-build-insight](skills/test-build-insight/) | Pipeline status, E2E results, deployments, Dependabot |
| [feature-test-generator](skills/feature-test-generator/) | Scaffold tests from PR diffs and repo conventions |
| [qa-release-gate](skills/qa-release-gate/) | PR/release QA gate: routing, standards, deployment verification |
| [qa-pr-codereview](skills/qa-pr-codereview/) | QA-focused PR code review agent patterns |

## Install

```bash
git clone https://github.com/DwonnG/qa-agent-skills.git
cp -r qa-agent-skills/skills/<skill-name> ~/.cursor/skills/
# or ~/.claude/skills/
```

Composable skills (`testplan-generator`, `bug-triage`, etc.) expect companion skills such as `jira-issues`, `github-manager`, and `confluence-pages` in your local skills path.

## Related

- [qa-mcp-server](https://github.com/DwonnG/qa-mcp-server) — MCP server for Jira, GitHub, Jenkins, AWS
- [Portfolio](https://dwonng.github.io/)

## Author

**Dwonn Goodwin** — [LinkedIn](https://www.linkedin.com/in/dwonngoodwin/) · [GitHub](https://github.com/DwonnG)

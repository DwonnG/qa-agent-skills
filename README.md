# qa-agent-skills

Public [Agent Skills](https://agentskills.io) for **platform QA**, **test automation**, and **agentic quality engineering**.

Sanitized for open source: no employer service names, credentials, or internal architecture details.

## Skills

| Skill | Description |
|-------|-------------|
| [selenium-to-playwright](skills/selenium-to-playwright/) | Migrate Selenium 3 page objects/tests to pytest-playwright; segment bulky tests for parallel runs |
| [cloudwatch-metric-comparison](skills/cloudwatch-metric-comparison/) | Post-deploy CloudWatch drift checks for Lambda and API Gateway |
| [qa-merge-guardrails](skills/qa-merge-guardrails/) | Merge-readiness checklist for QA/test PRs with human-in-the-loop gates |

## Install (Cursor / Claude Code)

Copy a skill folder into your agent skills path, for example:

```bash
git clone https://github.com/DwonnG/qa-agent-skills.git
cp -r qa-agent-skills/skills/selenium-to-playwright ~/.cursor/skills/
# or ~/.claude/skills/
```

For **cloudwatch-metric-comparison**, run commands from inside the skill directory so `scripts/` paths resolve. Requires `nix`, AWS CLI, and a read-only AWS profile.

## Related projects

- [qa-mcp-server](https://github.com/DwonnG/qa-mcp-server) — MCP integrations for Jira, GitHub, Jenkins, and AWS
- [Portfolio](https://dwonng.github.io/)

## Author

**Dwonn Goodwin** — [LinkedIn](https://www.linkedin.com/in/dwonngoodwin/) · [GitHub](https://github.com/DwonnG)

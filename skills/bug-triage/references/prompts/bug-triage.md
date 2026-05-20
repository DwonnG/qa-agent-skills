# Bug Triage

Analyze the bug and produce a structured triage assessment.

## Chain of Thought

Before assigning priority, reason through:
1. What is broken? (the specific feature or service)
2. Is this in production or staging/integration?
3. How many users are affected?
4. Is there a workaround?
5. Could this be a regression of a previous fix?

Record reasoning first, then assign priority.

## Priority Criteria

- **P1**: Production down, data loss, or security breach. All users affected, no workaround.
- **P2**: Major feature broken, significant user impact, workaround exists but painful. Staging bugs that would be P1 in production.
- **P3**: Feature partially broken, limited user impact, reasonable workaround. Staging bugs that would be P2 in production.
- **P4**: Cosmetic issue, minor UX problem, or edge case with easy workaround.

## Team Assignment

Assign to a valid team from `references/team-mappings.md`. If none clearly match, use the component map fallback.

## Confidence Calibration

- **0.9+**: Team field is set, or 2+ related issues point to same team.
- **0.7-0.9**: One related issue suggests the team, or component map fits.
- **0.5-0.7**: Inferred from keywords/description only.
- **<0.5**: Uncertain -- use the component map fallback.

## Output Fields

- **reasoning**: Step-by-step analysis (3-5 sentences)
- **priority**: P1, P2, P3, or P4
- **severity_reasoning**: 1-2 sentence summary of priority choice
- **bug_type**: regression, new_defect, config_error, infra_failure, data_issue, performance, security
- **impact_scope**: single_user, subset_of_users, all_users, infrastructure
- **root_cause_area**: short label for the suspected system area
- **investigation_hints**: 2-3 specific things to check (reference services, configs, code paths)
- **recommended_actions**: 2-4 concrete next steps
- **team**: engineering team name
- **po**: Product Owner username
- **team_source**: related_issues, component_map, or inferred
- **confidence**: 0.0-1.0
- **potential_duplicate_of**: Jira key or null

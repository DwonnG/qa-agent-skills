# Jira Patterns

Use Jira to recover epic scope, child stories/tasks, and acceptance criteria.

## Read The Main Issue

Use the shared `jira-issues` skill to view the starting Jira issue.

Start with:
- summary
- description
- acceptance criteria
- linked issues
- issue type

## Find Child Scope

Try the simplest supported query first. Depending on Jira configuration, one of these may be correct:

Use the shared `jira-issues` skill with these JQL patterns:

- `parentEpic = PROJ-50974 ORDER BY Rank ASC`
- `"Epic Link" = PROJ-50974 ORDER BY Rank ASC`
- `parent = PROJ-50974 ORDER BY Rank ASC`

Use whichever returns the actual scoped children on the instance.

## What To Extract

- end-user problem
- acceptance criteria
- dependencies
- config changes
- rollout constraints
- linked bugs or subtasks that imply edge cases

## How To Use Jira In The Plan

- map test scenarios to explicit acceptance criteria when available
- use child issues to break down scenario families
- use linked bugs to add regression cases

If Jira is sparse, do not inflate precision. Fall back to Confluence and label the gap.

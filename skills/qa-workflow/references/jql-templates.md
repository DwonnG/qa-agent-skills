# JQL Templates

Pre-built JQL queries for common QA operations. Default project: **PROJ**.

## Ready for QA

Tickets in QA or Beta QA status with no validator assigned, in the current sprint:
```
project = {project} AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in (QA, "Beta QA") AND Sprint in openSprints() AND Validator is EMPTY ORDER BY fixVersion ASC
```

## In Progress (Dev)

Tickets actively being worked on by development:
```
project = {project} AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in ("In Progress", "PR Pending Review") AND Sprint in openSprints() ORDER BY fixVersion ASC
```

## My Validations

Tickets assigned to a specific validator:
```
project = {project} AND Validator = {username} AND status in (QA, "Beta QA") ORDER BY updated DESC
```

## Release Testing Progress

All issues linked to a release epic, with test result status:
```
"Epic Link" = {epic_key} ORDER BY status ASC, key ASC
```

## Unresolved in Fix Version

All open issues targeting a specific fix version:
```
project = {project} AND fixVersion = "{version}" AND status not in (Resolved, Closed) ORDER BY priority DESC, key ASC
```

## Recently Failed QA

Tickets that were reopened (failed QA) in the last 7 days:
```
project = {project} AND status = Reopened AND updated >= -7d ORDER BY updated DESC
```

## Usage with jira-cli

```
jira-cli search --jql '<JQL>' --format json
```

Replace `{project}` with `PROJ`, `{username}` with the Jira username, `{epic_key}` with the epic issue key, and `{version}` with the fix version string.

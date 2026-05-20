# QA Queue Overview

View the current QA queue: tickets ready for validation, in-progress validations, and recently failed tickets.

## Steps

Run these four queries to build the full queue view. Present results in the report format below.

### 1. Ready for QA (Unclaimed)
Tickets in QA/Beta QA with no validator, current sprint:
```
jira-cli search --jql 'project = PROJ AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in (QA, "Beta QA") AND Sprint in openSprints() AND Validator is EMPTY ORDER BY fixVersion ASC' --format json
```

### 2. My Active Validations
Tickets assigned to the current user for QA:
```
jira-cli search --jql 'project = PROJ AND Validator = <USERNAME> AND status in (QA, "Beta QA") ORDER BY updated DESC' --format json
```

### 3. Recently Failed
Tickets that were reopened in the last 7 days:
```
jira-cli search --jql 'project = PROJ AND status = Reopened AND updated >= -7d ORDER BY updated DESC' --format json
```

### 4. In Dev Pipeline
Tickets being developed that will come to QA soon:
```
jira-cli search --jql 'project = PROJ AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in ("In Progress", "PR Pending Review") AND Sprint in openSprints() ORDER BY fixVersion ASC' --format json
```

## Report Format

Present results in this structured format:

```
QA Queue Overview
=================

Ready for QA (unclaimed): <N>
  <KEY> | <SUMMARY> | <PRIORITY> | <FIX_VERSION>
  ...

My Validations: <N>
  <KEY> | <SUMMARY> | <STATUS> | <TEST_RESULT>
  ...

Recently Failed: <N>
  <KEY> | <SUMMARY> | <REOPENED_DATE>
  ...

Coming Soon (In Dev): <N>
```

## Notes

- Replace `<USERNAME>` with the user's Jira username (`dwgoodwi`). Ask if not known.
- To filter by sub-team, add a sprint name filter: `AND Sprint = "TeamA - 26.8"`.
- See `references/jql-templates.md` for the full set of reusable JQL queries.

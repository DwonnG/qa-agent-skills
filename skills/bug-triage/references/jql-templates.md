# JQL Templates

## Untriaged Bugs (Daily Scan)

```
project = {project} AND issuetype = Bug AND created >= "-{days}d" AND (labels NOT IN ("ai-triaged-bug") OR labels is EMPTY) ORDER BY created DESC
```

## QA Queue (Ready for Testing)

```
project = {project} AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in (QA, "Beta QA") AND "Team(s)" in ({team}) AND Sprint in openSprints() AND Validator is EMPTY ORDER BY fixVersion ASC
```

## In Progress

```
project = {project} AND type in (Story, Bug, Improvement, Task, Vulnerability) AND status in ("In Progress", "PR Pending Review") ORDER BY updated DESC
```

## Related Issues: Summary AND (Stories/Tasks/Epics)

```
project = {project} AND issuetype in ({issue_types}) AND ({summary_clauses}) AND updated >= "-{max_age_days}d" ORDER BY updated DESC
```

## Related Issues: Full Text

```
project = {project} AND issuetype in ({issue_types}) AND ({text_clauses}) AND updated >= "-{max_age_days}d" ORDER BY updated DESC
```

## Related Issues: Same Component

```
project = {project} AND issuetype in ({issue_types}) AND component = "{component}" AND updated >= "-{max_age_days}d" ORDER BY updated DESC
```

## Related Issues: Resolved Bugs

```
project = {project} AND issuetype = Bug AND key != {exclude_key} AND status in (Resolved, Done, Closed) AND ({summary_clauses}) AND updated >= "-{max_age_days}d" ORDER BY updated DESC
```

## Related Issues: Open Bugs

```
project = {project} AND issuetype = Bug AND key != {exclude_key} AND status not in (Resolved, Done, Closed) AND ({summary_clauses}) AND updated >= "-{max_age_days}d" ORDER BY created DESC
```

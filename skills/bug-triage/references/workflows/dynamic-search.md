# Dynamic Search Strategy

Find related Jira issues using up to 5 JQL search strategies. Run each in order, deduplicate results, and cap the candidate pool at 25 issues.

## Strategy 1: Summary Terms AND (Stories/Tasks/Epics)

Search for extracted keywords AND-ed in the summary field across non-bug issue types:
```
project = <PROJECT> AND issuetype in (Story, Task, Epic) AND (<summary clauses>) AND updated >= "-365d" ORDER BY updated DESC
```

Build `<summary clauses>` by AND-ing exact identifiers:
```
summary ~ "ServiceName" AND summary ~ "ConfigKey"
```

Limit: 5 results.

## Strategy 2: Resolved Bugs

Search resolved/closed bugs matching summary terms:
```
project = <PROJECT> AND issuetype = Bug AND key != <CURRENT-KEY> AND status in (Resolved, Done, Closed) AND (<summary clauses>) AND updated >= "-365d" ORDER BY updated DESC
```

Limit: 5 results.

## Strategy 3: Open Bugs

Search open bugs matching summary terms:
```
project = <PROJECT> AND issuetype = Bug AND key != <CURRENT-KEY> AND status not in (Resolved, Done, Closed) AND (<summary clauses>) AND updated >= "-365d" ORDER BY created DESC
```

Limit: 5 results.

## Strategy 4: Same Component

If the bug has a component, search by component:
```
project = <PROJECT> AND issuetype in (Story, Task, Epic) AND component = "<COMPONENT>" AND updated >= "-365d" ORDER BY updated DESC
```

Limit: 5 results.

## Strategy 5: Linked and Epic Keys

If the bug has linked issues or an epic, fetch those directly by key.

## Post-Processing

1. Deduplicate across all strategies by issue key.
2. Cap at 25 candidates.
3. Pass to relevance ranking (see `references/prompts/relevance-ranking.md`).

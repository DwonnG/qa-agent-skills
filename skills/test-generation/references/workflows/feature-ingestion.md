# Feature Ingestion

How to gather context from Jira and Confluence for test planning.

## Epic Context

Fetch the epic and all linked stories:
```
jira-cli --format json view <EPIC-KEY>
jira-cli --format json search --jql '"Epic Link" = <EPIC-KEY>' --limit 50
```

Collect from each ticket:
- Summary, description, acceptance criteria
- Issue type and status
- Fix version
- Linked issues (blocks, is-blocked-by, relates-to)

## Confluence URLs

Scan ticket descriptions and comments for Confluence links. Common patterns:
- `https://<instance>.atlassian.net/wiki/spaces/<SPACE>/pages/<ID>/<TITLE>`
- `https://<instance>/wiki/display/<SPACE>/<TITLE>`

Extract the page ID from the URL path.

## PR Context

Find related PRs for code-level understanding:
```
gh pr list --search "<ISSUE-KEY>" --json number,title,state,headRefName
```

Review PR descriptions and changed files to understand implementation details.

## Output

Combine all gathered context into a structured summary:
- Epic objective and scope
- Story-by-story requirements
- Confluence document summaries
- Implementation notes from PRs

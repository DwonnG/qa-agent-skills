# config - Prerequisite Setup

`testplan-generator` is a composite skill. Configure the underlying CLI wrappers individually before using the skill end to end.

## Required Setup Order

1. Configure Confluence access through the shared `confluence-pages` skill.

2. Configure Jira access through the shared `jira-issues` skill.

3. Configure GitHub access (github.com or your GitHub Enterprise host) through the shared `github-manager` skill.

## What To Verify

- Confluence auth succeeds for the instance that hosts the supplied page URLs.
- Jira auth succeeds for the instance that hosts the supplied issue keys or URLs.
- GitHub Enterprise auth is valid for `github.com` when GitHub URLs or Jira-linked PR artifacts are used.

## Notes

- This skill does not have a single unified `config` subcommand because it composes three separate authenticated CLIs.
- Keep secrets in the underlying tools' secure storage. Do not print tokens in chat or terminal logs.

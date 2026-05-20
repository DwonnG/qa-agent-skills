# Jira Transitions

Available transitions and when to use each.

| Transition | When to Use |
|---|---|
| backlog | Move to backlog for future consideration |
| grooming | Ready for team grooming/refinement |
| open | Newly opened, ready for assignment |
| in_progress | Development actively working on it |
| pr_pending_review | PR submitted, awaiting code review |
| resolved | Fix verified and complete |
| blocked | Cannot proceed due to external dependency |
| reopened | QA failed or issue recurred |
| closed | Fully complete, no further action |
| qa | Ready for QA validation |
| staging_qa | Ready for QA in beta environment |

## Transition Commands

```
jira-cli transition <ISSUE-KEY> --to <TRANSITION-NAME>
```

Transition IDs are project-specific. The CLI resolves names to IDs automatically.

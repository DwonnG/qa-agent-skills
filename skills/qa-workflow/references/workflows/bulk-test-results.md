# Bulk Test Result Update

Update test results for multiple tickets at once, typically after a release testing pass.

## Dry Run (Mandatory)

All bulk updates require explicit user confirmation. Present the full list of proposed changes before executing any writes.

## Steps

1. **Gather the ticket list**: Accept from the user as:
   - A list of issue keys (e.g., `PROJ-51001, PROJ-51002, PROJ-51003`)
   - An epic key to update all children (e.g., "mark all QA tickets in PROJ-51296 as passed")
   - A JQL query (e.g., "all QA tickets in sprint X assigned to me")

2. **If epic or JQL, fetch the tickets**:
   ```
   jira-cli search --jql '"Epic Link" = <EPIC-KEY> AND status in (QA, "Beta QA")' --format json
   ```

3. **Present dry run** showing each ticket and the proposed change:
   ```
   Bulk Update: Set Test Result = Pass, Transition = Resolved
   ============================================================
   PROJ-51001 | Fix email routing | Currently: QA / In Progress
   PROJ-51002 | Update policy engine | Currently: QA / Not Tested
   PROJ-51003 | Add retry logic | Currently: Beta QA / In Progress

   Total: 3 tickets
   Proceed? (yes/no)
   ```

4. **On confirmation, for each ticket**:
   a. Add a QA pass comment using the template from `references/comment-templates.md`.
   b. Transition to resolved: `jira-cli transition <ISSUE-KEY> --to resolved`
   c. Report success or failure for each ticket.

   For field-only bulk updates (e.g., setting Validator on multiple tickets), `jira-cli bulk-update` can be used with `--dry-run` first:
   ```
   jira-cli bulk-update --jql '<JQL>' --field '<VALIDATOR_FIELD_ID>={"name":"<USERNAME>"}' --dry-run
   ```

5. **Summary report**:
   ```
   Bulk Update Complete
   ====================
   Succeeded: 2
   Failed: 1 (PROJ-51003: transition error - already resolved)
   ```

## Supported Operations

| Action | What It Does |
|--------|-------------|
| Bulk pass | Set test result to Pass + transition to Resolved + add pass comment |
| Bulk fail | Set test result to Fail + transition to Reopened + add fail comment |
| Bulk claim | Assign to current user + set Validator + set test result to In Progress |

## Notes

- Never execute without the dry run confirmation step.
- Process tickets sequentially to provide clear error reporting per ticket.
- If a transition fails for one ticket, continue with the remaining tickets and report failures at the end.

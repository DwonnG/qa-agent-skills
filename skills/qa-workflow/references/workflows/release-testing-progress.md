# Release Testing Progress

Track the QA validation progress for all tickets linked to a release epic.

## Steps

1. **Identify the release epic**: Get the epic key from the user (e.g., `PROJ-51296`).

2. **Fetch all issues in the epic**:
   ```
   jira-cli search --jql '"Epic Link" = <EPIC-KEY>' --format json
   ```

3. **Categorize each issue** by its status and test result:
   - **Passed**: status = Resolved/Closed with Test Result = Pass
   - **Failed**: status = Reopened with Test Result = Fail
   - **In QA**: status = QA or Beta QA with Test Result = In Progress
   - **Not Started**: status = QA or Beta QA with no Validator and no Test Result
   - **Blocked**: status = Blocked
   - **In Dev**: status = In Progress or PR Pending Review

4. **Calculate progress**:
   - Total issues in epic
   - Count per category
   - Percentage complete (Passed / Total)

5. **Report summary**:
   ```
   Release <VERSION> Testing Progress
   ===================================
   Total: <N> issues
   Passed:      <N> (<P>%)
   Failed:      <N>
   In QA:       <N>
   Not Started: <N>
   Blocked:     <N>
   In Dev:      <N>
   ```

6. **List failed tickets** with their summaries and assignees for follow-up.

## Notes

- The Test Result custom field (<TEST_RESULT_FIELD_ID>) values are: Pass, Fail, In Progress, Blocked, Not Tested.
- The Validator custom field (<VALIDATOR_FIELD_ID>) indicates who is assigned for QA.
- jira-cli returns these in the JSON output fields.

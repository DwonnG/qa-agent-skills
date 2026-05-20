# Release Epic Setup

Clone a release testing template epic and its linked tasks for a new release version.

## Template

- Template epic key: `PROJ-49840`
- Summary format: `Release {version} Testing`

## Steps

1. **Fetch template epic** and its linked tasks:
   ```
   jira-cli --format json view PROJ-49840
   jira-cli --format json search --jql '"Epic Link" = PROJ-49840'
   ```

2. **Create new epic** with the release version in the summary:
   ```
   jira-cli create --type Epic --summary "Release {version} Testing" --project PROJ
   ```

3. **Clone each linked task** under the new epic, preserving:
   - Summary (with version substituted)
   - Description
   - Labels
   - Component

4. **Link tasks** to the new epic.

5. **Report** the new epic key and count of cloned tasks.

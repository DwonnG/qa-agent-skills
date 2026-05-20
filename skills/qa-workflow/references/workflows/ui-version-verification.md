# UI Version Verification

Validate the deployed UI application shows the expected version, build, and environment.

## Steps

1. **Fetch issue details** to extract the expected version:
   ```
   jira-cli --format json view <ISSUE-KEY>
   ```

2. **Determine target environment**: Default is integration.

3. **Check UI version**: The UI console typically exposes version, build hash, and environment info. This may require browser-based verification or API endpoint checks depending on the application.

4. **Compare** the deployed version against the expected version from the ticket.

5. **Report results**: State whether the version matches, and include the actual values observed.

6. **Resolve ticket** if version matches (when auto_resolve is requested).

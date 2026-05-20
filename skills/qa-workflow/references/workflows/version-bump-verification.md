# Version Bump Verification

Verify a version bump is deployed across one or more repos in a target environment.

## Steps

1. **Fetch issue details** to extract the expected version:
   ```
   jira-cli --format json view <ISSUE-KEY>
   ```

2. **Identify repos**: Extract from the ticket description or use the provided repo list.

3. **Check deployment per repo**: Look up job paths in `~/.claude/skills/test-build-insight/references/jenkins-jobs.md`, then check recent builds:
   ```
   ~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format json builds <JOB-PATH> 5
   ```
   Inspect build logs for version strings:
   ```
   ~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format text logs <JOB-PATH> <BUILD-NUMBER> --full-logs | grep -i "version"
   ```

4. **Check Lambda timestamps** (optional): Use the deployment config from `~/.claude/skills/test-build-insight/references/deployment-config.md`:
   ```
   AWS_PROFILE=app_engineer aws lambda get-function-configuration --function-name <FUNCTION_NAME> --query 'LastModified' --output text
   ```

5. **Compare environments** if needed: Confirm the version in the target environment matches expectations by repeating steps 3-4 for each environment.

6. **Report results**: Summarize which repos are verified and which are pending.

7. **Resolve ticket** if all repos pass (when auto_resolve is requested). This is a write operation -- present a dry run first.

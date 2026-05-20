# E2E Test Status Check

Interpret the latest E2E build results for a repo, beyond just listing builds.

## Steps

1. **Resolve the job path** from `references/jenkins-jobs.md` using the repo name and `e2e` job type.

2. **Fetch the latest build**:
   ```
   ~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format json builds <JOB-PATH> 1
   ```

3. **Get build details** for the latest build number:
   ```
   ~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format json build-info <JOB-PATH> <BUILD-NUMBER>
   ```

4. **Interpret the result**:
   | Jenkins Result | Tests Passed | Summary |
   |---------------|-------------|---------|
   | SUCCESS | Yes | E2E tests passed |
   | FAILURE | No | E2E tests failed |
   | UNSTABLE | No | E2E tests unstable (some failures) |
   | null (building) | Unknown | E2E tests currently running |
   | Other | Unknown | Unknown status: {result} |

5. **Report** a summary including:
   - Repo name and job type
   - Build number and URL
   - Result and human-readable interpretation
   - Timestamp and duration
   - Whether tests are currently building

## Extended: Check Specific Build

If checking a build after a specific commit/merge:
1. List recent builds: `jenkins-cli --format json builds <JOB-PATH> 10`
2. Find the build with a timestamp after the merge time.
3. Report that build's result using the interpretation table above.

## Extended: Test Failure Details

For failed/unstable builds, get filtered logs:
```
~/.claude/skills/jenkins-manager/scripts/jenkins-cli --format toon logs <JOB-PATH> <BUILD-NUMBER> 'FAIL|ERROR|AssertionError'
```

# Deployment Check

Verify which version of code is deployed to a given environment by checking AWS Lambda function timestamps.

## Prerequisites

Requires AWS CLI with the `app_engineer` profile. Always set `AWS_PROFILE=app_engineer` before calling `aws lambda`.

## Steps

1. **Look up the repo** in `references/deployment-config.md` to get the list of Lambda functions for the target environment.

2. **Check each Lambda function**:
   ```bash
   AWS_PROFILE=app_engineer aws lambda get-function-configuration \
     --function-name <FUNCTION_NAME> \
     --query 'LastModified' \
     --output text
   ```

3. **Compare timestamps** (optional): If you have a commit or merge timestamp, compare each Lambda's `LastModified` against it.
   - If `LastModified` is after the commit timestamp, the function has been updated since the commit.
   - If `LastModified` is before the commit timestamp, the function has NOT been redeployed.

4. **Summarize per function**:
   - `[OK]` if deployed after the reference timestamp (or if no reference, just report the timestamp)
   - `[STALE]` if deployed before the reference timestamp
   - `[ERROR]` if the function could not be found or access was denied

5. **Overall verdict**: All functions must be `[OK]` for the repo to be considered fully deployed.

## Environment Comparison

To compare two environments:
1. Collect `LastModified` for all functions in environment A.
2. Collect `LastModified` for all functions in environment B.
3. Report any functions where environment B is older than environment A (drift).

## Supported Repos and Environments

See `references/deployment-config.md` for the full mapping. Currently tracked:
- api-service (integration, qa)
- policy-service (integration, qa)
- directory-data (integration, qa)
- frontend-app (integration, qa)

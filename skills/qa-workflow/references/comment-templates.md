# Comment Templates

Wiki markup templates for QA validation comments in Jira.

## QA Pass

```
h3. QA Validation - PASS

*Environment:* {environment}

*Verification:*
{verification_steps}

*Test Result:* PASS - {summary}
```

## QA Fail

```
h3. QA Validation - FAIL

*Environment:* {environment}

*Issue Found:*
{issue_description}

*Steps to Reproduce:*
{steps}

*Expected:* {expected}
*Actual:* {actual}

*Test Result:* FAIL - Returning to development for fix.
```

## Vulnerability Verification

```
h3. Vulnerability Verification - {PASS|FAIL}

*Environment:* {environment}
*PR:* {pr_url}
*Deployed:* {yes|no}
*E2E Tests:* {pass|fail}

*Verification Summary:*
{details}
```

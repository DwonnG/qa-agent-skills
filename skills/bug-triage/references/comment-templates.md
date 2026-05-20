# Comment Templates

Wiki markup templates for Jira comments. Use these formats when posting triage results or QA validation results.

## Triage Comment

```
h2. AI Bug Triage

h3. Summary
{triage_summary}

h3. Priority: {priority}
{severity_reasoning}

h3. Assigned Team: {team}
* Product Owner: [~{po}]
* QA: [~{qa}]
* Confidence: {confidence}

h3. Investigation Hints
{investigation_hints_as_bullets}

h3. Recommended Actions
{actions_as_bullets}

h3. Related Issues
|| Key || Score || Reason ||
{related_issues_table_rows}

{panel:title=Bug Type|borderColor=#ccc}
Type: {bug_type}
Impact: {impact_scope}
Root Cause Area: {root_cause_area}
{panel}
```

## QA Pass Comment

```
h3. QA Validation - PASS

*Environment:* {environment}

*Verification:*
{verification_steps}

*Test Result:* PASS - {summary}
```

## QA Fail Comment

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

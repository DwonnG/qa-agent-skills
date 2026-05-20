# Testcase Template

Use this template when the user asks for fully written testcases instead of only a scenario list.
If the user asked for a full detailed plan, expand every materially distinct scenario with this template.

## Rules

- Keep the exact section names and order.
- Do not invent missing details.
- If a detail is unknown from source material, write `Unknown`.
- If an expected result is inferred rather than stated, label it `Inferred`.
- Prefer one testcase per observable behavior.
- Prefer concrete runtime steps and validations over abstract placeholders.
- If the evidence supports end-to-end validation, make the testcase explicitly end-to-end.
- Reuse observable artifacts from the evidence such as sender mailbox, recipient mailbox, journal, delivery status, stored message, modified message id, policy retrieval, API response, logs, or metrics.

## Template

```markdown
### <Test Case Title>

**Title**
- <Test Case Title>

**Pre-condition**
- <precondition 1>
- <precondition 2>

**Test Case Steps**
1. <step 1>
2. <step 2>
3. <step 3>

**Expected Behaviour**
- <expected behavior>

**Pass/Fail Criterion**
Pass if <objective pass condition>.

**Teardown**
- <cleanup step 1>
- <cleanup step 2>
```

## Population Guidance

### Title

- Use a behavior-driven title.
- Mention the main condition and the expected effect.

Example:
- `Verify SPF authentication result drives filtering correctly for a real inbound message`

Always include the explicit `Title` field in the testcase body, even if the surrounding heading already contains the title.

### Pre-condition

Include only setup conditions known from the sources, such as:
- policy or rule configured
- tenant or environment requirement
- mail sample requirement
- user role requirement
- sender/recipient mailbox availability
- journal or delivery-status visibility
- stored-message retrieval availability
- baseline policy state

If the required setup is not documented, write:
- `Unknown`

### Test Case Steps

- Use concrete observable actions.
- Prefer runtime validation steps over internal implementation assumptions.
- Reference actual source-backed artifacts when known, such as UI, API, logs, S3, PRODUCT UI, or message verdicts.
- If the feature is mail-processing and the evidence supports it, write the steps in an execution order such as:
  1. configure or update the rule/policy
  2. send a real or representative inbound message from a sender
  3. retrieve the message id or correlation id
  4. validate journal, mailbox folder, delivery status, stored-message, or runtime artifacts
  5. confirm the final recipient-visible outcome
- Avoid generic filler such as `Execute the relevant flow` or `Observe outputs as applicable`.

### Expected Behaviour

- State the user-visible or system-visible outcome.
- If not directly documented, mark the statement as `Inferred`.
- Prefer outcomes that mention what is visible in the final mailbox, journal, stored message, policy retrieval, API result, or logs when those artifacts are supported by the sources.

### Pass/Fail Criterion

- Use a crisp measurable condition.
- Avoid vague wording like `works correctly`.
- Prefer conditions tied to explicit artifacts, for example:
  - header present or absent in delivered message
  - recipient mailbox folder matches expectation
  - message is not delivered
  - modified message id is returned and resolves correctly
  - policy retrieval contains the expected rule values
  - logs or metrics contain the expected decision evidence

### Teardown

- Remove created rules or policy changes.
- Delete sent test emails if that behavior is known from existing patterns.
- If teardown is not specified in the sources, write `Unknown`.

## Anti-Patterns To Avoid

- Generic step text such as `prepare the setup required` without saying what is configured
- Generic validation text such as `validate expected behavior`
- Expected outcomes that do not identify an observable artifact
- Detailed testcases that only restate API or design wording when the evidence supports mailbox-visible end-to-end validation

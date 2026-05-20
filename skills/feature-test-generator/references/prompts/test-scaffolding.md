# Test Scaffolding

Generate E2E test code that matches the established conventions in the target repository.

## Read Before You Write

Before generating any test code, you MUST read the following files in the target E2E test directory:

1. **`conftest.py`** -- Learn the available fixtures, setup/teardown patterns, CLI options, and environment configuration.
2. **One existing test file** in the same area as the feature being tested -- Learn the import style, marker usage, class vs function style, fixture parameters, assertion patterns, and naming conventions.

Do NOT assume conventions. Every repo and test directory has its own patterns. Let the existing code teach you.

## Generation Rules

1. **Match the style exactly** -- If existing tests use class-based tests, use classes. If they use standalone functions, use functions. Match indentation, import ordering, and assertion style.

2. **Use the same fixtures** -- Only use fixtures that exist in the conftest. Do not invent new fixtures unless the test truly needs something that doesn't exist.

3. **Use registered markers** -- Only use pytest markers that appear in existing tests or are registered in `tox.ini`/`pyproject.toml`/`setup.cfg`. Check which markers similar tests use and follow the same pattern.

4. **Jira traceability** -- Always include the Jira ticket URL in a module-level docstring:
   ```python
   """
   https://jira.example.com/browse/PROJ-XXXXX
   """
   ```

5. **Naming** -- File: `test_<feature>.py`. Function/method: `test_<behavior>`. Match the granularity of existing tests in the same directory.

6. **Test content** -- Derive test scenarios from:
   - Jira ticket acceptance criteria
   - The PR diff (what behavior was added/changed)
   - Existing test patterns in the same area (what they typically verify)

7. **Keep it focused** -- Generate 2-5 test functions covering the key scenarios. Don't over-test. Cover the happy path, one error case, and any edge cases from the acceptance criteria.

## Extending an Existing File

When adding to an existing test file:
- Add new test functions at the end of the file (or end of the class if class-based)
- Follow the same fixture usage as the other tests in the file
- Do not modify existing tests
- Show a diff of what will be added

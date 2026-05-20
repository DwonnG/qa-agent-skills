# Test Segmentation Analysis

Heuristics for detecting bulky, tightly-coupled, or redundant tests and recommendations for splitting them into smaller, focused, parallelizable tests.

Run this analysis before converting a Selenium test to Playwright. The goal is to improve the test during migration, not just translate it 1:1.

## Heuristics

### 1. Size: Lines and Assertions

**Threshold:** A test function with >50 lines or >10 `assert` statements is a candidate for splitting.

**Why:** Large tests are harder to debug (which assertion failed?), slower to run, and cannot be parallelized internally.

**Action:** Split into one test per logical verification. Each test should have 1-3 assertions that verify a single behavior.

```python
# Before — one bulky test
def test_admin_user_permissions(app, env_consts):
    app.login()
    admin_page = app.get_admin_page()
    assert admin_page.is_google_analytics_enabled()
    # ... 20 more lines of setup ...
    msg_page = app.get_messages_page()
    assert msg_page.is_remediation_enabled()
    # ... 15 more lines ...
    config_page = app.get_configuration_page()
    assert config_page.is_policy_tab_visible()
    # ... etc

# After — split by feature area
def test_admin_analytics_permissions(app):
    app.login()
    admin_page = app.get_admin_page()
    assert admin_page.is_google_analytics_enabled()

def test_admin_remediation_permissions(app):
    app.login()
    msg_page = app.get_messages_page()
    assert msg_page.is_remediation_enabled()

def test_admin_config_permissions(app):
    app.login()
    config_page = app.get_configuration_page()
    assert config_page.is_policy_tab_visible()
```

### 2. Multiple Flows in One Test

**Detection:** A test that calls `app.login()` or navigates to multiple distinct pages (e.g., messages page then config page then admin page) is testing multiple flows.

**Signals:**
- Multiple `app.open_*_page()` or `app.get_*_page()` calls on different pages
- Multiple unrelated navigation steps
- Comments separating "phases" (e.g., `# Navigate to Help Center - Release Notes` then `# Navigate to Help Center - User Guide`)

**Action:** Split at the flow boundaries. Each test navigates to one page and verifies one flow.

```python
# Before — tests 4 help page navigations in one function
def test_navigate_to_help_pages(app):
    app.login()
    home = app.get_home_page()
    # Navigate to Release Notes
    current_url = home.open_release_notes()
    assert release_notes_path in current_url
    home.switch_back_to_etd_tab()
    # Navigate to User Guide
    current_url = home.open_user_guide()
    assert user_guide_path in current_url
    home.switch_back_to_etd_tab()
    # Navigate to Public API Guide
    current_url = home.open_public_api_guide()
    assert public_api_url in current_url
    home.switch_back_to_etd_tab()
    # Navigate to FAQs
    current_url = home.open_freq_asked_questions()
    assert freq_asked_questions_path in current_url

# After — one test per help page, can run in parallel
@pytest.mark.parametrize("page_name,open_method,expected_path", [
    ("release_notes", "open_release_notes", "/Content/.../Home-RN.htm"),
    ("user_guide", "open_user_guide", "/Content/.../homeUG.htm"),
    ("public_api", "open_public_api_guide", "https://example.com/docs/api/"),
    ("faqs", "open_freq_asked_questions", "/Content/.../Home-FAQ.htm"),
])
def test_navigate_to_help_page(app, page_name, open_method, expected_path):
    app.login()
    home = app.get_home_page()
    current_url = getattr(home, open_method)()
    assert expected_path in current_url
```

### 3. Setup-Heavy Tests

**Threshold:** If >40% of a test function body is setup/teardown (API calls, data creation, feature toggle manipulation, waiting for preconditions), extract that into a fixture.

**Signals:**
- `ApiClient()` calls inside the test body
- `Lambda()` / `boto3` calls for environment manipulation
- Feature toggle enable/disable (`app.enable_feature_toggle(...)`)
- Long blocks before the first assertion

**Action:** Move setup into a `@pytest.fixture` and pass it to the test.

```python
# Before — setup dominates the test
def test_bulk_remediation(app):
    lambda_helper = Lambda(env=app.env_configs.env)
    original_value = lambda_helper.get_env_var(LAMBDA_NAME, "bulk_action_message_threshold")
    lambda_helper.update_env_var(LAMBDA_NAME, "bulk_action_message_threshold", "5")
    app.login()
    app.enable_feature_toggle(BULK_REMEDIATION_FEATURE_FLAG, True)
    msg_page = app.get_messages_page()
    # ... actual test logic ...

# After — setup extracted to fixture
@pytest.fixture
def bulk_remediation_env(app):
    lambda_helper = Lambda(env=app.env_configs.env)
    original = lambda_helper.get_env_var(LAMBDA_NAME, "bulk_action_message_threshold")
    lambda_helper.update_env_var(LAMBDA_NAME, "bulk_action_message_threshold", "5")
    app.enable_feature_toggle(BULK_REMEDIATION_FEATURE_FLAG, True)
    yield
    lambda_helper.update_env_var(LAMBDA_NAME, "bulk_action_message_threshold", original)

def test_bulk_remediation(app, bulk_remediation_env):
    app.login()
    msg_page = app.get_messages_page()
    # ... focused test logic ...
```

### 4. Sequential Dependency

**Detection:** Tests in a file that rely on execution order (test B depends on state created by test A).

**Signals:**
- `pytest-ordering` markers (`@pytest.mark.run(order=N)`)
- Module-level variables mutated by tests
- Tests that fail when run in isolation or in different order
- Comments like "must run after test_X"

**Action:**
- Make each test independent with its own setup/teardown
- If shared state is necessary, use session-scoped fixtures with proper cleanup
- Consider if the dependency means these are really one test that should be a single function

### 5. xdist Group Analysis

**Current state:** Tests use `@pytest.mark.xdist_group(name="policy-insensitive")` or similar to control parallel grouping.

**Opportunities:**
- Tests in `policy-insensitive` group that do NOT modify policies can often run fully parallel (no group needed)
- Tests NOT in any group that DO modify shared state (policies, feature toggles, message rules) should be in a group
- Tests in the same group that don't interact can be split into separate groups for better parallelism

**Action:** Review each test's actual side effects:

| Side Effect | Grouping |
|---|---|
| Read-only (navigate, assert visibility) | No group needed — fully parallel |
| Modifies feature toggles | Group with other toggle tests |
| Modifies policies | Group: `policy-sensitive` |
| Creates/deletes message rules | Group: `message-rules` |
| Modifies admin settings | Group: `admin-settings` |

### 6. Redundancy Detection

**Detection:** Tests in the same file or directory that verify overlapping behaviors.

**Signals:**
- Multiple tests that login and navigate to the same page with similar assertions
- Tests that verify the same element exists in different contexts
- Tests that were written for different bugs but now cover the same code path

**Action:**
- Merge overlapping tests into parameterized tests
- Remove lower-value duplicates (keep the one with better coverage)
- Document why coverage was reduced if removing tests

## Segmentation Report Format

When analyzing a file, output this structure:

```
## Segmentation Report: <filename>

### Summary
- Total tests: N
- Candidates for splitting: N
- Candidates for fixture extraction: N
- Parallelization opportunities: N
- Redundancy candidates: N

### Split Recommendations

#### test_function_name (line X)
- **Reason:** [size | multiple-flows | ...]
- **Current:** 1 test, ~Y lines, Z assertions
- **Proposed:** Split into N tests:
  1. `test_specific_behavior_a` — verifies [what]
  2. `test_specific_behavior_b` — verifies [what]

### Fixture Extraction

#### test_function_name (line X)
- **Setup block:** lines X-Y (~N lines, N% of test body)
- **Proposed fixture:** `fixture_name` — [what it sets up]
- **Cleanup needed:** [yes/no, what]

### Parallelization

| Test | Current Group | Recommendation | Reason |
|---|---|---|---|
| `test_name` | `policy-insensitive` | Remove group | Read-only test |
| `test_name` | None | Add `admin-settings` | Modifies feature toggles |

### Redundancy

| Test A | Test B | Overlap | Recommendation |
|---|---|---|---|
| `test_x` | `test_y` | Both verify nav to messages | Merge into parameterized |
```

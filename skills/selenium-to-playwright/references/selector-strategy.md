# Selector Strategy

How to convert enterprise Selenium pytest suites selectors from Selenium to Playwright locators.

## Priority Order

When converting, prefer locators in this order (most resilient first):

1. **`get_by_test_id`** — for `data-testid` attributes (heavily used in this codebase)
2. **`get_by_role`** — for semantic elements (buttons, headings, links)
3. **`get_by_text`** — for text content matching
4. **CSS locator** — for structural selectors
5. **XPath locator** — last resort, only when CSS cannot express the query

## `data-testid` Selectors (Most Common)

The codebase uses `GET_BY_TEST_ID = '[data-testid="{}"]'` extensively.

### Before

```python
from tests.constants.constants import GET_BY_TEST_ID

REMEDIATION_MODAL_CSS = GET_BY_TEST_ID.format("confirm-modal")
self.click_with_wait(self.REMEDIATION_MODAL_CSS)
```

### After

```python
self.page.get_by_test_id("confirm-modal").click()
```

### Partial match: `GET_BY_TEST_ID_PARTLY`

```python
# Before: GET_BY_TEST_ID_PARTLY = '[data-testid*="{}"]'
selector = GET_BY_TEST_ID_PARTLY.format("widget")

# After: use CSS locator for partial match
self.page.locator('[data-testid*="widget"]')
```

## CSS Selectors

CSS selectors work directly in Playwright. No prefix needed.

```python
# Before
self.click_with_wait('[class*="spinner"] svg', find_by=By.CSS_SELECTOR)

# After
self.page.locator('[class*="spinner"] svg').click()
```

### Common CSS patterns in this codebase

| Pattern | Example | Playwright |
|---|---|---|
| Class contains | `[class*="table--loading"]` | `page.locator('[class*="table--loading"]')` |
| Data attribute exact | `[data-testid="loader"]` | `page.get_by_test_id("loader")` |
| Data attribute partial | `[data-testid*="widget"]` | `page.locator('[data-testid*="widget"]')` |
| Nested | `[data-testid="date-time-to-picker"] [data-testid="cds-date-time-picker"]` | `page.get_by_test_id("date-time-to-picker").get_by_test_id("cds-date-time-picker")` |
| Title attribute | `[title="Delete"]` | `page.locator('[title="Delete"]')` or `page.get_by_title("Delete")` |

## XPath Selectors

Prefix with `xpath=` in Playwright.

```python
# Before
self.click_with_wait('//button[text()="Save"]', find_by=By.XPATH)

# After
self.page.locator('xpath=//button[text()="Save"]').click()
```

### Convert XPath to Playwright-native when possible

| XPath | Playwright native |
|---|---|
| `//h1[text()="Messages"]` | `page.get_by_role("heading", name="Messages")` |
| `//button[text()="Save"]` | `page.get_by_role("button", name="Save")` |
| `//button[text()="Cancel"]` | `page.get_by_role("button", name="Cancel")` |
| `//span[contains(text(), 'Select verdict')]` | `page.get_by_text("Select verdict")` |
| `//a[@data-testid='nav-link-trends']` | `page.get_by_test_id("nav-link-trends")` |
| `//*[@data-testid='nav-link-dashboard']` | `page.get_by_test_id("nav-link-dashboard")` |

### Keep as XPath when conversion is not straightforward

Complex XPath with axes, positional predicates, or ancestor/sibling traversals should stay as XPath:

```python
# ancestor axis — keep as XPath
'./ancestor::*[@data-testid="cds-select-control"]'
# Playwright:
locator.locator('xpath=./ancestor::*[@data-testid="cds-select-control"]')

# Dynamic format strings with axes
'//span[contains(text(), "{}")]/..//span[contains(@class, "icon")]'.format(label)
# Playwright:
page.locator(f'xpath=//span[contains(text(), "{label}")]/..//span[contains(@class, "icon")]')
```

## Dynamic Selectors (Format Strings)

The codebase uses `.format()` for dynamic selectors. Keep the pattern but update the locator call:

```python
# Before
MAGNETIC_DYNAMIC_WIDGET_CONTAINER_XPATH = "//*[@data-testid='{}-widget-container']"
self.is_element_visible(
    self.MAGNETIC_DYNAMIC_WIDGET_CONTAINER_XPATH.format(container.lower()), By.XPATH)

# After
MAGNETIC_DYNAMIC_WIDGET_CONTAINER = "{}-widget-container"
self.page.get_by_test_id(self.MAGNETIC_DYNAMIC_WIDGET_CONTAINER.format(container.lower())).is_visible()
```

## `By` Enum Removal

Remove all `from selenium.webdriver.common.by import By` imports. Replace the `find_by` parameter pattern:

| `find_by` value | Conversion |
|---|---|
| `By.CSS_SELECTOR` | Default — no prefix needed |
| `By.XPATH` | Prefix selector with `xpath=` |
| `By.ID` | Use `page.locator(f"#{id_value}")` |
| `By.CLASS_NAME` | Use `page.locator(f".{class_name}")` |
| `By.NAME` | Use `page.locator(f'[name="{name}"]')` |

## Helper Method for Converted BasePage

A `_locator` helper on the converted `BasePage` handles the `find_by` branching:

```python
def _locator(self, selector: str, find_by: str = "css"):
    """Return a Playwright Locator from a selector string.
    
    find_by: "css" (default) or "xpath"
    """
    if find_by == "xpath":
        return self.page.locator(f"xpath={selector}")
    return self.page.locator(selector)
```

This keeps the migration incremental — existing call sites that pass `find_by` continue to work while you migrate selectors to Playwright-native locators over time.

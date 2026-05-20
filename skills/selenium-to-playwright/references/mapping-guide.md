# Selenium to Playwright API Mapping

Complete mapping of Selenium 3 APIs used in enterprise Selenium pytest suites to their Playwright equivalents.

## Imports

### Before (Selenium)

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selen_kaa.webdriver import SeWebDriver
from tests.application.driver_wrapper import DriverWrapper
from tests.application.base_page import BasePage
import time
```

### After (Playwright)

```python
from playwright.sync_api import Page, expect
```

Remove all `selenium.*`, `selen_kaa.*`, `DriverWrapper`, and `time` imports (unless `time` is used for non-UI purposes like API polling).

## Element Location

| Selenium | Playwright |
|---|---|
| `driver.find_element(By.CSS_SELECTOR, sel)` | `page.locator(sel)` |
| `driver.find_element(By.XPATH, sel)` | `page.locator(f"xpath={sel}")` |
| `driver.find_elements(By.CSS_SELECTOR, sel)` | `page.locator(sel).all()` |
| `driver.find_element_by_css_selector(sel)` | `page.locator(sel)` |
| `driver.find_element_by_xpath(sel)` | `page.locator(f"xpath={sel}")` |
| `webdriver.init_web_element(sel)` | `page.locator(sel)` |
| `webdriver.init_all_web_elements(sel)` | `page.locator(sel).all()` |

## Waiting

Playwright auto-waits on all actionable operations. Remove all explicit waits.

| Selenium | Playwright |
|---|---|
| `WebDriverWait(driver, t).until(ec.visibility_of_element_located(...))` | `page.locator(sel).wait_for(state="visible")` or just use the locator directly |
| `WebDriverWait(driver, t).until(ec.element_to_be_clickable(...))` | `page.locator(sel).click()` (auto-waits for clickable) |
| `WebDriverWait(driver, t).until(ec.invisibility_of_element_located(...))` | `page.locator(sel).wait_for(state="hidden")` |
| `WebDriverWait(driver, t).until(ec.text_to_be_present_in_element(...))` | `expect(page.locator(sel)).to_contain_text(text)` |
| `time.sleep(N)` | Remove. Use `page.wait_for_timeout(N * 1000)` only as absolute last resort. |

## Actions

| Selenium | Playwright |
|---|---|
| `element.click()` | `page.locator(sel).click()` |
| `element.send_keys(text)` | `page.locator(sel).fill(text)` or `page.locator(sel).type(text)` for keystroke simulation |
| `element.send_keys(Keys.RETURN)` | `page.locator(sel).press("Enter")` |
| `element.send_keys(Keys.BACKSPACE)` | `page.locator(sel).press("Backspace")` |
| `element.send_keys(ctrl + 'a')` | `page.locator(sel).press("Meta+a")` (macOS) or `page.locator(sel).press("Control+a")` |
| `element.clear()` | `page.locator(sel).clear()` |
| `element.set_text_value(text)` (legacy driver wrapper) | `page.locator(sel).fill(text)` |
| `element.is_selected()` | `page.locator(sel).is_checked()` |
| `element.is_enabled()` | `page.locator(sel).is_enabled()` |
| `element.get_attribute(attr)` | `page.locator(sel).get_attribute(attr)` |
| `element.text` | `page.locator(sel).text_content()` |
| `element.value_of_css_property(prop)` | `page.locator(sel).evaluate("el => getComputedStyle(el).prop")` |

## Mouse and Hover

| Selenium | Playwright |
|---|---|
| `ActionChains(driver).move_to_element(el).perform()` | `page.locator(sel).hover()` |
| `driver.execute_script("arguments[0].scrollIntoView(true);", el)` | `page.locator(sel).scroll_into_view_if_needed()` |
| `driver.execute_script("arguments[0].click();", el)` | `page.locator(sel).dispatch_event("click")` |
| JS `dispatchEvent(new MouseEvent('mouseover', ...))` | `page.locator(sel).hover()` |

## Navigation

| Selenium | Playwright |
|---|---|
| `driver.get(url)` | `page.goto(url)` |
| `driver.title` | `page.title()` |
| `driver.current_url` | `page.url` |
| `driver.execute_script("window.open(url, '_blank')")` | Use `context.new_page()` or `page.evaluate("() => window.open(url)")` then handle via `page.context.pages` |
| `driver.switch_to.window(handles[1])` | `context.pages[1]` — Playwright tracks pages per context |
| `driver.close()` | `page.close()` |

## Checkboxes and Toggles

| Selenium | Playwright |
|---|---|
| `element.is_selected()` | `page.locator(sel).is_checked()` |
| Check if selected then click | `page.locator(sel).set_checked(True)` or `page.locator(sel).set_checked(False)` |

## Assertions

| Selenium (pytest assert) | Playwright (expect API) |
|---|---|
| `assert text in element.text` | `expect(page.locator(sel)).to_contain_text(text)` |
| `assert element is visible` (via try/except TimeoutException) | `expect(page.locator(sel)).to_be_visible()` |
| `assert element is not visible` | `expect(page.locator(sel)).to_be_hidden()` |
| `assert url_part in driver.current_url` | `expect(page).to_have_url(re.compile(url_part))` |
| `assert element.get_attribute("checked")` | `expect(page.locator(sel)).to_be_checked()` |

## Timeouts

Playwright default timeout is 30 seconds. To customize per-action:

```python
page.locator(sel).click(timeout=5000)
expect(page.locator(sel)).to_be_visible(timeout=10000)
```

Global timeout via `playwright.config`:

```python
# conftest.py
@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1750, "height": 1080}}
```

## JavaScript Execution

| Selenium | Playwright |
|---|---|
| `driver.execute_script("return document.title")` | `page.evaluate("document.title")` |
| `driver.execute_script("arguments[0].click()", el)` | `page.locator(sel).evaluate("el => el.click()")` |
| `driver.execute_script("arguments[0].scrollIntoView(true)", el)` | `page.locator(sel).scroll_into_view_if_needed()` |

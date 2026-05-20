# Common Pattern Conversions

Recurring Selenium patterns in enterprise Selenium pytest suites and their Playwright replacements.

## `time.sleep` Elimination

The codebase has widespread `time.sleep` usage. Playwright's auto-waiting eliminates almost all of them.

### Rule: Remove unless it's for a non-UI delay

| Context | Action |
|---|---|
| Before a click/fill/assert | **Remove** — Playwright auto-waits |
| After a click, waiting for page to settle | **Remove** — use `page.wait_for_load_state()` if needed |
| In a polling loop for element state | **Replace** with `locator.wait_for()` or `expect()` |
| Between API calls (non-browser) | **Keep** — not a UI wait |
| Waiting for animation/transition | **Replace** with `expect(loc).to_have_css(...)` |

### Examples from this codebase

```python
# Before — sleep before clicking OK button after date selection
choice(available_dates[:-1]).click()
time.sleep(ONE_SEC_TIMEOUT)
if self.is_element_visible(self.OK_BUTTON_CSS, timeout=ONE_SEC_TIMEOUT):
    self.click_with_wait(self.OK_BUTTON_CSS)
    time.sleep(ONE_SEC_TIMEOUT)
self.wait_until_all_loaders_stop_running()

# After — Playwright auto-waits for clickability
available_dates = self._locator(self.AVAILABLE_DATES_CSS).all()
choice(available_dates[:-1]).click()
ok_button = self.page.locator(self.OK_BUTTON_CSS)
if ok_button.is_visible(timeout=1000):
    ok_button.click()
self.wait_until_all_loaders_stop_running()
```

```python
# Before — sleep in remediation modal flow
def click_on_remediation_modal(self):
    self.wait_until_modal_is_loaded(self.REMEDIATION_MODAL_CSS)
    time.sleep(ONE_SEC_TIMEOUT)
    self.click_with_wait(self.REMEDIATION_MODAL_SUBMIT_CSS)

# After
def click_on_remediation_modal(self):
    self.wait_until_modal_is_loaded(self.REMEDIATION_MODAL_CSS)
    self.page.locator(self.REMEDIATION_MODAL_SUBMIT_CSS).click()
```

```python
# Before — sleep in toast message wait
def wait_for_toast_messages(self):
    try:
        self._wait_for_element_be_visible(self.REQUEST_INFO, timeout=TWENTY_SEC_TIMEOUT)
        self.wait_until_element_invisible(self.REQUEST_INFO)
        time.sleep(TWO_SEC_TIMEOUT)
    except TimeoutException:
        return

# After
def wait_for_toast_messages(self):
    try:
        toast = self.page.locator(self.REQUEST_INFO)
        toast.wait_for(state="visible", timeout=20000)
        toast.wait_for(state="hidden")
    except Exception:
        return
```

## `WebDriverWait` + `expected_conditions` Elimination

Remove all `WebDriverWait`/`ec` patterns. Playwright's locator API handles waiting internally.

### Pattern: Wait-then-act

```python
# Before
element = WebDriverWait(self.webdriver, timeout).until(
    ec.visibility_of_element_located((By.CSS_SELECTOR, selector)))
element.click()

# After
self.page.locator(selector).click()
```

### Pattern: Wait-then-return

```python
# Before
WebDriverWait(self.webdriver, timeout).until(
    ec.visibility_of_element_located((find_by, selector)))
return self.webdriver.init_web_element(selector)

# After
return self.page.locator(selector)
```

### Pattern: Wait for invisibility

```python
# Before
WebDriverWait(self.webdriver, timeout).until(
    ec.invisibility_of_element_located((find_by, selector)))

# After
self.page.locator(selector).wait_for(state="hidden", timeout=timeout_ms)
```

## `tenacity` Retry Elimination

The codebase uses `tenacity.retry` for flaky waits. Playwright's built-in retry mechanism replaces this.

```python
# Before
@retry(wait=wait_fixed(2), stop=stop_after_attempt(5), retry=retry_if_exception_type())
def wait_for_element_with_retry(self, selector, find_by=By.CSS_SELECTOR, timeout=FIFTEEN_SEC_TIMEOUT):
    WebDriverWait(self.webdriver, timeout).until(
        ec.visibility_of_element_located((find_by, selector)))

# After — Playwright retries internally with auto-waiting
def wait_for_element_with_retry(self, selector, find_by="css", timeout=15000):
    self._locator(selector, find_by).wait_for(state="visible", timeout=timeout)
```

Keep `tenacity` only for non-browser retries (API calls, AWS operations).

## `ActionChains` Replacement

### Hover

```python
# Before
element_to_hover = self.webdriver.find_element(By.XPATH, selector)
hover = ActionChains(self.webdriver).move_to_element(element_to_hover)
hover.perform()

# After
self.page.locator(f"xpath={selector}").hover()
```

### Drag and drop

```python
# Before
source = self.webdriver.find_element(By.CSS_SELECTOR, source_sel)
target = self.webdriver.find_element(By.CSS_SELECTOR, target_sel)
ActionChains(self.webdriver).drag_and_drop(source, target).perform()

# After
self.page.locator(source_sel).drag_to(self.page.locator(target_sel))
```

### Key combos

```python
# Before
element.send_keys(Keys.COMMAND + 'a')
element.send_keys(Keys.BACKSPACE)

# After
self.page.locator(selector).press("Meta+a")
self.page.locator(selector).press("Backspace")
```

## `execute_script` Replacement

### Scroll into view

```python
# Before
self.webdriver.execute_script("arguments[0].scrollIntoView(true);", element)

# After
self.page.locator(selector).scroll_into_view_if_needed()
```

### Force click (JS click)

```python
# Before
self.webdriver.execute_script("arguments[0].click();", element)

# After — option 1: Playwright force click
self.page.locator(selector).click(force=True)

# After — option 2: dispatch event (matches JS behavior exactly)
self.page.locator(selector).dispatch_event("click")
```

### Get computed style

```python
# Before
opacity = float(elem.value_of_css_property('opacity'))

# After
opacity = float(self.page.locator(selector).evaluate("el => getComputedStyle(el).opacity"))
```

### Open new tab

```python
# Before
self.webdriver.execute_script(f"window.open('{url}', '_blank');")

# After
new_page = self.page.context.new_page()
new_page.goto(url)
```

## Custom Polling Loops

The codebase has manual polling loops (modal opacity, drawer position). Replace with `expect` assertions.

### Modal opacity polling

```python
# Before
time.sleep(ONE_SEC_TIMEOUT)
timer = 0
while timer <= FIFTEEN_SEC_TIMEOUT:
    elem = self.webdriver.find_element(find_by, selector)
    opacity = float(elem.value_of_css_property('opacity'))
    if opacity == 1.0:
        time.sleep(TWO_SEC_TIMEOUT)
        break
    else:
        time.sleep(ONE_SEC_TIMEOUT)
        timer += ONE_SEC_TIMEOUT

# After
loc = self.page.locator(selector)
loc.wait_for(state="visible")
expect(loc).to_have_css("opacity", "1", timeout=15000)
```

### Drawer animation polling

```python
# Before
timer = 0
while timer <= FIFTEEN_SEC_TIMEOUT:
    elem = self.webdriver.find_element(By.CSS_SELECTOR, self.DRAWER_ANIMATION_CSS)
    if elem.value_of_css_property('right') == '0px':
        break
    time.sleep(ONE_SEC_TIMEOUT)
    timer += ONE_SEC_TIMEOUT

# After
expect(self.page.locator(self.DRAWER_ANIMATION_CSS)).to_have_css("right", "0px", timeout=15000)
```

## Tab/Window Handling

Playwright uses `BrowserContext` to manage pages (tabs).

```python
# Before — Selenium window handles
self.webdriver.execute_script(f"window.open('{url}', '_blank');")
self.webdriver.switch_to.window(self.webdriver.window_handles[1])
# ... do work ...
self.webdriver.close()
self.webdriver.switch_to.window(self.webdriver.window_handles[0])

# After — Playwright context pages
new_page = self.page.context.new_page()
new_page.goto(url)
# ... do work on new_page ...
new_page.close()
# original self.page is still active, no switching needed
```

## Timeout Constants

Convert seconds to milliseconds. Playwright uses milliseconds everywhere.

| Constant | Selenium (seconds) | Playwright (milliseconds) |
|---|---|---|
| `ONE_SEC_TIMEOUT` | 1 | 1000 |
| `TWO_SEC_TIMEOUT` | 2 | 2000 |
| `THREE_SEC_TIMEOUT` | 3 | 3000 |
| `FIVE_SEC_TIMEOUT` | 5 | 5000 |
| `SEVEN_SEC_TIMEOUT` | 7 | 7000 |
| `TEN_SEC_TIMEOUT` | 10 | 10000 |
| `FIFTEEN_SEC_TIMEOUT` | 15 | 15000 |
| `TWENTY_SEC_TIMEOUT` | 20 | 20000 |

When converting, either:
- Multiply inline: `timeout=FIVE_SEC_TIMEOUT * 1000`
- Update the constants file to use milliseconds
- Use Playwright's default 30s timeout and only override when needed

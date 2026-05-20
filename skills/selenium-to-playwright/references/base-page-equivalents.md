# BasePage Method Equivalents

Every method in `tests/application/base_page.py` and its Playwright replacement.

In the converted codebase, `BasePage` is replaced by passing Playwright's `page: Page` object directly to page objects. Page objects store `self.page` instead of `self.webdriver`.

## Constructor

### Before

```python
class BasePage:
    def __init__(self):
        self.webdriver = DriverWrapper

class ConfigurationPage(BasePage):
    def __init__(self, webdriver):
        super().__init__()
        self.webdriver = webdriver
```

### After

```python
class BasePage:
    def __init__(self, page: Page):
        self.page = page

class ConfigurationPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
```

## Method-by-Method Conversion

### Element retrieval

#### `return_element_with_wait(selector, find_by, timeout)`

```python
# Before
def return_element_with_wait(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    WebDriverWait(self.webdriver, timeout).until(ec.visibility_of_element_located((find_by, selector)))
    return self.webdriver.init_web_element(selector)

# After
def return_element(self, selector, find_by="css"):
    return self._locator(selector, find_by)

def _locator(self, selector, find_by="css"):
    if find_by == "xpath":
        return self.page.locator(f"xpath={selector}")
    return self.page.locator(selector)
```

#### `return_all_elements_with_wait(selector, find_by, timeout)`

```python
# Before
def return_all_elements_with_wait(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    WebDriverWait(self.webdriver, timeout).until(ec.visibility_of_element_located((find_by, selector)))
    return self.webdriver.init_all_web_elements(selector)

# After
def return_all_elements(self, selector, find_by="css"):
    return self._locator(selector, find_by).all()
```

### Click methods

#### `click_with_wait(selector, find_by, timeout)`

```python
# Before
def click_with_wait(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    try:
        element = WebDriverWait(self.webdriver, timeout).until(
            ec.visibility_of_element_located((find_by, selector)))
        element.click()
    except Exception:
        element = self.webdriver.find_element(find_by, selector)
        self.webdriver.execute_script("arguments[0].click();", element)

# After
def click_with_wait(self, selector, find_by="css", timeout=20000):
    self._locator(selector, find_by).click(timeout=timeout)
```

#### `click_from_dom(selector, find_by, timeout)`

```python
# Before — JS click to avoid click-intercept
def click_from_dom(self, selector, find_by=By.CSS_SELECTOR, timeout=TEN_SEC_TIMEOUT):
    element = WebDriverWait(self.webdriver, timeout).until(ec.element_to_be_clickable((find_by, selector)))
    self.webdriver.execute_script("arguments[0].click();", element)

# After
def click_from_dom(self, selector, find_by="css"):
    self._locator(selector, find_by).dispatch_event("click")
```

#### `click_from_console(selector, find_by)`

```python
# Before
def click_from_console(self, selector, find_by=By.CSS_SELECTOR):
    element = self.webdriver.find_element(find_by, selector)
    self.webdriver.execute_script("arguments[0].click();", element)

# After
def click_from_console(self, selector, find_by="css"):
    self._locator(selector, find_by).dispatch_event("click")
```

#### `click_parent_with_wait(selector, find_by, timeout)`

```python
# Before
def click_parent_with_wait(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    element = WebDriverWait(self.webdriver, timeout).until(
        ec.element_to_be_clickable((find_by, selector))).find_element_by_xpath("..")
    element.click()

# After
def click_parent_with_wait(self, selector, find_by="css"):
    self._locator(selector, find_by).locator("xpath=..").click()
```

### Visibility checks

#### `is_element_visible(selector, find_by, timeout)`

```python
# Before
def is_element_visible(self, selector, find_by=By.CSS_SELECTOR, timeout=FIVE_SEC_TIMEOUT):
    try:
        self._wait_for_element_be_visible(find_by=find_by, selector=selector, timeout=timeout)
        return True
    except TimeoutException:
        return False

# After
def is_element_visible(self, selector, find_by="css", timeout=5000):
    return self._locator(selector, find_by).is_visible(timeout=timeout)
```

#### `is_element_invisible(selector, find_by, timeout)`

```python
# Before
def is_element_invisible(self, selector, find_by=By.XPATH, timeout=TEN_SEC_TIMEOUT):
    try:
        WebDriverWait(self.webdriver, timeout).until(ec.invisibility_of_element((find_by, selector)))
        return True
    except TimeoutException:
        return False

# After
def is_element_invisible(self, selector, find_by="css", timeout=10000):
    return self._locator(selector, find_by).is_hidden(timeout=timeout)
```

#### `_wait_for_element_be_visible(selector, find_by, timeout)`

```python
# Before
def _wait_for_element_be_visible(self, selector, find_by=By.CSS_SELECTOR, timeout=TEN_SEC_TIMEOUT):
    WebDriverWait(self.webdriver, timeout).until(ec.visibility_of_element_located((find_by, selector)))

# After
def _wait_for_element_be_visible(self, selector, find_by="css", timeout=10000):
    self._locator(selector, find_by).wait_for(state="visible", timeout=timeout)
```

#### `wait_for_element_with_retry(selector, find_by, timeout)` (tenacity)

```python
# Before
@retry(wait=wait_fixed(2), stop=stop_after_attempt(5), retry=retry_if_exception_type())
def wait_for_element_with_retry(self, selector, find_by=By.CSS_SELECTOR, timeout=FIFTEEN_SEC_TIMEOUT):
    WebDriverWait(self.webdriver, timeout).until(ec.visibility_of_element_located((find_by, selector)))

# After — tenacity retry is no longer needed; Playwright retries internally
def wait_for_element_with_retry(self, selector, find_by="css", timeout=15000):
    self._locator(selector, find_by).wait_for(state="visible", timeout=timeout)
```

### Wait / invisibility methods

#### `wait_until_element_invisible(selector, find_by, timeout)`

```python
# Before
def wait_until_element_invisible(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    try:
        WebDriverWait(self.webdriver, timeout).until(ec.invisibility_of_element_located((find_by, selector)))
    except TimeoutException:
        pass

# After
def wait_until_element_invisible(self, selector, find_by="css", timeout=20000):
    try:
        self._locator(selector, find_by).wait_for(state="hidden", timeout=timeout)
    except Exception:
        pass
```

#### `wait_until_spinner_stop_running()`

```python
# Before
def wait_until_spinner_stop_running(self):
    self.wait_until_element_invisible(self.PAGE_LOADER_CSS, timeout=TEN_SEC_TIMEOUT)

# After — identical structure, calls converted method
def wait_until_spinner_stop_running(self):
    self.wait_until_element_invisible(self.PAGE_LOADER_CSS, timeout=10000)
```

#### `wait_until_all_loaders_stop_running()`

No change needed — it calls the other converted wait methods.

#### `wait_until_modal_is_loaded(selector, find_by)`

```python
# Before — polls CSS opacity with time.sleep loop
def wait_until_modal_is_loaded(self, selector, find_by=By.CSS_SELECTOR):
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
def wait_until_modal_is_loaded(self, selector, find_by="css"):
    loc = self._locator(selector, find_by)
    loc.wait_for(state="visible")
    expect(loc).to_have_css("opacity", "1", timeout=15000)
```

#### `wait_for_drawer()`

```python
# Before — polls CSS right property
def wait_for_drawer(self):
    time.sleep(ONE_SEC_TIMEOUT)
    timer = 0
    while timer <= FIFTEEN_SEC_TIMEOUT:
        elem = self.webdriver.find_element(By.CSS_SELECTOR, self.DRAWER_ANIMATION_CSS)
        drawer = elem.value_of_css_property('right')
        if drawer == '0px':
            break
        else:
            time.sleep(ONE_SEC_TIMEOUT)
            timer += ONE_SEC_TIMEOUT

# After
def wait_for_drawer(self):
    expect(self.page.locator(self.DRAWER_ANIMATION_CSS)).to_have_css("right", "0px", timeout=15000)
```

### Text methods

#### `get_text_from_element(selector, find_by, timeout)`

```python
# Before
def get_text_from_element(self, selector, find_by=By.CSS_SELECTOR, timeout=TWENTY_SEC_TIMEOUT):
    return WebDriverWait(self.webdriver, timeout).until(
        ec.visibility_of_element_located((find_by, selector))).text

# After
def get_text_from_element(self, selector, find_by="css", timeout=20000):
    loc = self._locator(selector, find_by)
    loc.wait_for(state="visible", timeout=timeout)
    return loc.text_content()
```

#### `get_hover_text(locator)`

```python
# Before
def get_hover_text(self, locator):
    return self.webdriver.find_element_by_css_selector(locator).text

# After
def get_hover_text(self, locator):
    return self.page.locator(locator).text_content()
```

#### `wait_for_text(text, selector, find_by, time_limit)`

```python
# Before — manual polling loop
def wait_for_text(self, text, selector, find_by=By.CSS_SELECTOR, time_limit=FIFTEEN_SEC_TIMEOUT):
    expected_text = False
    timer = 0
    while expected_text is False:
        try:
            if timer > time_limit:
                break
            assert text in self.get_text_from_element(selector, find_by)
            expected_text = True
        except AssertionError:
            time.sleep(ONE_SEC_TIMEOUT)
            timer += ONE_SEC_TIMEOUT

# After
def wait_for_text(self, text, selector, find_by="css", time_limit=15000):
    expect(self._locator(selector, find_by)).to_contain_text(text, timeout=time_limit)
```

#### `wait_for_text_to_be_present(locator, expected_text, timeout)`

```python
# Before
def wait_for_text_to_be_present(self, locator, expected_text, timeout=10):
    try:
        WebDriverWait(self.webdriver, timeout).until(ec.text_to_be_present_in_element(locator, expected_text))
        return True
    except TimeoutException:
        return False

# After
def wait_for_text_to_be_present(self, selector, expected_text, find_by="css", timeout=10000):
    try:
        expect(self._locator(selector, find_by)).to_contain_text(expected_text, timeout=timeout)
        return True
    except AssertionError:
        return False
```

### Input methods

#### `input_text(selector, text)`

```python
# Before
def input_text(self, selector, text):
    self.webdriver.init_web_element(selector).set_text_value(text)

# After
def input_text(self, selector, text):
    self.page.locator(selector).fill(text)
```

#### `clear_text_input(selector, find_by)`

```python
# Before
def clear_text_input(self, selector, find_by=By.CSS_SELECTOR):
    element = self.webdriver.find_element(find_by, selector)
    element.clear()

# After
def clear_text_input(self, selector, find_by="css"):
    self._locator(selector, find_by).clear()
```

#### `clear_and_input_text(selector, text, find_by, timeout)`

```python
# Before — complex clear with platform detection and fallback
def clear_and_input_text(self, selector, text, find_by=By.CSS_SELECTOR, timeout=10):
    ctrl_or_cmd = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
    element = WebDriverWait(self.webdriver, timeout).until(ec.element_to_be_clickable((find_by, selector)))
    self.clear_text_input(selector, find_by)
    if element.get_attribute("value"):
        element.send_keys(ctrl_or_cmd + 'a')
        element.send_keys(Keys.BACKSPACE)
    element.send_keys(text)

# After
def clear_and_input_text(self, selector, text, find_by="css"):
    self._locator(selector, find_by).fill(text)
```

### Attribute methods

#### `get_value_from_attribute(selector, attribute, timeout, find_by)`

```python
# Before
def get_value_from_attribute(self, selector, attribute, timeout=TWENTY_SEC_TIMEOUT, find_by=By.XPATH):
    element = WebDriverWait(self.webdriver, timeout).until(ec.element_to_be_clickable((find_by, selector)))
    return element.get_attribute(attribute)

# After
def get_value_from_attribute(self, selector, attribute, find_by="xpath"):
    return self._locator(selector, find_by).get_attribute(attribute)
```

### Checkbox methods

#### `select_checkbox(checkbox, element, find_by, timeout)`

```python
# Before
def select_checkbox(self, checkbox, element, find_by=By.XPATH, timeout=TWENTY_SEC_TIMEOUT):
    checked = WebDriverWait(self.webdriver, timeout).until(
        ec.element_to_be_clickable((find_by, checkbox))).is_selected()
    if not checked:
        self.click_with_wait(element, find_by=find_by)

# After
def select_checkbox(self, selector, find_by="xpath"):
    self._locator(selector, find_by).set_checked(True)
```

#### `unselect_checkbox(checkbox, element, find_by, timeout)`

```python
# After
def unselect_checkbox(self, selector, find_by="xpath"):
    self._locator(selector, find_by).set_checked(False)
```

#### `is_checkbox_selected(selector, find_by)`

```python
# Before
def is_checkbox_selected(self, selector, find_by=By.XPATH):
    checkbox = self.webdriver.find_element(find_by, selector)
    if ('checked' or 'checkbox--indeterminate') in checkbox.get_attribute('class') or checkbox.is_selected():
        return True
    return False

# After
def is_checkbox_selected(self, selector, find_by="xpath"):
    loc = self._locator(selector, find_by)
    classes = loc.get_attribute("class") or ""
    return "checked" in classes or "checkbox--indeterminate" in classes or loc.is_checked()
```

### Hover and scroll

#### `hover_over_on_element(selector, find_by)`

```python
# Before
def hover_over_on_element(self, selector, find_by=By.XPATH):
    element_to_hover = self.webdriver.find_element(find_by, selector)
    hover = ActionChains(self.webdriver).move_to_element(element_to_hover)
    hover.perform()

# After
def hover_over_on_element(self, selector, find_by="xpath"):
    self._locator(selector, find_by).hover()
```

#### `mouse_over_on_element(selector, find_by)`

```python
# Before — dispatches JS mouseover events
def mouse_over_on_element(self, selector, find_by=By.CSS_SELECTOR):
    element = self.webdriver.find_element(find_by, selector)
    self.webdriver.execute_script("""...""", element)

# After
def mouse_over_on_element(self, selector, find_by="css"):
    self._locator(selector, find_by).hover()
```

#### `scroll_until_element_visible(selector, align_to_top, find_by)`

```python
# Before
def scroll_until_element_visible(self, selector, align_to_top='true', find_by=By.XPATH):
    target_element = self.webdriver.find_element(find_by, selector)
    self.webdriver.execute_script(f"arguments[0].scrollIntoView({align_to_top});", target_element)

# After
def scroll_until_element_visible(self, selector, find_by="xpath"):
    self._locator(selector, find_by).scroll_into_view_if_needed()
```

### Navigation

#### `navigate_to_url(url)`

```python
# Before
def navigate_to_url(self, url):
    self.webdriver.get(url)

# After
def navigate_to_url(self, url):
    self.page.goto(url)
```

#### `get_page_title()`

```python
# After
def get_page_title(self):
    return self.page.title()
```

#### `open_url_in_new_tab(url)` and `switch_on_second_tab()`

```python
# Before
def open_url_in_new_tab(self, url):
    self.webdriver.execute_script(f"window.open('{url}', '_blank');")
    self.switch_on_second_tab()

def switch_on_second_tab(self):
    self.webdriver.switch_to.window(self.webdriver.window_handles[1])

# After — Playwright tracks pages per browser context
def open_url_in_new_tab(self, url):
    new_page = self.page.context.new_page()
    new_page.goto(url)
    return new_page
```

#### `close_browser()`

```python
# After
def close_browser(self):
    self.page.close()
```

### Toggle

#### `switch_toggle_to_value(selector, value, find_by)`

```python
# Before
def switch_toggle_to_value(self, selector, value="Off", find_by=By.CSS_SELECTOR):
    self.wait_until_spinner_stop_running()
    if value == "Off" and self.get_text_from_element(selector, find_by=find_by) == "On":
        self.click_with_wait(selector, find_by=find_by)
    elif value == "On" and self.get_text_from_element(selector, find_by=find_by) == "Off":
        self.click_with_wait(selector, find_by=find_by)

# After — same logic, calls converted methods
def switch_toggle_to_value(self, selector, value="Off", find_by="css"):
    self.wait_until_spinner_stop_running()
    current = self.get_text_from_element(selector, find_by=find_by)
    if current != value:
        self.click_with_wait(selector, find_by=find_by)
```

### Button waits

#### `wait_until_button_is_clickable(selector, find_by, timeout)`

```python
# Before
def wait_until_button_is_clickable(self, selector, find_by=By.CSS_SELECTOR, timeout=TEN_SEC_TIMEOUT):
    return WebDriverWait(self.webdriver, timeout).until(ec.element_to_be_clickable((find_by, selector)))

# After
def wait_until_button_is_clickable(self, selector, find_by="css", timeout=10000):
    loc = self._locator(selector, find_by)
    expect(loc).to_be_enabled(timeout=timeout)
    return loc
```

### Clipboard

#### `click_and_save_value_from_clipboard(selector, find_by)`

```python
# Before
def click_and_save_value_from_clipboard(self, selector, find_by=By.CSS_SELECTOR):
    self.click_with_wait(selector, find_by=find_by)
    return pyperclip.paste()

# After — clipboard via Playwright's built-in
def click_and_save_value_from_clipboard(self, selector, find_by="css"):
    self.click_with_wait(selector, find_by=find_by)
    return self.page.evaluate("navigator.clipboard.readText()")
```

### Remediation/toast helpers

#### `wait_for_toast_messages()`

```python
# Before
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

## DriverWrapper Methods

`DriverWrapper` extends `legacy driver wrapper`'s `SeWebDriver`. Its custom method:

#### `click_wth_scroll(web_element, timeout)`

```python
# Before
def click_wth_scroll(self, web_element, timeout=10):
    self.webdriver.execute_script("arguments[0].scrollIntoView(true);", web_element)
    WebDriverWait(self.webdriver, timeout, POLL_FREQUENCY).until(lambda d: web_element.is_enabled())
    web_element.click()

# After — not needed as a separate method; Playwright auto-scrolls before click
# Replace call sites with:
page.locator(selector).click()
```

# Fixture Model Conversion

How to convert the enterprise Selenium pytest suites Selenium fixture chain to pytest-playwright.

## Current Fixture Chain (Selenium)

```
pytest_addoption (CLI flags)
    └─> env_consts (EnvConsts from CLI)
    └─> session (Session with browser_type)
            └─> app (Application with DriverWrapper + EnvConsts)
                    └─> teardown: screenshot + logs + session_end
```

### Current `session` fixture

```python
@pytest.fixture()
def session(request):
    browser_type = request.config.getoption("--browser")
    return Session(browser_type)
```

`Session.start_driver()` creates a raw Selenium `webdriver.Chrome`/`Firefox`, wraps it in `DriverWrapper(SeWebDriver)`, and returns it.

### Current `app` fixture

```python
@pytest.fixture()
def app(request, session, env_consts):
    env_vars = env_consts
    application = Application(session.start_driver(), env_vars)

    def teardown():
        try:
            if request.node.rep_call.failed:
                _save_screenshot(application.webdriver, ...)
                _allure_save_screenshot(application.webdriver)
                logs = application.webdriver.get_log("performance")
                ...
        finally:
            session.session_end()

    request.addfinalizer(teardown)
    return application
```

### Current `env_consts` fixture

```python
@pytest.fixture()
def env_consts(request):
    source = request.config.getoption("--source")
    env = request.config.getoption("--env")
    user_role = request.config.getoption("--role")
    app_uri = request.config.getoption("--uri")
    appversion = request.config.getoption("--appversion")
    return EnvConsts(source, env, user_role, app_uri, appversion)
```

## Converted Fixture Chain (Playwright)

```
pytest_addoption (CLI flags — keep as-is)
    └─> env_consts (EnvConsts from CLI — keep as-is)
    └─> browser_context_args (viewport, tracing config)
    └─> page (provided by pytest-playwright)
            └─> app (Application with page + EnvConsts)
                    └─> teardown: Playwright handles tracing/screenshots
```

### Removed: `Session` class

Not needed. Playwright manages browsers via `pytest-playwright` fixtures: `browser`, `context`, `page`.

### Removed: `DriverWrapper` class

Not needed. Playwright's `Page` object replasecondary all `legacy driver wrapper` and `DriverWrapper` functionality.

### Converted `conftest.py`

```python
import pytest
from tests.application.application import Application
from tests.constants.environment import EnvConsts


def pytest_addoption(parser):
    """CLI options — unchanged."""
    parser.addoption("--source", action="store", default="primary",
                     help="Message source: primary, secondary, inline")
    parser.addoption("--env", action="store", default="integration",
                     help="Environment: qa, integration, prod_va, prod_fra")
    parser.addoption("--browser", action="store", default="chromium",
                     help="Browser: chromium, firefox, webkit")
    parser.addoption("--role", action="store", default="superadmin",
                     help="User role")
    parser.addoption("--uri", action="store", default=None,
                     help="UI PR Gating job URL")
    parser.addoption("--skipRules", action="store", default=False,
                     help="Skip message rule fixture creation")
    parser.addoption("--appversion", action="store", default=None,
                     help="Verify App version from console logs")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1750, "height": 1080},
    }


@pytest.fixture()
def env_consts(request):
    """Unchanged from Selenium version."""
    return EnvConsts(
        request.config.getoption("--source"),
        request.config.getoption("--env"),
        request.config.getoption("--role"),
        request.config.getoption("--uri"),
        request.config.getoption("--appversion"),
    )


@pytest.fixture()
def app(page, env_consts):
    """Application fixture — Playwright manages browser lifecycle."""
    application = Application(page, env_consts)
    yield application
```

### Failure artifacts with Playwright

Playwright captures screenshots, trasecondary, and videos automatically via `conftest.py` or `pytest.ini` / `pyproject.toml`:

```ini
# pyproject.toml
[tool.pytest.ini_options]
# Playwright options
playwright_screenshot = "only-on-failure"
playwright_video = "retain-on-failure"
playwright_tracing = "retain-on-failure"
```

This replasecondary the manual `_save_screenshot`, `_allure_save_screenshot`, and performance log capture in the current teardown.

### Allure integration

Allure still works with `pytest-playwright`. Screenshots from Playwright failures can be attached via a pytest hook:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            import allure
            allure.attach(
                page.screenshot(),
                name="failure-screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
```

## `Application` Class Changes

### Before

```python
class Application(BasePage):
    def __init__(self, webdriver, env_consts):
        super().__init__()
        self.webdriver = webdriver
        self.env_configs = env_consts
```

### After

```python
class Application(BasePage):
    def __init__(self, page: Page, env_consts):
        super().__init__(page)
        self.env_configs = env_consts
```

Page factory methods stay the same structurally but pass `self.page` instead of `self.webdriver`:

```python
# Before
def get_messages_page(self):
    return MessagesPage(self.webdriver)

# After
def get_messages_page(self):
    return MessagesPage(self.page)
```

## Browser Selection

### Before (Selenium)

`--browser chrome` or `--browser mozilla`, handled by `Session._get_chrome_driver()` / `Session._get_mozilla_driver()`.

### After (Playwright)

`--browser chromium`, `--browser firefox`, or `--browser webkit`. Handled by pytest-playwright natively:

```bash
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit
```

## Session-Scoped API Fixtures

Fixtures that use `ApiClient` for setup/teardown (message rules, policy exceptions, etc.) do NOT interact with the browser. They require no conversion — keep them exactly as they are:

```python
@pytest.fixture(scope='session', autouse=True)
def create_VO_message_rules(request, env_consts):
    """API-only fixture — no browser interaction, no conversion needed."""
    ...
```

## xdist Compatibility

`pytest-xdist` works identically with `pytest-playwright`. The `xdist_group` markers and `gw0`/`gw1` branching logic in session-scoped fixtures remain unchanged.

## CLI Invocation

### Before

```bash
pytest tests/functional/ --source=primary --env=integration --browser=chrome -n 4
```

### After

```bash
pytest tests/functional/ --source=primary --env=integration --browser=chromium -n 4
```

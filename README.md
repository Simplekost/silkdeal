# SILKDEAL — README

A Scrapy project with two Selenium-enabled spiders:

* `compt_deal` — scrapes Slickdeals Computer Deals and paginates by clicking the **Next** button. (file: `silkdeal/spiders/compt_deal.py`)
* `silkdeal_spy` — development spider used when working on stealthing and driver issues (DuckDuckGo). (file: `silkdeal/spiders/silkdeal_spy.py`)

This README documents how to install, run, and reproduce the environment used in this repository, and it documents the Selenium 4 compatibility fix you applied (the `executable_path` → `Service` change) including where to patch the `scrapy-selenium` middleware.

---

## Table of contents

* [Requirements](#requirements)
* [Install](#install)
* [Repository layout (relevant files)](#repository-layout-relevant-files)
* [Chromedriver — placement & version](#chromedriver---placement--version)
* \[Selenium 4 compatibility: patching `scrapy_selenium/middlewares.py`]\(#selenium-4-compatibility-patching-scrapy\_seleniummiddlewaresp y)
* [Recommended `settings.py` (what to set)](#recommended-settingspy-what-to-set)
* [Spiders (what runs)](#spiders-what-runs)
* [Run the spiders](#run-the-spiders)
* [Troubleshooting — common errors & fixes](#troubleshooting--common-errors--fixes)
* [Testing / CI suggestions](#testing--ci-suggestions)
* [License & contributions](#license--contributions)
* [Author notes (maintenance / choices you made)](#author-notes-maintenance--choices-you-made)

---

## Requirements

* Python 3.8+
* Google Chrome (installed locally)
* Matching ChromeDriver for your Chrome major version

Python packages:

* `scrapy`
* `scrapy-selenium`
* `selenium>=4`
* `selenium-stealth` (optional — used by `silkdeal_spy` via `get_stealth_driver()`)
* `webdriver-manager` (optional — recommended for CI / to avoid manual chromedriver updates)

---

## Install

Create and activate a virtual environment, then install packages:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install scrapy scrapy-selenium selenium selenium-stealth
# Optional: automatic chromedriver management
pip install webdriver-manager
```
## Repository layout 

```
SILKDEAL/
├─ silkdeal/
│  ├─ spiders/
│  │  ├─ compt_deal.py       # Slickdeals Computer Deals spider (Selenium)
│  │  └─ silkdeal_spy.py     # Development / stealth spider (Selenium)
│  ├─ middlewares.py        # (project file — may exist), but note: scrapy_selenium middleware was patched in site-packages
│  ├─ settings.py           # project settings & get_stealth_driver()
│  ├─ items.py
│  ├─ pipelines.py
│  └─ __init__.py
└─ scrapy.cfg             
```
## Chromedriver — placement & version

1. Check your Chrome browser version at `chrome://settings/help`. Note the major version (e.g., `116.x`).
2. Download the matching ChromeDriver for your platform. On Windows, name it `chromedriver.exe`.
3. Place the binary at one of:

   * Project root and set `SELENIUM_DRIVER_EXECUTABLE_PATH` to `os.path.join(os.getcwd(), "chromedriver.exe")` (used in this repo), or
   * An absolute path on disk (recommended for shared machines), or
   * Use `webdriver-manager` to handle install automatically (recommended for CI).

Example (Windows) path in `settings.py`:

```python
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), "chromedriver.exe")
SELENIUM_DRIVER_EXECUTABLE_PATH = CHROMEDRIVER_PATH
```

---

## Selenium 4 compatibility — patching `scrapy-selenium` middleware

**Problem:** Selenium 4 removed the `executable_path` argument from `WebDriver` constructors. Older `scrapy-selenium` middleware (or older usage) that calls `WebDriver(executable_path=...)` results in:

```
TypeError: WebDriver.__init__() got an unexpected keyword argument 'executable_path'
```

**Solution:** Patch `scrapy-selenium` middleware to use Selenium 4 style — create a `Service` object and pass it to the driver as `service=Service(...)`. Keep remote and fallback behavior for other drivers.

### Where to patch

Typical local paths where `scrapy_selenium` lives:

* Standard installation:

  ```
  C:\Users\<YOUR_USER>\AppData\Local\Programs\Python\Python311\Lib\site-packages\scrapy_selenium\middlewares.py
  ```
* Anaconda/miniconda:

  ```
  C:\Users\<YOUR_USER>\anaconda3\envs\<YOUR_ENV>\Lib\site-packages\scrapy_selenium\middlewares.py
  ```

Edit that `middlewares.py` (or maintain a patched fork of `scrapy-selenium`) and replace the driver initialization with the Selenium-4-compatible code.

### Example updated middleware (drop into `scrapy_selenium/middlewares.py` or in your fork)

```python
from importlib import import_module
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from .http import SeleniumRequest

class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path,
        browser_executable_path, command_executor, driver_arguments):
        """Initialize the selenium webdriver"""

        webdriver_base_path = f'selenium.webdriver.{driver_name}'
        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')
        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')
        driver_options = driver_options_klass()

        if browser_executable_path:
            driver_options.binary_location = browser_executable_path
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        # Chrome/Selenium 4.x style
        if driver_name and driver_name.lower() == 'chrome':
            service = Service(driver_executable_path)
            self.driver = driver_klass(service=service, options=driver_options)
        # Remote driver
        elif command_executor is not None:
            from selenium import webdriver
            capabilities = driver_options.to_capabilities()
            self.driver = webdriver.Remote(command_executor=command_executor,
                                           desired_capabilities=capabilities)
        # Other drivers (fallback to old style)
        else:
            driver_kwargs = {
                'executable_path': driver_executable_path,
                f'{driver_name}_options': driver_options
            }
            self.driver = driver_klass(**driver_kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        if (driver_name.lower() != 'chrome') and (driver_executable_path is None and command_executor is None):
            raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        if not isinstance(request, SeleniumRequest):
            return None

        self.driver.get(request.url)

        for cookie_name, cookie_value in request.cookies.items():
            self.driver.add_cookie({
                'name': cookie_name,
                'value': cookie_value
            })

        if request.wait_until:
            WebDriverWait(self.driver, request.wait_time).until(request.wait_until)

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        self.driver.quit()
```

Make a backup of the original `middlewares.py` before editing. Prefer maintaining a fork of `scrapy-selenium` and applying the patch in version control.

---

## Recommended `settings.py`

Add or confirm these keys in your project `silkdeal/settings.py`:

```python
import os

CHROMEDRIVER_PATH = os.path.join(os.getcwd(), "chromedriver.exe")  # or absolute path
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = CHROMEDRIVER_PATH
SELENIUM_DRIVER_ARGUMENTS = [
    '--start-maximized',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--disable-dev-shm-usage',
    '--no-sandbox'
]
DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800  # points to patched middleware in site-packages/fork
}
```

If you want to use `selenium-stealth` and want a stealth driver factory used in `silkdeal_spy`, it is included in `silkdeal/settings.py`:

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth

def get_stealth_driver(chromedriver_path=CHROMEDRIVER_PATH):
    options = webdriver.ChromeOptions()
    for arg in SELENIUM_DRIVER_ARGUMENTS:
        options.add_argument(arg)

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver
```

`silkdeal_spy.py` imports `get_stealth_driver` from `silkdeal.settings`.

---

## Spiders

Files are present in `silkdeal/spiders/`:

* `compt_deal.py` — Slickdeals Computer Deals spider (Selenium). It uses `SeleniumRequest` and `driver.page_source` to build a `Selector`. It paginates by clicking the Next button using explicit waits and staleness checks.
* `silkdeal_spy.py` — Dev spider that uses `get_stealth_driver()` and demonstrates stealth options, human-like delays, and screenshot saving. It also scrapes a subset of links from DuckDuckGo.

You can open these files in the `silkdeal/spiders/` directory to inspect the exact code.

---

## Run the spiders

From the repository root (where `scrapy.cfg` lives) run:

```bash
# Slickdeals
scrapy crawl compt_deal -o deals.json

# Dev / stealth spider
scrapy crawl silkdeal_spy -o duck_links.json
```

`deals.json` and `duck_links.json` will be created with scraped items.

---

## Troubleshooting — common errors & fixes

* **TypeError: `WebDriver.__init__()` got an unexpected keyword argument 'executable\_path'**

  * Cause: unpatched `scrapy-selenium` middleware or an older middleware still using `executable_path=`.
  * Fix: apply the middleware patch above (replace initialization with `Service(...)` pattern).

* **selenium.common.exceptions.NoSuchDriverException**

  * Cause: chromedriver not found or mismatched version.
  * Fix: Verify `CHROMEDRIVER_PATH` and chromedriver major version equals Chrome major version; or use `webdriver-manager`.

* **TypeError: a bytes-like object is required, not 'NoneType'** when writing screenshot

  * Cause: `response.meta.get('screenshot')` is `None`.
  * Fix: ensure `SeleniumRequest(..., screenshot=True)` and check `if img:` before writing, or call `driver.get_screenshot_as_png()` in middleware.

* **CAPTCHA / bot detection**

  * Use `selenium-stealth` (already wired into `get_stealth_driver()`), add randomized delays, avoid headless mode when debugging. Respect site terms.

* **Spider not discovered (`scrapy list`)**

  * Ensure spider files are in `silkdeal/spiders/` and class `name` is unique.

---

## Testing & CI suggestions

* Use `webdriver-manager` in CI to avoid committing somedriver binary and to auto-provision the correct driver. Example with `webdriver-manager`:

```python
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
```

* For CI smoke tests, run spiders against a controlled fixture or a staging endpoint rather than the live site. Use a short run and assert keys in the output JSON.

---

## License & contributing

This project is suitable for an MIT-style license.

Contributions: fork, create a branch, open a PR. 

---


 

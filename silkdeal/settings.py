# Scrapy settings for silkdeal project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "silkdeal"

SPIDER_MODULES = ["silkdeal.spiders"]
NEWSPIDER_MODULE = "silkdeal.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "silkdeal (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "silkdeal.middlewares.SilkdealSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "silkdeal.middlewares.SilkdealDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "silkdeal.pipelines.SilkdealPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

#Selenium#

# from selenium.webdriver.chrome.service import Service

# SELENIUM_DRIVER_NAME = 'chrome'
# SELENIUM_DRIVER_EXECUTABLE_PATH = 'chromedriver.exe'  

# # SELENIUM_DRIVER_ARGUMENTS = ["--headless=new"] 
# SELENIUM_DRIVER_ARGUMENTS = [
#     '--disable-blink-features=AutomationControlled',
#     '--start-maximized',
#     '--disable-infobars',
#     '--disable-dev-shm-usage',
#     '--no-sandbox'
# ]


# SELENIUM_DRIVER_SERVICE_ARGS = {
#     'service': Service(SELENIUM_DRIVER_EXECUTABLE_PATH)
# }

# DOWNLOADER_MIDDLEWARES = {
#     'scrapy_selenium.SeleniumMiddleware': 800
# }

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import os

# Path to ChromeDriver
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), "chromedriver.exe")  # or absolute path

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_ARGUMENTS = [
    '--start-maximized',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--disable-dev-shm-usage',
    '--no-sandbox'
]

DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800
}

def get_stealth_driver():
    options = webdriver.ChromeOptions()
    for arg in SELENIUM_DRIVER_ARGUMENTS:
        options.add_argument(arg)

    service = Service(executable_path=CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=options)

    # Apply stealth
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver

#     driver.execute_cdp_cmd('Network.setUserAgentOverride', {
#      "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
#  })

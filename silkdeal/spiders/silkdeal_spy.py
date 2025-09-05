import scrapy
import time
import random
from scrapy_selenium import SeleniumRequest
from scrapy.selector import Selector
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from silkdeal.settings import get_stealth_driver  # import from settings

class SilkdealSpySpider(scrapy.Spider):
    name = "silkdeal_spy"
    # allowed_domains = ["slickdeals.net"]
    # start_urls = ["https://slickdeals.net"]

    def start_requests(self):
        driver = get_stealth_driver()

        yield SeleniumRequest(
            url='https://duckduckgo.com',
            callback=self.parse,
            wait_time=10, 
            screenshot= True, 
            meta={'driver': driver}

            # wait_until=lambda driver: driver.find_element_by_id('searchbox_input')  
        )


    def parse(self, response):
        # img = response.meta.get('screenshot')

        # with open('screenshot.png', 'wb') as f:
        #     f.write(img)
        driver = response.meta.get('driver')

        #  # --- Stealth: remove webdriver flag ---
        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # # --- Fake plugins ---
        # driver.execute_script("""
        #     Object.defineProperty(navigator, 'plugins', {
        #         get: () => [{name: 'Chrome PDF Plugin'}, {name: 'Chrome PDF Viewer'}]
        #     });
        # """)

        # # --- Fake languages ---
        # driver.execute_script("""
        #     Object.defineProperty(navigator, 'languages', {
        #         get: () => ['en-US', 'en']
        #     });
        # """)

        # # --- Simulate human delay & scroll ---
        time.sleep(random.uniform(1.5, 3.0))
        actions = ActionChains(driver)
        actions.move_by_offset(20, 20).perform()
        driver.find_element("tag name", "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(random.uniform(0.5, 1.5))

        # --- Perform search ---

        search_box = driver.find_element("id", "searchbox_input")
        search_box.send_keys("hello world")

        time.sleep(random.uniform(0.5, 1.5))



        search_box.send_keys(Keys.ENTER)
        # search_box.submit()

        time.sleep(2)
        html = driver.page_source
        response_obj = Selector(text=html)


        links = response_obj.xpath('//div[@class="ikg2IXiCD14iVX7AdZo1"]/h2/a')
        for link in links:
            yield {
                'url': link.xpath('.//@href').get()
            }

        driver.save_screenshot('input_screenshot.png')
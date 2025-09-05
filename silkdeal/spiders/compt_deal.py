import scrapy
import time
import random
from scrapy_selenium import SeleniumRequest
from scrapy.selector import Selector
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Selenium wait helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ComptDealSpider(scrapy.Spider):
    name = "compt_deal"

    def start_requests(self):
        yield SeleniumRequest(
            url='https://slickdeals.net/computer-deals',
            callback=self.parse,
            wait_time=3,
            screenshot=True,
        )

    def parse(self, response):
        driver = response.meta.get('driver')
        wait = WebDriverWait(driver, 3)

        while True:
            # build a Selector from the current driver DOM
            sel = Selector(text=driver.page_source)

            products = sel.xpath('//ul[@class="bp-p-filterGrid_items"]/li')
            for product in products:
                yield {
                    'title': product.xpath('.//a[@class="bp-c-card_title bp-c-link"]/text()').get(),
                    'url': product.xpath('.//a[@class="bp-c-card_title bp-c-link"]/@href').get(),
                    'store': product.xpath('.//span[@class="bp-c-card_subtitle"]/text()').get(),
                    'price': product.xpath('.//span[@class="bp-p-dealCard_price"]/text()').get(),
                }

            # small human-like pause & scroll
            time.sleep(random.uniform(0.8, 1.5))
            actions = ActionChains(driver)
            actions.move_by_offset(20, 20).perform()
            driver.find_element("tag name", "body").send_keys(Keys.PAGE_DOWN)
            time.sleep(random.uniform(0.4, 1.0))

            # Try to find and click Next
            try:
                # optionally capture the first item element to wait for it to become stale after navigation
                try:
                    first_item = driver.find_element(By.XPATH, "//ul[@class='bp-p-filterGrid_items']/li[1]")
                except Exception:
                    first_item = None

                # wait until next button is clickable (try aria-label or data-page)
                next_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@aria-label='next' or @data-page='next']"))
                )

                # scroll into view and click
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
                time.sleep(random.uniform(0.3, 0.8))
                next_btn.click()

                # wait for old content to be replaced (staleness) OR wait for the new list to appear
                if first_item:
                    wait.until(EC.staleness_of(first_item))
                else:
                    # fallback: wait until at least one product appears in the new DOM
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//ul[@class='bp-p-filterGrid_items']/li")))

                # small delay to let rendering finish
                time.sleep(random.uniform(0.5, 1.2))

                # loop will re-run and scrape the new page (using driver.page_source)
            except Exception as e:
                # no next button / not clickable / timeout
                self.logger.info("No more pages or couldn't click next: %s", e)
                break

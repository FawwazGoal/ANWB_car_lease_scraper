import scrapy
from scrapy_playwright.page import PageMethod

class TestSpider(scrapy.Spider):
    name = 'test_spider'
    start_urls = ['https://quotes.toscrape.com/']  # Simple test site
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                },
                callback=self.parse
            )
    
    async def parse(self, response):
        # Get the page object
        try:
            page = response.meta["playwright_page"]
            self.logger.info("Page object successfully obtained!")
            
            # Get page title
            title = await page.title()
            self.logger.info(f"Page title: {title}")
            
            # Take screenshot
            await page.screenshot(path="test_screenshot.png")
            self.logger.info("Screenshot saved to test_screenshot.png")
            
            # Close the page
            await page.close()
            
            self.logger.info("Test completed successfully!")
        except KeyError as e:
            self.logger.error(f"KeyError: {e}")
        except Exception as e:
            self.logger.error(f"Error: {e}")
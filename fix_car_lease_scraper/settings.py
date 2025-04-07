# Scrapy settings for anwb_lease_scraper project

BOT_NAME = 'fix_car_lease_scraper'

SPIDER_MODULES = ['fix_car_lease_scraper.spiders']
NEWSPIDER_MODULE = 'fix_car_lease_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable cookies
COOKIES_ENABLED = True

# Set the log level
LOG_LEVEL = 'INFO'

# Enable and configure the Playwright integration
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': True,
    'timeout': 60000,
}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000

# Default User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Configure item pipelines
ITEM_PIPELINES = {
    'fix_car_lease_scraper.pipelines.ValidationPipeline': 300,
    'fix_car_lease_scraper.pipelines.LeaseOffersPipeline': 400,
}

# Enable item cache
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours

# Configure retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Additional settings for better crawling
DOWNLOAD_TIMEOUT = 180  # 3 minutes
FEED_EXPORT_ENCODING = 'utf-8'
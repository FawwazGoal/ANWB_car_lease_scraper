import scrapy
from scrapy_playwright.page import PageMethod
import os
import json

class SimpleANWBSpider(scrapy.Spider):
    name = 'anwb_simple'
    allowed_domains = ['anwb.nl']
    start_urls = ['https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod/aanbod=new']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': False,  # Set to False to see the browser
            'timeout': 60000,
        },
        'DOWNLOAD_DELAY': 2,
        'ROBOTSTXT_OBEY': True,
    }
    
    def start_requests(self):
        """Start requests with Playwright."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", "body", timeout=60000),
                    ],
                ),
                callback=self.parse
            )
    
    async def parse(self, response):
        """
        Explore the page structure and save useful information for debugging.
        """
        page = response.meta["playwright_page"]
        
        # Create directory for debug files
        os.makedirs("debug", exist_ok=True)
        
        # Save full page screenshot
        await page.screenshot(path="debug/full_page.png", full_page=True)
        
        # Save HTML content
        with open("debug/page_content.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Execute JavaScript to get all elements and their classes
        element_data = await page.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('*'));
            const filtered = elements.filter(el => {
                // Keep only elements that might be part of car listings
                return (el.tagName === 'A' && (
                    el.href.includes('/auto/private-lease/anwb-private-lease/aanbod/') || 
                    el.className.includes('card')
                )) || 
                (el.tagName === 'DIV' && (
                    el.className.includes('card') || 
                    el.className.includes('list') ||
                    el.className.includes('item')
                ));
            });
            
            return filtered.map(el => {
                const rect = el.getBoundingClientRect();
                
                // Try to find price-like content
                const priceElements = el.querySelectorAll('*[data-test*="price"], *[class*="price"]');
                const priceTexts = Array.from(priceElements).map(p => p.textContent.trim());
                
                // Try to find model/make-like content
                const titleElements = el.querySelectorAll('h1, h2, h3, h4, h5, *[class*="title"], *[class*="heading"]');
                const titleTexts = Array.from(titleElements).map(t => t.textContent.trim()).filter(Boolean);
                
                return {
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    href: el.href || null,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    visible: rect.width > 0 && rect.height > 0,
                    text: el.innerText?.slice(0, 100),
                    priceTexts,
                    titleTexts
                };
            });
        }""")
        
        # Save element data to JSON
        with open("debug/elements.json", "w", encoding="utf-8") as f:
            json.dump(element_data, f, indent=2, ensure_ascii=False)
        
        # Extract all links to car detail pages
        car_links = []
        for link in response.css('a::attr(href)').getall():
            if '/auto/private-lease/anwb-private-lease/aanbod/' in link and not link.endswith('aanbod=new'):
                car_links.append(response.urljoin(link))
        
        self.logger.info(f"Found {len(car_links)} potential car links")
        
        # Save list of car links
        with open("debug/car_links.json", "w", encoding="utf-8") as f:
            json.dump(car_links, f, indent=2)
        
        # Wait a moment to allow visual inspection (if headless=False)
        self.logger.info("Pausing for inspection...")
        await page.wait_for_timeout(5000)
        
        await page.close()
        
        self.logger.info("Debugging information has been saved to the 'debug' folder.")
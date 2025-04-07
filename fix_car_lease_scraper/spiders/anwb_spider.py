import scrapy
import json
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from fix_car_lease_scraper.items import LeaseOffer

class ANWBFullScraper(scrapy.Spider):
    name = 'anwb_lease'
    allowed_domains = ['anwb.nl']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 0.25,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, *args, **kwargs):
        super(ANWBFullScraper, self).__init__(*args, **kwargs)
        # Create output directories
        os.makedirs("output", exist_ok=True)
        os.makedirs("debug", exist_ok=True)
        
        # Setup Selenium
        chrome_options = Options()
        # Comment out headless mode to see the browser in action
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Install and setup Chrome driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Get all car URLs using Selenium - with extra effort to get ALL listings
        self.all_car_urls = self.get_all_car_urls()
        self.logger.info(f"Found {len(self.all_car_urls)} car URLs")
        
        # Stats tracking
        self.stats = {
            'car_links_found': len(self.all_car_urls),
            'cars_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0
        }
    
    def get_all_car_urls(self):
        """Use Selenium to load the page and click 'Load More' until all cars are shown"""
        car_urls = []
        main_url = "https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod/aanbod=new"
        
        try:
            self.logger.info("Starting Selenium browser to get all car URLs...")
            self.driver.get(main_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # Take a screenshot of the initial page
            self.driver.save_screenshot("debug/initial_page.png")
            
            # Find out how many cars in total (should be around 199)
            try:
                # Wait longer for the page to fully load
                time.sleep(5)
                total_text = self.driver.find_element(By.CSS_SELECTOR, '[data-test="results-count"]').text
                total_match = re.search(r'(\d+)', total_text)
                if total_match:
                    total_cars = int(total_match.group(1))
                    self.logger.info(f"Found total of {total_cars} cars to extract")
                else:
                    total_cars = 199  # Default if we can't extract the number
                    self.logger.info(f"Using default value of {total_cars} cars")
            except Exception as e:
                total_cars = 199  # Default
                self.logger.error(f"Error getting total cars: {str(e)}")
            
            # Calculate how many times to click "Load More"
            # Each click loads 15 more cars, and 15 are shown initially
            initial_count = 15
            clicks_needed = ((total_cars - initial_count) // 15) + 1
            
            # Add a safety buffer to make sure we get all listings
            clicks_needed += 2  # Add 2 more clicks just to be safe
            
            self.logger.info(f"Need to click 'Load More' approximately {clicks_needed} times")
            
            # Keep clicking "Load More" until we've loaded all cars or reached the maximum clicks
            clicks_done = 0
            max_attempts = 3  # Max attempts per click
            cars_shown = 0
            previous_count = 0
            
            while clicks_done < clicks_needed:
                try:
                    # Check how many cars are currently shown
                    car_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/auto/private-lease/anwb-private-lease/aanbod/"]')
                    cars_shown = len([e for e in car_elements if 'aanbod=new' not in e.get_attribute('href')])
                    
                    self.logger.info(f"Currently showing {cars_shown} cars after {clicks_done} clicks")
                    
                    # If we're not getting more cars after clicking, we might be at the end
                    if cars_shown == previous_count and clicks_done > 0:
                        self.logger.warning(f"No new cars loaded after click. Still at {cars_shown} cars.")
                        # Try one more time before giving up
                        if clicks_done > 2:  # If we've tried a few times already
                            break
                    
                    previous_count = cars_shown
                    
                    # Scroll to the bottom to make sure the button is visible
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for scrolling to complete
                    
                    # Find the load more button
                    load_more_button = None
                    attempt = 0
                    
                    while attempt < max_attempts and not load_more_button:
                        try:
                            # Try different selector strategies
                            selectors = [
                                "//button[contains(text(), 'Laad de volgende 15 resultaten')]",
                                "//button[contains(@class, 'PONCHO-typography--button-link')]",
                                "//button[@data-test='button-tertiary']"
                            ]
                            
                            for selector in selectors:
                                try:
                                    buttons = self.driver.find_elements(By.XPATH, selector)
                                    for button in buttons:
                                        if 'Laad de volgende' in button.text:
                                            load_more_button = button
                                            break
                                except:
                                    continue
                                    
                                if load_more_button:
                                    break
                            
                            if not load_more_button:
                                self.logger.warning(f"Button not found on attempt {attempt+1}")
                                # Try scrolling a bit up and down to find the button
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                                time.sleep(1)
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(1)
                                attempt += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error finding button: {str(e)}")
                            attempt += 1
                            time.sleep(1)
                    
                    if not load_more_button:
                        self.logger.warning("Load More button not found after multiple attempts")
                        # Take a screenshot to see what happened
                        self.driver.save_screenshot(f"debug/button_not_found_{clicks_done}.png")
                        
                        # Check if we've loaded enough cars already
                        if cars_shown >= total_cars * 0.9:  # If we have at least 90% of the expected cars
                            self.logger.info(f"Got {cars_shown}/{total_cars} cars (>90%). Continuing with extraction.")
                            break
                        elif clicks_done >= clicks_needed - 2:  # If we're close to the expected number of clicks
                            self.logger.info(f"Did {clicks_done}/{clicks_needed} clicks. Continuing with extraction.")
                            break
                        else:
                            # Try one more approach - click using JavaScript
                            self.logger.info("Trying direct JavaScript approach...")
                            try:
                                self.driver.execute_script("""
                                    const buttons = Array.from(document.querySelectorAll('button'));
                                    const loadMoreButton = buttons.find(button => button.textContent.includes('Laad de volgende'));
                                    if (loadMoreButton) {
                                        loadMoreButton.click();
                                    }
                                """)
                                time.sleep(5)  # Wait longer after JS click
                                clicks_done += 1
                                continue
                            except Exception as e:
                                self.logger.error(f"JavaScript click failed: {str(e)}")
                                if clicks_done >= 2:  # If we've made some progress
                                    break
                                else:
                                    # As a last resort, try refreshing the page and starting over
                                    self.driver.refresh()
                                    time.sleep(5)
                                    continue
                    
                    # Take a screenshot before clicking
                    self.driver.save_screenshot(f"debug/before_click_{clicks_done+1}.png")
                    
                    # Scroll the button into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                    time.sleep(2)  # Wait for scrolling
                    
                    # Click the button
                    try:
                        # Try regular click first
                        load_more_button.click()
                    except:
                        # If that fails, try JavaScript click
                        self.driver.execute_script("arguments[0].click();", load_more_button)
                    
                    # Wait for new content to load - longer wait
                    time.sleep(5)
                    
                    # Take a screenshot after clicking
                    self.driver.save_screenshot(f"debug/after_click_{clicks_done+1}.png")
                    
                    clicks_done += 1
                    self.logger.info(f"Clicked 'Load More' {clicks_done}/{clicks_needed}")
                    
                except StaleElementReferenceException:
                    # If element became stale, the page probably updated
                    self.logger.warning("Stale element - page might have updated")
                    time.sleep(3)
                    continue
                    
                except Exception as e:
                    self.logger.error(f"Error during 'Load More' process: {str(e)}")
                    # Take a screenshot to see what went wrong
                    self.driver.save_screenshot(f"debug/error_click_{clicks_done+1}.png")
                    
                    # If we've made some progress, continue with what we have
                    if clicks_done >= 3 or cars_shown > 45:  # If we've done a few clicks or have a decent number of cars
                        self.logger.warning(f"Continuing with {cars_shown} cars found so far")
                        break
                    else:
                        # Try a different approach if we haven't made much progress
                        try:
                            self.logger.info("Trying JavaScript approach after error...")
                            self.driver.execute_script("""
                                const buttons = Array.from(document.querySelectorAll('button'));
                                const loadMoreButton = buttons.find(button => button.textContent.includes('Laad de volgende'));
                                if (loadMoreButton) {
                                    loadMoreButton.click();
                                }
                            """)
                            time.sleep(5)
                            clicks_done += 1
                        except:
                            # If all else fails and we haven't made progress, just break
                            if clicks_done < 2:
                                self.logger.error("Failed to make progress loading cars. Moving on with limited results.")
                            break
            
            # Take a screenshot of the final page
            self.driver.save_screenshot("debug/final_page.png")
            
            # Save the final page HTML
            with open("debug/final_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Extract all car links from the fully loaded page - VERY thorough approach
            self.logger.info("Extracting all car links from the loaded page...")

            # First, save a screenshot after loading all cars
            self.driver.save_screenshot("debug/all_cars_loaded.png")

            # Get the page source for local analysis
            page_source = self.driver.page_source
            with open("debug/full_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)

            # Method 1: Use more specific CSS selectors that target actual car cards
            car_urls = []
            try:
                # Try to find the actual car cards with more specific selectors
                car_elements = self.driver.find_elements(By.CSS_SELECTOR, '.PONCHO-card, [data-test="product-card"], .card')
                
                self.logger.info(f"Found {len(car_elements)} car card elements")
                
                for card in car_elements:
                    try:
                        # Find links within each card
                        links = card.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            href = link.get_attribute('href')
                            if href and '/auto/private-lease/anwb-private-lease/aanbod/' in href and 'aanbod=new' not in href and 'begin-bij' not in href:
                                # Make sure it's a car detail page by checking URL structure
                                parts = href.split('/')
                                if len(parts) >= 7 and href not in car_urls:
                                    car_urls.append(href)
                    except Exception as e:
                        continue
            except Exception as e:
                self.logger.error(f"Error finding car cards: {str(e)}")

            # Method 2: Find all make/model headings and extract their parent links
            try:
                car_headings = self.driver.find_elements(By.CSS_SELECTOR, 'h2, h3, h4, [class*="heading"], [class*="title"]')
                
                self.logger.info(f"Found {len(car_headings)} potential car headings")
                
                for heading in car_headings:
                    try:
                        # Try to find parent or ancestor link
                        parent = heading.find_element(By.XPATH, './ancestor::a')
                        href = parent.get_attribute('href')
                        if href and '/auto/private-lease/anwb-private-lease/aanbod/' in href and 'aanbod=new' not in href:
                            parts = href.split('/')
                            if len(parts) >= 7 and href not in car_urls:
                                car_urls.append(href)
                    except:
                        # If no parent link, try finding sibling or nearby links
                        try:
                            links = heading.find_elements(By.XPATH, './following::a | ./preceding::a | ./parent::*/a')
                            for link in links[:2]:  # Only check first 2 links to avoid unrelated ones
                                href = link.get_attribute('href')
                                if href and '/auto/private-lease/anwb-private-lease/aanbod/' in href and 'aanbod=new' not in href:
                                    parts = href.split('/')
                                    if len(parts) >= 7 and href not in car_urls:
                                        car_urls.append(href)
                        except:
                            continue
            except Exception as e:
                self.logger.error(f"Error processing headings: {str(e)}")

            # Method 3: Use JavaScript to find links based on URL patterns and element context
            js_links = self.driver.execute_script("""
                // This function analyzes the DOM more deeply to find car links
                function findCarLinks() {
                    // All links on the page
                    const allLinks = Array.from(document.querySelectorAll('a'));
                    
                    // Filter for car detail links with valid structure
                    const carLinks = allLinks.filter(link => {
                        const href = link.href || '';
                        if (href.includes('/auto/private-lease/anwb-private-lease/aanbod/') && 
                            !href.includes('aanbod=new') &&
                            !href.includes('begin-bij')) {
                            
                            // Additional check: must have at least two path segments after "aanbod"
                            const parts = href.split('/aanbod/')[1];
                            return parts && parts.split('/').length >= 1 && parts.includes('/');
                        }
                        return false;
                    });
                    
                    // Get unique URLs
                    return [...new Set(carLinks.map(link => link.href))];
                }
                
                // Find car links in the page
                return findCarLinks();
            """)

            # Add JS-discovered links
            for href in js_links:
                if href not in car_urls:
                    parts = href.split('/')
                    if len(parts) >= 7:  # Valid car URL should have enough path segments
                        car_urls.append(href)

            self.logger.info(f"Extracted {len(car_urls)} unique car URLs")

            # If we still don't have enough URLs, try one more method - direct URL construction
            if len(car_urls) < 190:  # If we have fewer than 190 cars (we want all 199)
                self.logger.warning(f"Only found {len(car_urls)} cars, which is less than expected")
                
                # Extract make-model pairs from URLs we already have
                make_model_pairs = []
                for url in car_urls:
                    parts = url.split('/')
                    if len(parts) >= 7:
                        make = parts[-2]
                        model = parts[-1]
                        make_model_pairs.append((make, model))
                
                # Log what we found
                self.logger.info(f"Extracted {len(make_model_pairs)} make-model pairs from URLs")
                
                # Get a list of makes and models
                makes = sorted(list(set([pair[0] for pair in make_model_pairs])))
                self.logger.info(f"Found makes: {', '.join(makes[:10])}...")
                
                # Look through the HTML for additional make-model mentions
                try:
                    # Use regular expressions to find potential make-model pairs in the HTML
                    page_text = self.driver.page_source.lower()
                    
                    # Common makes to look for
                    common_makes = [
                        'audi', 'bmw', 'citroen', 'dacia', 'fiat', 'ford', 'hyundai', 'kia', 
                        'leapmotor', 'mazda', 'mercedes', 'mg', 'mini', 'mitsubishi', 
                        'nissan', 'opel', 'peugeot', 'renault', 'seat', 'skoda', 'suzuki', 
                        'tesla', 'toyota', 'volkswagen', 'volvo', 'byd', 'cupra', 'ds'
                    ]
                    
                    # Find all occurrences of makes in the page
                    found_makes = []
                    for make in common_makes:
                        if make in page_text:
                            found_makes.append(make)
                    
                    self.logger.info(f"Found {len(found_makes)} makes in page text")
                    
                    # Process and construct URLs for missing makes
                    base_url = "https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod"
                    new_urls = []
                    
                    # For each make we found in the page text
                    for make in found_makes:
                        # Get models we already know for this make
                        known_models = [pair[1] for pair in make_model_pairs if pair[0] == make]
                        
                        # If we're missing models for this make, try to find them in the page text
                        if not known_models:
                            # Try to find model references near make name
                            make_index = page_text.find(make)
                            if make_index > -1:
                                # Look at text after make name
                                text_after = page_text[make_index:make_index+200]
                                # Common model patterns
                                model_patterns = [
                                    r'([a-z0-9]+[-][a-z0-9]+(?:[-][a-z0-9]+)?)',  # like model-x or model-x-y
                                    r'(\d+(?:[-][a-z0-9]+)?)'  # like 208 or 208-e
                                ]
                                
                                for pattern in model_patterns:
                                    matches = re.findall(pattern, text_after)
                                    for match in matches:
                                        # Construct URL and add if it doesn't exist
                                        new_url = f"{base_url}/{make}/{match}"
                                        if new_url not in car_urls and new_url not in new_urls:
                                            new_urls.append(new_url)
                    
                    self.logger.info(f"Generated {len(new_urls)} additional URLs to try")
                    
                    # Add new URLs to our list
                    car_urls.extend(new_urls)
                except Exception as e:
                    self.logger.error(f"Error generating additional URLs: {str(e)}")

            self.logger.info(f"Final count: {len(car_urls)} unique car URLs")

            # Save the list of URLs for reference
            with open("debug/all_car_urls.json", "w", encoding="utf-8") as f:
                json.dump(car_urls, f, indent=2)

            return car_urls
        
        except Exception as e:
            self.logger.error(f"Error during URL extraction with Selenium: {str(e)}")
            # Try to extract what we can from the current state
            try:
                all_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/auto/private-lease/anwb-private-lease/aanbod/"]')
                
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/auto/private-lease/anwb-private-lease/aanbod/' in href and 'aanbod=new' not in href:
                            parts = href.split('/')
                            if len(parts) >= 7 and href not in car_urls:
                                car_urls.append(href)
                    except:
                        continue
                
                if car_urls:
                    self.logger.info(f"Recovered {len(car_urls)} URLs after error")
                    return car_urls
            except:
                pass
            
            # Return an empty list if we couldn't extract anything
            return []
    
    def start_requests(self):
        """Generate requests for all car detail pages"""
        if not self.all_car_urls:
            self.logger.error("No car URLs were found. Please check the Selenium extraction process.")
            return
        
        for url in self.all_car_urls:
            yield scrapy.Request(url, callback=self.parse_car_detail, errback=self.handle_error)
    
    def handle_error(self, failure):
        """Handle errors for failed requests"""
        self.logger.warning(f"Request failed: {failure.request.url}")
        self.stats['failed_extractions'] += 1
    
    def parse_car_detail(self, response):
        """Parse individual car detail pages"""
        try:
            self.stats['cars_processed'] += 1
            
            # Extract make and model from the URL
            url_parts = response.url.split('/')
            make = url_parts[-2].capitalize() if len(url_parts) >= 2 else ""
            model = url_parts[-1].capitalize() if len(url_parts) >= 1 else ""
            
            self.logger.info(f"Processing car {self.stats['cars_processed']}/{len(self.all_car_urls)}: {make} {model}")
            
            # Check if this is actually a car page
            # If we don't find price or car-related content, skip it
            if not re.search(r'€\s*\d+', response.text) and not any(x in response.text.lower() for x in ['lease', 'auto', 'private']):
                self.logger.warning(f"Skipping {response.url} - does not appear to be a car page")
                return
            
            # Extract price - looking for elements with € symbol
            price_element = response.css('*::text').re_first(r'€\s*(\d+(?:[\.,]\d+)?)')
            monthly_price = 0.0
            if price_element:
                monthly_price = float(price_element.replace('.', '').replace(',', '.'))
                
                # Fix for unreasonably low prices
                if monthly_price < 50:
                    monthly_price = monthly_price * 10  # Assume it's missing a digit
                    self.logger.info(f"Fixed low price: {monthly_price}")
            
            # Extract lease info - look specifically for the format "based on XX months - Y,YYY km/year"
            lease_duration = 0  # Initialize with 0 instead of default
            yearly_kilometers = 0  # Initialize with 0 instead of default
            
            # First try to find the exact pattern from the listing page
            based_on_text = response.css('p:contains("based on")::text, p:contains("gebaseerd op")::text').get()
            if not based_on_text:
                # Try a more generic approach
                based_on_texts = response.css('p::text, span::text').getall()
                for text in based_on_texts:
                    if ('months' in text.lower() or 'maanden' in text.lower()) and 'km' in text.lower():
                        based_on_text = text
                        break
            
            if based_on_text:
                # Extract months
                months_match = re.search(r'(\d+)\s*(?:months|month|maanden|maand)', based_on_text.lower())
                if months_match:
                    lease_duration = int(months_match.group(1))
                    self.logger.info(f"Extracted lease duration from listing: {lease_duration} months")
                
                # Extract kilometers - look for patterns like "5,000 km/year" or "5.000 km/year"
                km_match = re.search(r'([\d.,]+)\s*(?:k|km)/(?:year|jaar)', based_on_text.lower())
                if km_match:
                    km_text = km_match.group(1).replace('.', '').replace(',', '')
                    yearly_kilometers = int(km_text)
                    self.logger.info(f"Extracted yearly kilometers from listing: {yearly_kilometers} km/year")
            
            # If we couldn't extract from the specific pattern, fall back to our previous method
            if lease_duration == 0 or yearly_kilometers == 0:
                self.logger.info("Using fallback method for lease details")
                lease_info_elements = response.css('p::text, span::text, div::text').getall()
                
                # Only set defaults if we couldn't extract them from the page
                if lease_duration == 0:
                    lease_duration = 72  # Default most common value
                
                if yearly_kilometers == 0:
                    yearly_kilometers = 5000  # Default most common value
                
                for text in lease_info_elements:
                    # Try to extract months only if we haven't found it yet
                    if lease_duration == 72:
                        months_match = re.search(r'(\d+)\s*(?:months|month|maanden|maand)', text.lower())
                        if months_match:
                            lease_duration = int(months_match.group(1))
                    
                    # Try to extract kilometers only if we haven't found it yet
                    if yearly_kilometers == 5000:
                        km_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:k|km)', text.lower())
                        if km_match:
                            km_text = km_match.group(1).replace('.', '').replace(',', '')
                            km_value = int(km_text)
                            
                            # Fix unreasonably low km values
                            if km_value < 5000:
                                # Since the default is already 5000, don't replace with a default value
                                # Just use the value if it's reasonable
                                if km_value > 500:  # If it's at least somewhat reasonable
                                    yearly_kilometers = km_value
                                    self.logger.info(f"Using extracted yearly kilometers: {yearly_kilometers}")
                            else:
                                yearly_kilometers = km_value
            
            # Extract version/trim
            version = ""
            version_selectors = ['li::text', 'div::text', 'span::text']
            for selector in version_selectors:
                for text in response.css(selector).getall():
                    if 'version:' in text.lower() or 'versie:' in text.lower():
                        version = text.replace('Version:', '').replace('Versie:', '').strip()
                        break
                if version:  # If found, break outer loop
                    break
            
            # Extract delivery time
            delivery_time = ""
            delivery_selectors = ['li::text', 'div::text', 'span::text']
            for selector in delivery_selectors:
                for text in response.css(selector).getall():
                    if 'levertijd:' in text.lower() or 'delivery:' in text.lower():
                        delivery_time = text.replace('Levertijd:', '').replace('Delivery:', '').strip()
                        break
                if delivery_time:  # If found, break outer loop
                    break
            
            # Extract promotional tags
            promo_tags = []
            tag_selectors = [
                '.promotion-tag::text', 
                '.discount-tag::text',
                '[data-test="promotion-tag"]::text',
                'span:contains("voordeel")::text'
            ]
            
            for selector in tag_selectors:
                for tag in response.css(selector).getall():
                    if tag.strip() and tag.strip() not in promo_tags:
                        promo_tags.append(tag.strip())
            
            # If no promo tags found, try a more generic approach
            if not promo_tags:
                for text in response.css('*::text').getall():
                    if 'ledenvoordeel' in text.lower() and text.strip() not in promo_tags:
                        promo_tags.append('Ledenvoordeel')
                        break
            
            # Extract image URLs with better filtering
            image_urls = []
            car_brand_in_url = False

            # Use the make (brand) to help filter relevant images
            make_lower = make.lower()

            # Check all img elements
            for img in response.css('img::attr(src)').getall():
                # Must be an absolute URL
                if not img.startswith('http'):
                    continue
                    
                # Must be an image file or transformation
                if not ('transform' in img or '.jpg' in img or '.png' in img):
                    continue
                    
                # Exclude common non-car image patterns
                if any(x in img.lower() for x in ['icon', 'logo', 'banner', 'anwb-fietsverzekeren', 
                                                'autoverkoopservice', 'wat-je-pech', 'onderweg-app',
                                                'getty', 'campagnepagina', 'homepage', 'zonnepanelen',
                                                'energiecontract']):
                    continue
                    
                # Prefer images that contain the car make name or model
                if make_lower in img.lower() or model.lower().replace('-', '') in img.lower():
                    car_brand_in_url = True
                    image_urls.append(img)
                # Or at least match the general pattern of car images
                elif model.lower().split('-')[0] in img.lower():
                    car_brand_in_url = True
                    image_urls.append(img)
                # For images that don't explicitly mention the brand, be more selective
                elif 'transform' in img and any(x in img.lower() for x in ['front', 'back', 'side', 'interior', 'dash']):
                    image_urls.append(img)
                # Only include other transform images if we haven't found brand-specific ones yet
                elif 'transform' in img and not car_brand_in_url and not any(x in img.lower() for x in ['anwb-', 'campagne']):
                    image_urls.append(img)

            # Limit to a reasonable number - car listings typically have 5-10 images
            if len(image_urls) > 10:
                # If we have brand-specific images, prioritize those
                if car_brand_in_url:
                    brand_images = [img for img in image_urls if make_lower in img.lower() 
                                    or model.lower().replace('-', '') in img.lower()
                                    or model.lower().split('-')[0] in img.lower()]
                    if brand_images:
                        image_urls = brand_images[:10]  # Keep up to 10 brand-specific images
                    else:
                        image_urls = image_urls[:10]  # Just keep the first 10 if no brand-specific ones
                else:
                    image_urls = image_urls[:10]  # Just keep the first 10

            self.logger.info(f"Extracted {len(image_urls)} filtered car images")
            
            # Create item
            item = {
                'make': make,
                'model': model,
                'version': version,
                'monthly_price': monthly_price,
                'lease_duration_months': lease_duration,
                'yearly_kilometers': yearly_kilometers,
                'delivery_time': delivery_time,
                'promotion_tags': promo_tags,
                'image_urls': image_urls,
                'product_url': response.url
            }
            
            # Create and validate the final item
            try:
                lease_offer = LeaseOffer(**item)
                self.stats['successful_extractions'] += 1
                yield lease_offer.dict()
            except Exception as e:
                self.stats['failed_extractions'] += 1
                self.logger.error(f"Validation error for {response.url}: {str(e)}")
        
        except Exception as e:
            self.stats['failed_extractions'] += 1
            self.logger.error(f"Error processing {response.url}: {str(e)}")
    
    def closed(self, reason):
        """Log final statistics when spider closes"""
        # Close the Selenium driver
        if hasattr(self, 'driver'):
            self.driver.quit()
        
        self.logger.info("Spider closed. Final statistics:")
        self.logger.info(f"Car links found: {self.stats['car_links_found']}")
        self.logger.info(f"Cars processed: {self.stats['cars_processed']}")
        self.logger.info(f"Successful extractions: {self.stats['successful_extractions']}")
        self.logger.info(f"Failed extractions: {self.stats['failed_extractions']}")
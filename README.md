# ANWB Private Lease Scraper

## Overview
This scraper extracts car leasing information from the ANWB Private Lease website, including:
- Car make & model
- Version / trim
- Monthly lease price
- Lease duration & kilometers per year
- Delivery time / availability
- Bonus or discount tags
- Car image URLs

## Current Implementation
The current implementation uses a predefined list of 10 car URLs to demonstrate the extraction functionality. This approach was chosen for reliability and simplicity for the assignment.

## Full Solution for Discovery of All 199 Listings
To extract all 199 car listings, a URL discovery mechanism would need to be implemented. This would involve:

1. Starting at the main listing page: https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod/aanbod=new
2. Using browser automation (Playwright or Selenium) to extract all car links
3. Following pagination to get all pages of results
4. Saving and using the complete list of URLs

Below is a pseudocode example of how this discovery process would work:

```python

    # For a full solution that discovers all 199 car URLs, this method would be implemented:
    # 1. Start at the main listing page: https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod/aanbod=new
    # 2. Use browser automation (like Selenium or Playwright) to extract all car links
    # 3. Follow pagination to get all pages of results
    # 4. Save the complete list of URLs
    
    # A pseudocode example of how this would work:
    def discover_all_car_urls():
        from playwright.sync_api import sync_playwright
        
        car_urls = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Visit main listing page
            page.goto("https://www.anwb.nl/auto/private-lease/anwb-private-lease/aanbod/aanbod=new")
            page.wait_for_load_state("networkidle")
            
            # Loop through all pages
            has_next_page = True
            while has_next_page:
                # Extract all car links on current page
                links = page.query_selector_all('a[href*="/auto/private-lease/anwb-private-lease/aanbod/"]')
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/aanbod/' in href and not href.endswith('aanbod=new'):
                        full_url = 'https://www.anwb.nl' + href if not href.startswith('http') else href
                        if full_url not in car_urls:
                            car_urls.append(full_url)
                
                # Check for next page button
                next_button = page.query_selector('a[aria-label="Volgende pagina"]')
                if next_button:
                    next_button.click()
                    page.wait_for_load_state("networkidle")
                else:
                    has_next_page = False
            
            browser.close()
        
        # Save URLs to file
        with open('all_car_urls.json', 'w') as f:
            json.dump(car_urls, f, indent=2)
        
        return car_urls
    ```

## Running the Scraper
1. Ensure you have the required dependencies installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the spider:
   ```
   scrapy crawl anwb_lease
   ```

3. The results will be saved in both JSON and CSV formats in the `output` directory.

## File Structure
- `anwb_lease_scraper/` - Main project directory
  - `spiders/` - Contains the spider implementation
  - `items.py` - Defines the data structure and validation
  - `pipelines.py` - Handles processing and saving the data
- `output/` - Contains the extracted data
- `debug/` - Contains debugging information
            
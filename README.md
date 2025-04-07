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

## Solution Overview
The implementation uses Scrapy with Selenium for browser automation to handle dynamic content loading. The scraper performs the following steps:

1. Uses Selenium to navigate to the main listing page and extracts all 199 car listing URLs by:
   - Automatically clicking the "Load More" button to reveal all listings
   - Extracting all car detail page URLs using various CSS selectors and JavaScript techniques
   - Handling edge cases and potential errors during the discovery process

2. Scrapes each individual car page to extract detailed information
   - Extracts pricing, configuration, and promotional information
   - Validates and transforms the data
   - Handles various formats and error cases

3. Saves the results in both JSON and CSV formats with validation

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone this repository
3. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Install the Chrome browser if not already installed (required for Selenium)

## Running the Scraper

To run the scraper that extracts all car listings:
```
scrapy crawl anwb_lease
```

## Output
The scraped data will be saved in the `output` directory in both JSON and CSV formats.

## Project Structure
- `fix_car_lease_scraper/` - Main project directory
  - `spiders/` - Contains the spider implementation
    - `anwb_spider.py` - Main spider that extracts all car listings
  - `processors/` - Contains data processing utilities
    - `transformers.py` - Data transformation utilities
    - `validators.py` - Data validation utilities
  - `items.py` - Defines data models with validation using Pydantic
  - `pipelines.py` - Processing pipelines for validation and storage
  - `settings.py` - Scrapy settings
- `output/` - Output directory for scraped data

## Notes
- The scraper handles anti-bot mechanisms by using browser automation with realistic user agent and behavior
- Error handling and retries are implemented throughout the scraping process
- Data validation ensures the extracted data meets the expected format and value ranges
- The solution is designed to be robust against changes in the website structure

## Limitations
- The scraper requires Chrome browser and ChromeDriver to be installed
- Performance may vary depending on network conditions and website load
- The website structure may change, requiring updates to the selectors used in the scraper
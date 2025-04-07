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

## Scheduling

The project includes a scheduler component (`scheduler.py`) for implementing automated, regular data collection. This scheduler is a wrapper script for the scraper that adds error handling, logging, and retry capabilities.

### Important Note on the Scheduler

**The `scheduler.py` script itself DOES NOT automatically schedule anything.** It is designed to be called by an external scheduling system like cron (Linux/Mac) or Task Scheduler (Windows).

The scheduler component serves several purposes:
1. Provides a stable execution environment for the scraper
2. Implements error handling and automatic retries if the scraper fails
3. Maintains detailed logs of execution history and results
4. Creates a standardized interface for external scheduling systems

### Running the scheduler manually:
```
python scheduler.py
```
This will run the scraper once with retry logic.

### Setting up automated scheduling:

To run the scraper on a regular schedule (e.g., daily), you need to configure an external scheduling system:

#### Using cron (Linux/Mac):
```
# Edit crontab
crontab -e

# Add line to run daily at 2 AM
0 2 * * * cd /path/to/project && /path/to/venv/bin/python scheduler.py
```

#### Using Windows Task Scheduler:
1. Open Task Scheduler
2. Create a Basic Task
3. Set the trigger (e.g., Daily at 2 AM)
4. Set the action to "Start a program"
5. Program/script: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `scheduler.py`
7. Start in: `C:\path\to\project`

### How the scheduling system works:

1. The external scheduler (cron, Task Scheduler) determines WHEN to run
2. The `scheduler.py` script determines HOW to run (with retries, logging, etc.)
3. The scraper (`anwb_lease`) performs the actual data collection

This separation of concerns allows for a robust and maintainable data pipeline.

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
- `scheduler.py` - Script for scheduling regular scraper runs

## Notes
- The scraper handles anti-bot mechanisms by using browser automation with realistic user agent and behavior
- Error handling and retries are implemented throughout the scraping process
- Data validation ensures the extracted data meets the expected format and value ranges
- The solution is designed to be robust against changes in the website structure

## Limitations
- The scraper requires Chrome browser and ChromeDriver to be installed
- Performance may vary depending on network conditions and website load
- The website structure may change, requiring updates to the selectors used in the scraper
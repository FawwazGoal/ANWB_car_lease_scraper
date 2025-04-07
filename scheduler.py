"""
ANWB Lease Scraper Scheduler
----------------------------
This script serves as a job wrapper for the ANWB lease scraper.

IMPORTANT: This script does NOT schedule itself automatically. 
It is designed to be executed by an external scheduling system such as:
- cron (Linux/Mac)
- Windows Task Scheduler
- Airflow
- Jenkins
- etc.

Purpose:
1. Provides a stable execution environment for the scraper
2. Implements error handling and automatic retries
3. Manages logging of execution results
4. Creates a standard interface for external schedulers

Usage:
    python scheduler.py

For production use, this script should be called by your system's scheduler.
See README.md for detailed setup instructions.
"""

import os
import subprocess
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='scraper_scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run_scraper():
    """
    Run the ANWB lease scraper and log the results.
    
    Returns:
        bool: True if scraper completed successfully, False otherwise
    """
    try:
        # Log start time
        start_time = datetime.now()
        logging.info(f"Starting ANWB lease scraper run at {start_time}")
        
        # Generate a timestamp for output files
        timestamp = start_time.strftime('%Y%m%d%H%M%S')
        
        # Run the scraper
        result = subprocess.run(
            ['scrapy', 'crawl', 'anwb_lease'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"Scraper completed successfully in {duration:.2f} seconds")
        
        # Save the output to a log file
        with open(f'output/scraper_run_{timestamp}.log', 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        logging.info(f"Scraper output saved to output/scraper_run_{timestamp}.log")
        
        return True
        
    except subprocess.CalledProcessError as e:
        # Log error information
        logging.error(f"Scraper failed with exit code {e.returncode}")
        if e.stderr:
            logging.error(f"Error output: {e.stderr}")
            
        # Save the error output to a log file
        with open(f'output/scraper_error_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', 'w', encoding='utf-8') as f:
            f.write(f"Exit code: {e.returncode}\n\n")
            f.write(f"Standard output:\n{e.stdout}\n\n")
            f.write(f"Error output:\n{e.stderr}")
            
        return False
    
    except Exception as e:
        # Handle other exceptions
        logging.error(f"Unexpected error running scraper: {str(e)}")
        return False

def run_with_retry(max_retries=3, retry_delay=300):
    """
    Run the scraper with automatic retries on failure.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        bool: True if successful, False if all retries failed
    """
    for attempt in range(1, max_retries + 1):
        success = run_scraper()
        if success:
            return True
        
        # If failed but we have retries left
        if attempt < max_retries:
            logging.info(f"Retry {attempt}/{max_retries} scheduled after {retry_delay} seconds")
            time.sleep(retry_delay)
    
    logging.error(f"Scraper failed after {max_retries} attempts")
    return False

if __name__ == "__main__":
    # This will execute when the script is run directly
    # When called by a scheduler like cron, this is the entry point
    print("ANWB Lease Scraper Scheduler")
    print("============================")
    print("Starting scraper execution with retry logic")
    print("NOTE: This script does not schedule itself automatically.")
    print("It should be called by an external scheduler like cron or Task Scheduler.")
    print("See README.md for setup instructions.")
    print("============================")
    
    result = run_with_retry()
    
    if result:
        print("Scraper completed successfully!")
    else:
        print("Scraper failed after multiple attempts. Check logs for details.")
    
    print(f"Logs available in: scraper_scheduler.log and output/ directory")
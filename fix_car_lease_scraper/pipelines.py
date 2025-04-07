import json
import csv
import os
from itemadapter import ItemAdapter
from datetime import datetime
from fix_car_lease_scraper.processors.validators import validate_lease_offer

class ValidationPipeline:
    """
    Pipeline to validate scraped items.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validate the item
        errors = validate_lease_offer(dict(adapter))
        
        if errors:
            spider.logger.warning(f"Validation errors for {adapter.get('product_url')}: {errors}")
            # Add validation errors to the item
            adapter['validation_errors'] = errors
        
        return item

class JsonWriterPipeline:
    """
    Pipeline to write items to a JSON file.
    """
    def __init__(self):
        self.items = []
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.file_path = f'output/lease_offers_{timestamp}.json'
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Only store valid items
        if not adapter.get('validation_errors'):
            self.items.append(dict(adapter))
        return item
    
    def close_spider(self, spider):
        # Write items to JSON file
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4)
        
        spider.logger.info(f"Saved {len(self.items)} valid lease offers to {self.file_path}")

class CsvWriterPipeline:
    """
    Pipeline to write items to a CSV file.
    """
    def __init__(self):
        self.items = []
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.file_path = f'output/lease_offers_{timestamp}.csv'
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Only store valid items
        if not adapter.get('validation_errors'):
            # Handle lists by converting to string
            item_dict = dict(adapter)
            
            # Convert lists to strings
            for key, value in item_dict.items():
                if isinstance(value, list):
                    item_dict[key] = '; '.join(map(str, value))
            
            self.items.append(item_dict)
        return item
    
    def close_spider(self, spider):
        if not self.items:
            spider.logger.warning("No valid items to write to CSV")
            return
        
        # Write items to CSV file
        with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
            # Get field names from the first item
            fieldnames = self.items[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(self.items)
        
        spider.logger.info(f"Saved {len(self.items)} valid lease offers to {self.file_path}")

class LeaseOffersPipeline:
    """
    Combined pipeline that uses both JSON and CSV writers.
    """
    def __init__(self):
        self.json_pipeline = JsonWriterPipeline()
        self.csv_pipeline = CsvWriterPipeline()
    
    def process_item(self, item, spider):
        self.json_pipeline.process_item(item, spider)
        self.csv_pipeline.process_item(item, spider)
        return item
    
    def close_spider(self, spider):
        self.json_pipeline.close_spider(spider)
        self.csv_pipeline.close_spider(spider)
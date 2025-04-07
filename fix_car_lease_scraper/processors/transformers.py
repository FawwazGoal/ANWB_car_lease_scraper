import re
from typing import Tuple, Optional

def clean_price(price_text: Optional[str]) -> float:
    """
    Extract and clean the price from a text string.
    
    Args:
        price_text: A string containing the price, e.g. "€ 329,-"
        
    Returns:
        The price as a float, e.g. 329.0
    """
    if not price_text:
        return 0.0
    
    # Extract digits and possible decimal part
    price_match = re.search(r'(\d+)(?:,(\d+))?', price_text)
    if not price_match:
        return 0.0
    
    # Get digits
    euros = price_match.group(1)
    cents = price_match.group(2) if price_match.group(2) else '0'
    
    # Convert to float
    return float(f"{euros}.{cents}")

def extract_duration_kilometers(lease_info: Optional[str]) -> Tuple[int, int]:
    """
    Extract lease duration and kilometers from the lease info text.
    
    Args:
        lease_info: A string like "based on 72 months - 5,000 km/year"
        
    Returns:
        A tuple of (duration_months, yearly_kilometers)
    """
    if not lease_info:
        return 60, 10000  # Default values
    
    # Extract duration
    duration_match = re.search(r'(\d+)\s*(?:months|month|maanden|maand)', lease_info.lower())
    duration = int(duration_match.group(1)) if duration_match else 60
    
    # Extract kilometers
    km_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:k|km)/(?:year|jaar)', lease_info.lower())
    
    if km_match:
        km_text = km_match.group(1).replace('.', '').replace(',', '')
        kilometers = int(km_text)
    else:
        kilometers = 10000  # Default
    
    return duration, kilometers

def extract_make_model(make_model_text: Optional[str]) -> Tuple[str, str]:
    """
    Extract make and model from a combined text.
    
    Args:
        make_model_text: A string like "Leapmotor T03"
        
    Returns:
        A tuple of (make, model)
    """
    if not make_model_text:
        return "", ""
    
    # Common car brands to help with splitting
    common_brands = [
        "Alfa Romeo", "Audi", "BMW", "Citroën", "Citroen", "Dacia", "Fiat", "Ford", 
        "Honda", "Hyundai", "Jaguar", "Jeep", "Kia", "Land Rover", "Lexus", "Mazda", 
        "Mercedes", "Mercedes-Benz", "Mini", "Mitsubishi", "Nissan", "Opel", "Peugeot", 
        "Porsche", "Renault", "Seat", "Skoda", "Škoda", "Suzuki", "Tesla", "Toyota", 
        "Volkswagen", "Volvo", "MG", "Leapmotor"
    ]
    
    # Try to find a known brand in the text
    for brand in common_brands:
        if make_model_text.lower().startswith(brand.lower()):
            make = brand
            model = make_model_text[len(brand):].strip()
            return make, model
    
    # Fallback: split on first space
    parts = make_model_text.split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    
    # If all else fails, return the whole text as model and unknown make
    return "Unknown", make_model_text
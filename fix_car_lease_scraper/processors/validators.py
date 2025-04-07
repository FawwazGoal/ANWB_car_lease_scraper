import re
from typing import Dict, Any, List, Optional, Union

def validate_make_model(make: str, model: str) -> bool:
    """
    Validate that make and model are not empty.
    
    Args:
        make: Car manufacturer
        model: Car model
    
    Returns:
        True if valid, False otherwise
    """
    if not make or not model:
        return False
    
    if make.lower() == "unknown" and not model:
        return False
    
    return True

def validate_price(price: Union[float, str]) -> bool:
    """
    Validate that price is within a reasonable range.
    
    Args:
        price: Price value
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Convert to float if string
        if isinstance(price, str):
            price = float(price.replace(',', '.'))
        
        # Check range
        return 50.0 <= price <= 3000.0
    except (ValueError, TypeError):
        return False

def validate_lease_duration(duration: Union[int, str]) -> bool:
    """
    Validate that lease duration is within expected range.
    
    Args:
        duration: Lease duration in months
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Convert to int if string
        if isinstance(duration, str):
            duration = int(duration)
        
        # Check range
        return 12 <= duration <= 72
    except (ValueError, TypeError):
        return False

def validate_kilometers(km: Union[int, str]) -> bool:
    """
    Validate that yearly kilometers is within expected range.
    
    Args:
        km: Yearly kilometers
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Convert to int if string
        if isinstance(km, str):
            km = int(km.replace(',', '').replace('.', ''))
        
        # Check range
        return 5000 <= km <= 50000
    except (ValueError, TypeError):
        return False

def validate_image_url(url: str) -> bool:
    """
    Validate that an image URL is properly formatted.
    
    Args:
        url: Image URL
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Simple URL validation
    return url.startswith('http://') or url.startswith('https://')

def validate_lease_offer(offer: Dict[str, Any]) -> List[str]:
    """
    Validate a complete lease offer and return a list of validation errors.
    
    Args:
        offer: Lease offer data
        
    Returns:
        List of validation error messages (empty if no errors)
    """
    errors = []
    
    # Required fields
    if not validate_make_model(offer.get('make', ''), offer.get('model', '')):
        errors.append("Invalid or missing make/model")
    
    if not validate_price(offer.get('monthly_price', 0)):
        errors.append(f"Invalid price: {offer.get('monthly_price')}")
    
    if not validate_lease_duration(offer.get('lease_duration_months', 0)):
        errors.append(f"Invalid lease duration: {offer.get('lease_duration_months')}")
    
    if not validate_kilometers(offer.get('yearly_kilometers', 0)):
        errors.append(f"Invalid yearly kilometers: {offer.get('yearly_kilometers')}")
    
    # Optional fields
    if 'image_urls' in offer and offer['image_urls']:
        invalid_urls = [url for url in offer['image_urls'] if not validate_image_url(url)]
        if invalid_urls:
            errors.append(f"Invalid image URLs: {len(invalid_urls)} invalid URLs")
    
    # URL field
    if not offer.get('product_url') or not isinstance(offer.get('product_url'), str):
        errors.append("Missing or invalid product URL")
    
    return errors
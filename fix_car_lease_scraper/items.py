import re
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class LeaseOffer(BaseModel):
    """
    Pydantic model for a lease offer.
    This provides both data structure and validation.
    """
    make: str = Field(..., description="Car manufacturer")
    model: str = Field(..., description="Car model")
    version: Optional[str] = Field(None, description="Car version/trim")
    monthly_price: float = Field(..., description="Monthly lease price in EUR")
    lease_duration_months: int = Field(..., description="Lease duration in months")
    yearly_kilometers: int = Field(..., description="Kilometers per year allowed")
    delivery_time: Optional[str] = Field(None, description="Delivery time or availability")
    promotion_tags: List[str] = Field(default_factory=list, description="Promotional or discount tags")
    image_urls: List[str] = Field(default_factory=list, description="URLs of car images")
    product_url: str = Field(..., description="URL to the detailed product page")
    
    @validator('monthly_price')
    def validate_price(cls, v):
        """Validate that the price is within a reasonable range."""
        if v < 50 or v > 3000:
            raise ValueError(f"Monthly price (€{v}) is outside reasonable range (€50-€3000)")
        return v
    
    @validator('lease_duration_months')
    def validate_duration(cls, v):
        """Validate that the lease duration is within expected range."""
        if v < 12 or v > 72:
            raise ValueError(f"Lease duration ({v} months) is outside expected range (12-72 months)")
        return v
    
    @validator('yearly_kilometers')
    def validate_kilometers(cls, v):
        """
        Validate yearly kilometers and fix unreasonably low values.
        If the value is below 5,000, use the default 5,000 instead.
        """
        if v < 500:
            # Very low values are likely errors
            return 5000
        elif v < 5000:
            # Low but plausible values are accepted but normalized to 5000
            return 5000
        elif v > 50000:
            # Very high values are likely errors
            raise ValueError(f"Yearly kilometers ({v}) is outside expected range (5,000-50,000)")
        return v
    
    @validator('image_urls')
    def validate_image_urls(cls, urls):
        """Validate that all image URLs are properly formatted."""
        valid_urls = []
        for url in urls:
            # Simple URL validation
            if url and isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
                valid_urls.append(url)
        return valid_urls

    class Config:
        """Configuration for the Pydantic model."""
        title = "Lease Offer"
        validate_assignment = True
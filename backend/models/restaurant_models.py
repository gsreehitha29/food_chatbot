"""
=============================================================
RESTAURANT PYDANTIC MODELS
=============================================================
These models define the data shape for restaurant-related operations.

Pydantic models serve two purposes:
1. REQUEST VALIDATION  - Ensures incoming API data is correct
2. RESPONSE FORMATTING - Controls what data goes back to the client

The 'model_config' with json_schema_extra provides example
values that show up in the Swagger docs (/docs) for testing.
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional


# -------------------------------------------------------
# REQUEST MODEL: Create/Add a new restaurant
# -------------------------------------------------------
class RestaurantCreateRequest(BaseModel):
    """Data required to create a new restaurant."""
    restaurant_name: str = Field(..., min_length=1, max_length=150, description="Name of the restaurant")
    location: str = Field(..., min_length=1, description="Physical location of the restaurant")
    cuisine: str = Field(..., min_length=1, description="Cuisine type served by the restaurant")
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating of the restaurant")
    delivery_time: str = Field(default="", description="Estimated delivery time, e.g., '30-40 mins'")
    price_for_two: float = Field(default=0.0, ge=0.0, description="Average price for two people")
    is_open: bool = Field(default=True, description="Whether the restaurant is currently open")
    contact_number: Optional[str] = Field(default=None, description="Optional contact number for the restaurant")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "restaurant_name": "Pizza Palace",
                    "location": "Koramangala, Bangalore",
                    "cuisine": "Italian",
                    "rating": 4.5,
                    "delivery_time": "30-40 mins",
                    "price_for_two": 600.0,
                    "is_open": True,
                    "contact_number": "9876543210"
                }
            ]
        }
    }


# -------------------------------------------------------
# RESPONSE MODEL: Restaurant details returned to client
# -------------------------------------------------------
class RestaurantResponse(BaseModel):
    """Restaurant data returned in API responses."""
    restaurant_id: str = Field(..., description="Unique restaurant identifier")
    restaurant_name: str = Field(..., description="Name of the restaurant")
    location: str = Field(..., description="Physical location of the restaurant")
    cuisine: str = Field(..., description="Cuisine type served by the restaurant")
    rating: float = Field(default=0.0, description="Average rating of the restaurant")
    delivery_time: str = Field(default="", description="Estimated delivery time")
    price_for_two: float = Field(default=0.0, description="Average price for two people")
    is_open: bool = Field(default=True, description="Whether the restaurant is currently open")
    contact_number: Optional[str] = Field(default=None, description="Optional contact number for the restaurant")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "restaurant_id": "REST001",
                    "restaurant_name": "Pizza Palace",
                    "location": "Koramangala, Bangalore",
                    "cuisine": "Italian",
                    "rating": 4.5,
                    "delivery_time": "30-40 mins",
                    "price_for_two": 600.0,
                    "is_open": True,
                    "contact_number": "9876543210"
                }
            ]
        }
    }

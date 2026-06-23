"""
=============================================================
MENU PYDANTIC MODELS
=============================================================
Models for menu items and search results.

FIX #12: Removed the duplicate RestaurantResponse class that
previously existed alongside the canonical one in restaurant_models.py.
If you need RestaurantResponse, import it from:
    from models.restaurant_models import RestaurantResponse

KEY CONCEPTS:
- MenuItemResponse: What the API sends back for a menu item
- MenuSearchResponse: Wraps search results with metadata
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# FIX #12: RestaurantResponse is NOT defined here anymore.
# It was a duplicate of the class in restaurant_models.py.
# Import from: from models.restaurant_models import RestaurantResponse


# -------------------------------------------------------
# RESPONSE MODEL: A single menu item
# -------------------------------------------------------
class MenuItemResponse(BaseModel):
    """Menu item data returned in API responses."""
    item_id: str
    restaurant_id: str
    category_id: str
    item_name: str
    description: str = ""
    price: float
    veg_or_nonveg: str = "veg"  # "veg" or "nonveg"
    rating: float = 0.0
    availability: bool = True


# -------------------------------------------------------
# RESPONSE MODEL: Menu search results
# -------------------------------------------------------
class MenuSearchResponse(BaseModel):
    """Wraps search results with the query and count."""
    query: str
    total_results: int
    items: List[MenuItemResponse]

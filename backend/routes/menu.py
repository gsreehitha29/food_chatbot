"""
=============================================================
MENU ROUTES
=============================================================
API endpoints for browsing restaurants and menu items.

ENDPOINTS:
  GET /menu              → List all restaurants
  GET /menu/{id}         → Get menu for a specific restaurant
  GET /menu/search?q=    → Search menu items by name/description

HOW ROUTING WORKS:
- We create an APIRouter with a prefix "/menu"
- Each function is decorated with the HTTP method
- FastAPI auto-generates Swagger docs at /docs
=============================================================
"""

from fastapi import APIRouter, HTTPException, Query
from services.menu_service import (
    get_all_restaurants,
    get_menu_by_restaurant,
    search_menu_items,
    search_menu_items_regex
)

# Create a router with /menu prefix and "Menu" tag for Swagger
router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get(
    "/",
    summary="List all restaurants",
    description="Returns a list of all restaurants in the system."
)
def list_restaurants():
    """
    GET /menu
    
    Returns all restaurants with their details.
    
    Sample Response:
    [
        {
            "restaurant_id": "REST001",
            "restaurant_name": "Pizza Palace",
            "location": "Koramangala, Bangalore",
            "cuisine": "Italian",
            "rating": 4.5,
            "delivery_time": "30-40 mins",
            "price_for_two": 600,
            "is_open": true,
            "contact_number": "9876543210"
        }
    ]
    """
    restaurants = get_all_restaurants()
    return {
        "status": "success",
        "total": len(restaurants),
        "restaurants": restaurants
    }


@router.get(
    "/search",
    summary="Search menu items",
    description="Search for menu items across all restaurants by name or description."
)
def search_menu(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query (e.g., 'pizza', 'biryani', 'burger')"
    )
):
    """
    GET /menu/search?q=pizza
    
    Searches across all restaurant menus using MongoDB text search.
    Falls back to regex search if text index is not available.
    
    Sample Response:
    {
        "status": "success",
        "query": "pizza",
        "total_results": 3,
        "items": [
            {
                "item_id": "ITEM001",
                "item_name": "Margherita Pizza",
                "price": 299,
                ...
            }
        ]
    }
    """
    try:
        # Try text search first (faster, relevance-ranked)
        items = search_menu_items(q)
    except Exception:
        # Fall back to regex search if text index issues
        items = search_menu_items_regex(q)

    if not items:
        raise HTTPException(
            status_code=404,
            detail=f"No menu items found matching '{q}'"
        )

    return {
        "status": "success",
        "query": q,
        "total_results": len(items),
        "items": items
    }


@router.get(
    "/{restaurant_id}",
    summary="Get restaurant menu",
    description="Returns the full menu for a specific restaurant."
)
def get_restaurant_menu(restaurant_id: str):
    """
    GET /menu/REST001
    
    Returns the restaurant info along with all its menu items.
    
    Sample Response:
    {
        "status": "success",
        "restaurant": { ... },
        "menu_items": [ ... ],
        "total_items": 15
    }
    """
    result = get_menu_by_restaurant(restaurant_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Restaurant with ID '{restaurant_id}' not found"
        )

    return {
        "status": "success",
        **result
    }

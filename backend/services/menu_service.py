"""
=============================================================
MENU SERVICE
=============================================================
Business logic for menu and restaurant operations.

This service layer sits between routes and the database.
Routes call service functions → services talk to MongoDB.

WHY A SERVICE LAYER?
- Keeps routes thin (just HTTP handling)
- Business logic is reusable and testable
- Easy to swap database without changing routes
=============================================================
"""

from database import menu_collection, restaurants_collection
import re  # FIX #19: needed for safe regex escaping


def _normalize_restaurant(doc: dict) -> dict:
    """
    Normalize a restaurant document from chatbot_database to a consistent
    shape the frontend expects.

    Real DB differences:
    - cuisine is a list  e.g. ["Arabian", "Middle Eastern"]
    - delivery_time is absent  → supply a default
    """
    if isinstance(doc.get("cuisine"), list):
        doc["cuisine"] = ", ".join(doc["cuisine"])
    if "delivery_time" not in doc:
        doc["delivery_time"] = "30-45 mins"
    return doc


def get_all_restaurants():
    """
    Fetch all restaurants from the database.

    Returns a list of restaurant dicts with MongoDB _id removed.
    The projection {'_id': 0} tells MongoDB to exclude the
    internal _id field from results.
    """
    restaurants = list(restaurants_collection.find({}, {"_id": 0}))
    return [_normalize_restaurant(r) for r in restaurants]


def get_menu_by_restaurant(restaurant_id: str):
    """
    Fetch all menu items for a specific restaurant.

    Args:
        restaurant_id: The unique ID of the restaurant

    Returns:
        dict with restaurant info and its menu items,
        or None if restaurant not found
    """
    # First, check if the restaurant exists
    restaurant = restaurants_collection.find_one(
        {"restaurant_id": restaurant_id}, {"_id": 0}
    )
    if not restaurant:
        return None

    restaurant = _normalize_restaurant(restaurant)

    # Fetch all menu items for this restaurant, injecting restaurant_name
    items = list(
        menu_collection.find(
            {"restaurant_id": restaurant_id}, {"_id": 0}
        )
    )

    # Normalize veg_or_nonveg casing and attach restaurant_name for search results
    rest_name = restaurant.get("restaurant_name", "")
    for item in items:
        item.setdefault("restaurant_name", rest_name)
        # Normalise to lowercase so frontend CSS classes work ('veg' / 'nonveg')
        veg_val = item.get("veg_or_nonveg", "veg")
        item["veg_or_nonveg"] = "veg" if "veg" in veg_val.lower() and "non" not in veg_val.lower() else "nonveg"

    return {
        "restaurant": restaurant,
        "menu_items": items,
        "total_items": len(items)
    }


def search_menu_items(query: str):
    """
    Search menu items by name or description using text search.
    
    MongoDB text search uses the text index we created on
    'item_name' and 'description' fields in database.py.
    
    The $text operator performs a text search on indexed fields.
    $meta: "textScore" ranks results by relevance.
    
    Args:
        query: Search term (e.g., "pizza", "biryani")
    
    Returns:
        List of matching menu items sorted by relevance
    """
    # Use MongoDB text search for best results
    items = list(
        menu_collection.find(
            {"$text": {"$search": query}},
            {"_id": 0, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
    )

    # Remove the text score from results (internal use only)
    for item in items:
        item.pop("score", None)

    return items


def search_menu_items_regex(query: str):
    """
    Fallback search using regex if text index is not available.
    
    This is slower than text search but works without indexes.
    The $regex operator matches partial strings.
    $options: "i" makes it case-insensitive.
    
    FIX #19: User input is sanitized with re.escape() to prevent
    regex injection attacks (e.g., query ".*(drop)" causing issues).
    
    Args:
        query: Search term
    
    Returns:
        List of matching menu items
    """
    safe_query = re.escape(query)  # FIX #19: Escape special regex characters
    items = list(
        menu_collection.find(
            {
                "$or": [
                    {"item_name": {"$regex": safe_query, "$options": "i"}},
                    {"description": {"$regex": safe_query, "$options": "i"}}
                ]
            },
            {"_id": 0}
        )
    )
    return items

"""
=============================================================
RECOMMENDATION SERVICE
=============================================================
Rule-based food recommendation engine.

HOW IT WORKS:
1. Looks at what's in the user's cart
2. Uses a PAIRING RULES dictionary to suggest complementary items
3. Also suggests popular items from the same restaurant
4. Returns a combined list of recommendations

PAIRING RULES EXAMPLES:
- Pizza → Coke, Garlic Bread
- Burger → Fries, Milkshake
- Biryani → Raita, Mirchi Ka Salan

This is a rule-based system (not ML). It uses keyword matching
on item names to trigger relevant pairings.
=============================================================
"""

from database import menu_collection, carts_collection


# -------------------------------------------------------
# PAIRING RULES
# -------------------------------------------------------
# Key = keyword to look for in cart item names (lowercase)
# Value = list of item name keywords to recommend
# -------------------------------------------------------
PAIRING_RULES = {
    "pizza": ["coke", "garlic bread", "pasta", "mocktail"],
    "burger": ["fries", "coke", "milkshake", "onion rings"],
    "biryani": ["raita", "mirchi ka salan", "gulab jamun", "lassi"],
    "dosa": ["sambar", "chutney", "filter coffee", "vada"],
    "noodles": ["spring roll", "manchurian", "fried rice", "soup"],
    "fried rice": ["manchurian", "spring roll", "soup", "noodles"],
    "sandwich": ["fries", "juice", "soup", "cookies"],
    "pasta": ["garlic bread", "soup", "coke", "tiramisu"],
    "momos": ["soup", "chutney", "fried rice", "thukpa"],
    "thali": ["lassi", "buttermilk", "papad", "pickle"],
    "paneer": ["naan", "roti", "rice", "raita"],
    "chicken": ["naan", "roti", "rice", "raita"],
    "dal": ["rice", "roti", "papad", "pickle"],
    "rolls": ["coke", "fries", "chutney", "soup"],
    "wrap": ["fries", "juice", "nachos", "smoothie"],
    "ice cream": ["brownie", "waffle", "milkshake", "cookies"],
    "cake": ["coffee", "tea", "ice cream", "pastry"],
    "coffee": ["sandwich", "cake", "cookies", "muffin"],
    "tea": ["samosa", "biscuit", "pakora", "cake"],
}


def get_recommendations(user_id: str):
    """
    Generate food recommendations based on the user's cart.
    
    ALGORITHM:
    1. Fetch the user's cart
    2. For each item in cart, check pairing rules
    3. Find matching items in the restaurant's menu
    4. Also add top-rated items from the restaurant
    5. Remove duplicates and items already in cart
    6. Return top 5 recommendations
    
    Args:
        user_id: The user's ID
    
    Returns:
        dict with cart_based and popular recommendations
    """
    # Step 1: Get the user's cart
    cart = carts_collection.find_one({"user_id": user_id}, {"_id": 0})

    if not cart or len(cart.get("items", [])) == 0:
        # No cart → return general popular items
        popular = list(
            menu_collection.find(
                {"availability": True},
                {"_id": 0}
            ).sort("rating", -1).limit(5)
        )
        return {
            "message": "No cart found. Here are popular items!",
            "cart_based": [],
            "popular": popular
        }

    restaurant_id = cart["restaurant_id"]
    cart_item_ids = {item["item_id"] for item in cart["items"]}
    cart_item_names = [item["item_name"].lower() for item in cart["items"]]

    # Step 2: Find recommended keywords based on pairing rules
    recommended_keywords = []
    for cart_name in cart_item_names:
        for rule_key, suggestions in PAIRING_RULES.items():
            if rule_key in cart_name:
                recommended_keywords.extend(suggestions)

    # Remove duplicates
    recommended_keywords = list(set(recommended_keywords))

    # Step 3: Search the restaurant's menu for matching items
    cart_based = []
    for keyword in recommended_keywords:
        matches = list(
            menu_collection.find(
                {
                    "restaurant_id": restaurant_id,
                    "item_name": {"$regex": keyword, "$options": "i"},
                    "availability": True
                },
                {"_id": 0}
            )
        )
        for match in matches:
            # Don't recommend items already in cart
            if match["item_id"] not in cart_item_ids:
                cart_based.append(match)
                cart_item_ids.add(match["item_id"])  # Prevent duplicates

    # Step 4: Get popular items from the same restaurant
    popular = list(
        menu_collection.find(
            {
                "restaurant_id": restaurant_id,
                "availability": True,
                "item_id": {"$nin": list(cart_item_ids)}
            },
            {"_id": 0}
        ).sort("rating", -1).limit(5)
    )

    return {
        "message": "Here are some items you might enjoy!",
        "cart_based": cart_based[:5],  # Max 5 rule-based recommendations
        "popular": popular             # Max 5 popular items
    }

"""
=============================================================
CART SERVICE
=============================================================
Business logic for shopping cart operations.

CART RULES:
1. Each user has at most ONE active cart
2. A cart belongs to ONE restaurant at a time
3. Adding items from a different restaurant clears the old cart
4. Cart total is recalculated on every add/remove
5. Cart is deleted after successful checkout
=============================================================
"""

import uuid
from datetime import datetime, timezone
from ..database import carts_collection


def get_cart(user_id: str):
    """
    Get the current cart for a user.
    
    Args:
        user_id: The user's ID
    
    Returns:
        Cart dict or None if no cart exists
    """
    cart = carts_collection.find_one(
        {"user_id": user_id}, {"_id": 0}
    )
    return cart


def add_to_cart(user_id: str, restaurant_id: str, item_id: str,
                item_name: str, price: float, quantity: int = 1):
    """
    Add an item to the user's cart.
    
    LOGIC:
    1. Check if user already has a cart
    2. If cart exists but for a DIFFERENT restaurant → clear it
    3. If item already in cart → increase quantity
    4. If new item → append to items list
    5. Recalculate cart total
    
    Args:
        user_id: User's ID
        restaurant_id: Restaurant the item belongs to
        item_id: Menu item ID
        item_name: Name of the item
        price: Price per unit
        quantity: How many to add
    
    Returns:
        Updated cart dict
    """
    now = datetime.now(timezone.utc)
    cart = carts_collection.find_one({"user_id": user_id}, {"_id": 0})

    if cart:
        # If cart is from a different restaurant, reset it
        if cart["restaurant_id"] != restaurant_id:
            carts_collection.delete_one({"user_id": user_id})
            cart = None

    if not cart:
        # Create a brand new cart
        cart = {
            "cart_id": f"CART-{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "items": [],
            "cart_total": 0.0,
            "created_at": now,
            "updated_at": now
        }

    # Check if item already exists in cart
    item_found = False
    for item in cart["items"]:
        if item["item_id"] == item_id:
            # Item exists → increase quantity
            item["quantity"] += quantity
            item_found = True
            break

    if not item_found:
        # New item → add to cart
        cart["items"].append({
            "item_id": item_id,
            "item_name": item_name,
            "price": price,
            "quantity": quantity
        })

    # Recalculate total: sum of (price × quantity) for each item
    cart["cart_total"] = sum(
        item["price"] * item["quantity"] for item in cart["items"]
    )
    cart["updated_at"] = now

    # Upsert: insert if new, update if exists
    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": cart},
        upsert=True
    )

    return cart


def remove_from_cart(user_id: str, item_id: str):
    """
    Remove an item from the user's cart.
    
    If the cart becomes empty after removal, delete it entirely.
    
    Args:
        user_id: User's ID
        item_id: ID of the item to remove
    
    Returns:
        Updated cart dict, or None if cart not found
    """
    cart = carts_collection.find_one({"user_id": user_id}, {"_id": 0})

    if not cart:
        return None

    # Filter out the item to remove
    original_length = len(cart["items"])
    cart["items"] = [
        item for item in cart["items"]
        if item["item_id"] != item_id
    ]

    # Check if anything was actually removed
    if len(cart["items"]) == original_length:
        return None  # Item wasn't in the cart

    # If cart is now empty, delete it
    if len(cart["items"]) == 0:
        carts_collection.delete_one({"user_id": user_id})
        return {"message": "Cart is now empty and has been removed."}

    # Recalculate total
    cart["cart_total"] = sum(
        item["price"] * item["quantity"] for item in cart["items"]
    )
    cart["updated_at"] = datetime.now(timezone.utc)

    carts_collection.update_one(
        {"user_id": user_id},
        {"$set": cart}
    )

    return cart


def clear_cart(user_id: str):
    """
    Delete the user's cart entirely (used after checkout).
    
    Args:
        user_id: User's ID
    
    Returns:
        True if a cart was deleted, False otherwise
    """
    result = carts_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0

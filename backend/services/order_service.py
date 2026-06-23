"""
=============================================================
ORDER SERVICE
=============================================================
Business logic for the checkout and order creation process.

CHECKOUT FLOW:
1. Fetch the user's cart
2. Validate cart is not empty
3. Calculate pricing breakdown:
   - total_amount = sum of item prices
   - delivery_fee = flat ₹40 (configurable)
   - tax_amount = 5% of total_amount (GST)
   - discount_amount = 0 (future: coupon system)
   - final_amount = total + delivery + tax - discount
4. Create an order document
5. Clear the cart
6. Return order confirmation
=============================================================
"""

import uuid
from datetime import datetime, timezone
from database import orders_collection
from services.cart_service import get_cart, clear_cart
# FIX #13: Import constants from config instead of hardcoding them here
import config


# -------------------------------------------------------
# FIX #13: Constants now live in config.py / .env
# (DELIVERY_FEE and TAX_RATE are loaded from environment variables)
# -------------------------------------------------------
DISCOUNT_AMOUNT = 0.0   # Future: implement coupon system



def create_order(user_id: str, payment_method: str, delivery_address: str):
    """
    Convert a user's cart into a confirmed order.
    
    This is the main checkout function. It:
    1. Retrieves the cart
    2. Calculates final pricing
    3. Saves the order to MongoDB
    4. Deletes the cart
    
    Args:
        user_id: ID of the user checking out
        payment_method: How the user wants to pay
        delivery_address: Where to deliver the food
    
    Returns:
        dict: Order document on success
        None: If no cart found or cart is empty
    """
    # Step 1: Get the user's current cart
    cart = get_cart(user_id)
    if not cart or len(cart.get("items", [])) == 0:
        return None

    now = datetime.now(timezone.utc)

    # Step 2: Calculate pricing
    total_amount = cart["cart_total"]
    delivery_fee = config.DELIVERY_FEE          # FIX #13: from config/env
    tax_amount = round(total_amount * config.TAX_RATE, 2)  # FIX #13: from config/env
    discount_amount = DISCOUNT_AMOUNT
    final_amount = round(
        total_amount + delivery_fee + tax_amount - discount_amount, 2
    )


    # Step 3: Build the order document
    order = {
        "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
        "user_id": user_id,
        "restaurant_id": cart["restaurant_id"],
        "items": cart["items"],  # Snapshot of cart items
        "total_amount": total_amount,
        "delivery_fee": delivery_fee,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "payment_method": payment_method,
        "payment_status": "pending",
        "order_status": "confirmed",
        "delivery_address": delivery_address,
        "ordered_at": now,
        "delivered_at": None,
        "created_at": now,
        "updated_at": now
    }

    # Step 4: Save to database
    orders_collection.insert_one(order)

    # Step 5: Clear the cart (it's been converted to an order)
    clear_cart(user_id)

    # Remove MongoDB's internal _id before returning
    order.pop("_id", None)

    return order


def get_user_orders(user_id: str):
    """
    FIX #18: Retrieve all past orders for a user.
    
    Returns orders sorted by most recent first so the user's
    latest order always appears at the top.
    
    Args:
        user_id: The user's ID
        
    Returns:
        List of order dicts (with _id excluded)
    """
    orders = list(
        orders_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("ordered_at", -1)  # Newest first
    )
    return orders

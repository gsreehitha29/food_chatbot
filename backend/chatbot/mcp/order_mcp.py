from fastmcp import FastMCP
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# 1. Setup paths to import from backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(backend_path)

# Load environment variables from backend/.env dynamically
env_path = os.path.abspath(os.path.join(backend_path, ".env"))
load_dotenv(dotenv_path=env_path)

# 2. Import database connection and cart/order services from backend
from database import menu_collection
from services.cart_service import (
    add_to_cart as db_add_to_cart,
    get_cart as db_get_cart,
    clear_cart as db_clear_cart
)
from services.order_service import create_order as db_create_order

mcp = FastMCP("OrderMCP")

@mcp.tool()
def create_cart(user_id: str):
    """Create a new cart for user (no-op since database carts are upserted dynamically)"""
    return {"message": "Cart initialized", "user_id": user_id}


@mcp.tool()
def add_to_cart(
    user_id: str,
    item_name: str,
    quantity: int
):
    """Add item to database cart by item name"""

    # Look up item in MENU collection
    item = menu_collection.find_one(
        {"item_name": {"$regex": f"^{item_name}$", "$options": "i"}},
        {"_id": 0}
    )
    if not item:
        # try substring match
        item = menu_collection.find_one(
            {"item_name": {"$regex": item_name, "$options": "i"}},
            {"_id": 0}
        )

    if not item:
        return {
            "error": f"Item '{item_name}' not found"
        }

    # Add to DB cart
    cart = db_add_to_cart(
        user_id=user_id,
        restaurant_id=item["restaurant_id"],
        item_id=item["item_id"],
        item_name=item["item_name"],
        price=float(item["price"]),
        quantity=quantity
    )

    # Map database cart items to the format expected by the chatbot nodes
    mapped_items = []
    for i in cart.get("items", []):
        mapped_items.append({
            "item": i["item_name"],
            "quantity": i["quantity"],
            "price": i["price"],
            "total": i["price"] * i["quantity"]
        })

    return {
        "message": f"Added {quantity} x {item['item_name']} to cart.",
        "cart": mapped_items
    }


@mcp.tool()
def get_cart(user_id: str):
    """Get cart items from database"""

    cart = db_get_cart(user_id)
    if not cart:
        return {
            "items": [],
            "grand_total": 0.0
        }

    mapped_items = []
    for i in cart.get("items", []):
        mapped_items.append({
            "item": i["item_name"],
            "quantity": i["quantity"],
            "price": i["price"],
            "total": i["price"] * i["quantity"]
        })

    return {
        "items": mapped_items,
        "grand_total": cart.get("cart_total", 0.0)
    }


@mcp.tool()
def clear_cart(user_id: str):
    """Clear database cart"""

    db_clear_cart(user_id)
    return {"message": "Cart cleared"}


@mcp.tool()
def checkout_cart(
    user_id: str,
    payment_method: str = "Cash on Delivery",
    delivery_address: str = "Ordered via SpiceBot Chat"
):
    """Convert cart to a database order and clear the cart"""
    order = db_create_order(
        user_id=user_id,
        payment_method=payment_method,
        delivery_address=delivery_address
    )
    if not order:
        return {"error": "Cannot checkout: Cart is empty or not found"}
    return order


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002
    )
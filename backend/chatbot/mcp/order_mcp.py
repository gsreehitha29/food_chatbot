from fastmcp import FastMCP
from datetime import datetime

from pymongo import MongoClient

mcp = FastMCP("OrderMCP")

# simple in-memory cart (replace with Redis in production)
CARTS = {}
client = MongoClient("mongodb+srv://Cluster47062:XLxGVu26VDbfppvU@cluster47062.yhvoyo7.mongodb.net/")
db = client.chatbot
menu = db.menu

@mcp.tool()
def create_cart(user_id: str):
    """Create a new cart for user"""
    if user_id not in CARTS:
        CARTS[user_id] = []

    return {"message": "Cart created", "user_id": user_id}


@mcp.tool()
def add_to_cart(
    user_id: str,
    item_name: str,
    quantity: int
):
    """Add item to cart"""

    item = menu.find_one(
    {
        "dish_name": {
            "$regex": f"^{item_name}$",
            "$options": "i"
        }
    },
    {
        "_id": 0,
        "price": 1,
        "dish_name": 1
    }
)

    if not item:
        return {
            "error": f"{item_name} not found"
        }

    price = float(item["price"])

    if user_id not in CARTS:
        CARTS[user_id] = []

    CARTS[user_id].append({
        "item": item_name,
        "quantity": quantity,
        "price": price,
        "total": price * quantity
    })

    return {
        "message": "Item added",
        "cart": CARTS[user_id]
    }


@mcp.tool()
def get_cart(user_id: str):
    """Get cart items"""

    cart = CARTS.get(user_id, [])

    total = sum(i["total"] for i in cart)

    return {
        "items": cart,
        "grand_total": total
    }


@mcp.tool()
def clear_cart(user_id: str):
    """Clear cart"""

    CARTS[user_id] = []
    return {"message": "Cart cleared"}


import os

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("ORDER_MCP_PORT", "8002"))
    )
from fastmcp import FastMCP

mcp = FastMCP("RestaurantMenuMCP")

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from backend/.env dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_database")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
menu = db["MENU"]

@mcp.tool()
def get_categories():
    """
    Returns all available menu categories
    """
    raw_cats = list(menu.distinct("category_id"))
    friendly_cats = []
    for cat in raw_cats:
        friendly = cat.replace("CAT_", "").replace("_", " ").title()
        friendly_cats.append(friendly)
    return friendly_cats

@mcp.tool()
def get_menu_items(category: str):
    """
    Returns all items in a given category
    """
    cat_upper = category.upper().replace(" ", "_")
    cat_id = f"CAT_{cat_upper}"
    items = list(menu.find({"category_id": cat_id}, {"_id": 0}))
    if not items:
        items = list(menu.find({"category_id": {"$regex": cat_upper, "$options": "i"}}, {"_id": 0}))
    return items

@mcp.tool()
def search_menu(query: str):
    """
    Search menu items by name (case-insensitive)
    """

    return list(
        menu.find(
            {
                "item_name": {
                    "$regex": query,
                    "$options": "i"
                }
            },
            {"_id": 0}
        )
    )

@mcp.tool()
def get_item_details(item_name: str):
    """
    Get exact item details from MongoDB menu collection
    """

    item = menu.find_one(
        {
            "item_name": {
                "$regex": f"^{item_name}$",
                "$options": "i"
            }
        },
        {
            "_id": 0
        }
    )

    if not item:
        return {
            "error": "Item not found"
        }

    return item


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8011
    )
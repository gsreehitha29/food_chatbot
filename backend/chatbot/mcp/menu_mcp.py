from fastmcp import FastMCP
import os
mcp = FastMCP("RestaurantMenuMCP")

from pymongo import MongoClient

client = MongoClient("mongodb+srv://Cluster47062:XLxGVu26VDbfppvU@cluster47062.yhvoyo7.mongodb.net/")

db = client.chatbot
menu = db.menu

@mcp.tool()
def get_categories():
    """
    Returns all available menu categories
    """
    return list(menu.distinct("category"))

@mcp.tool()
def get_menu_items(category: str):
    """
    Returns all items in a given category
    """
    return list(menu.find({"category": category}))

@mcp.tool()
def search_menu(query: str):
    """
    Search menu items by dish name (case-insensitive)
    """

    return list(
        menu.find(
            {
                "dish_name": {
                    "$regex": query,
                    "$options": "i"
                }
            },
            {"_id": 0}
        )
    )

@mcp.tool()
def get_item_details(dish_name: str):
    """
    Get exact item details from MongoDB menu collection
    """

    item = menu.find_one(
        {
            "dish_name": {
                "$regex": f"^{dish_name}$",
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
@mcp.tool()
def retrieve_all_menu_items():
    results = []

    for item in menu.find():
        results.append(item)

    return results 




if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MENU_MCP_PORT", "8001"))
    )
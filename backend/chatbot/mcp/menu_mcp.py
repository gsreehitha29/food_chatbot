from fastmcp import FastMCP
import os
mcp = FastMCP("RestaurantMenuMCP")

from pymongo import MongoClient

client = MongoClient("monogodb-connection-url")
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
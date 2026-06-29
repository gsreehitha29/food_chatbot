from fastmcp import FastMCP
import gspread
import json
import uuid
from datetime import datetime

mcp = FastMCP("SheetsMCP")

import os

# Google Sheets setup
credentials_path = os.getenv("SHEETS_CREDENTIALS_PATH", "./experiment/credentials.json")
gc = gspread.service_account(
    filename=credentials_path
)

sheet = gc.open(
    "RestaurantOrders"
).sheet1
print("Google Sheets connected successfully!",sheet.title)

@mcp.tool()
def log_order(user_id: str, items: list, total: float):

    order_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []

    for item in items:
        rows.append([
            order_id,
            user_id,
            item["item"],
            item["quantity"],
            item["price"],
            item["total"],
            timestamp
        ])

    sheet.append_rows(rows)

    return {
        "order_id": order_id,
        "message": "Order saved successfully"
    }


@mcp.tool()
def get_order(order_id: str):
    """
    Fetch a specific order
    """

    rows = sheet.get_all_records()

    for row in rows:

        if str(row.get("order_id")) == str(order_id):
            return row

    return {
        "error": "Order not found"
    }


@mcp.tool()
def get_orders():
    """
    Fetch all orders
    """

    return sheet.get_all_records()


@mcp.tool()
def get_user_orders(user_id: str):
    """
    Fetch all orders of a user
    """

    rows = sheet.get_all_records()

    return [
        row
        for row in rows
        if str(row.get("user_id")) == str(user_id)
    ]


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("SHEETS_MCP_PORT", "8003"))
    )
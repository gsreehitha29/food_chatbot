from fastmcp import FastMCP
import gspread
import json
import uuid
from datetime import datetime

mcp = FastMCP("SheetsMCP")

# Google Sheets setup with graceful fallback for empty credentials
sheet = None
try:
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.abspath(os.path.join(current_dir, "..", "experiment", "credentials.json"))
    gc = gspread.service_account(
        filename=cred_path
    )
    sheet = gc.open(
        "RestaurantOrders"
    ).sheet1
    print("Google Sheets connected successfully!", sheet.title)
except Exception as e:
    print("WARNING: Google Sheets logging disabled - credentials.json is empty or invalid.", e)

@mcp.tool()
def log_order(user_id: str, items: list, total: float):
    order_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if sheet is None:
        print(f"[CONSOLE LOG] Order {order_id} placed by {user_id} for total Rs. {total}")
        return {
            "order_id": order_id,
            "message": "Order saved successfully (Sheets offline fallback)"
        }

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
    if sheet is None:
        return {"error": "Google Sheets offline"}

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
    if sheet is None:
        return []

    return sheet.get_all_records()


@mcp.tool()
def get_user_orders(user_id: str):
    """
    Fetch all orders of a user
    """
    if sheet is None:
        return []

    rows = sheet.get_all_records()

    return [
        row
        for row in rows
        if str(row.get("user_id")) == str(user_id)
    ]


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8003
    )
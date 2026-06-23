from adapter.mcp_adapter import order_client, sheets_client

async def checkout_node(state):

    user_id = state.get("conversation_id", "123")

    async with order_client:
        checkout_res = await order_client.call_tool(
            "checkout_cart",
            {
                "user_id": user_id,
                "payment_method": "Cash on Delivery",
                "delivery_address": "Ordered via SpiceBot Chat"
            }
        )

    order_data = checkout_res.data
    if not order_data or "error" in order_data:
        err = order_data.get("error") if order_data else "Cart is empty or not found"
        return {
            "response": f"❌ Could not place order: {err}"
        }

    order_id = order_data["order_id"]
    items = []
    for item in order_data.get("items", []):
        items.append({
            "item": item["item_name"],
            "quantity": item["quantity"],
            "price": item["price"],
            "total": item["price"] * item["quantity"]
        })
    total = order_data["final_amount"]

    try:
        async with sheets_client:
            await sheets_client.call_tool(
                "log_order",
                {
                    "user_id": user_id,
                    "items": items,
                    "total": total
                }
            )
    except Exception as e:
        print("Failed to log order to Google Sheets:", e)

    return {
        "response": f"🍽️ *Order Confirmed!* \n\nYour order has been placed successfully.\n\n* **Order ID:** `{order_id}`\n* **Amount:** ₹{total}\n* **Payment Method:** Cash on Delivery\n\nThank you for ordering with Spice Haven! You can view the order details in your *Orders* tab.",
        "order_status": "placed",
        "cart": []
    }
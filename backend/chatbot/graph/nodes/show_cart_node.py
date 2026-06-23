from adapter.mcp_adapter import order_client
from services.calculate_total import calculate_total
from services.llm import llm
async def summary_node(state):

    async with order_client:
        cart = await order_client.call_tool(
            "get_cart",
            {
                "user_id": state["conversation_id"]
            }
        )
    cart_items = cart.structured_content["items"]

    total = calculate_total(cart_items)

    response = llm.invoke(
        f"""
        Generate a professional order summary.

        Cart:
        {cart}

        Total:
        ₹{total}

        Include:

        Order Items
        Quantities
        Total Cost

        Ask if the user wants
        to place the order.
        """
    )

    return {
        "response": response.content,
        "total": total
    }
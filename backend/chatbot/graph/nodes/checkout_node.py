from adapter.mcp_adapter import order_client, sheets_client
from services.llm import llm


async def checkout_node(state):

    user_id = state.get("conversation_id", "123")

    # -------------------------
    # GET CART
    # -------------------------
    async with order_client:
        cart_result = await order_client.call_tool(
            "get_cart",
            {"user_id": user_id}
        )

    cart = cart_result.structured_content if hasattr(cart_result, "structured_content") else cart_result
    items = cart.get("items", [])
    total = cart.get("grand_total", 0)

    # -------------------------
    # LOG ORDER
    # -------------------------
    async with sheets_client:
        order_result = await sheets_client.call_tool(
            "log_order",
            {
                "user_id": user_id,
                "items": items,
                "total": total
            }
        )

    order_id = order_result.data["order_id"] if hasattr(order_result, "data") else "N/A"

    # -------------------------
    # LLM RESPONSE (HTML STRICT)
    # -------------------------
    SYSTEM_PROMPT = """
You are a restaurant assistant chatbot.

YOU MUST OUTPUT ONLY CLEAN HTML.

========================
RULES
========================
- Output ONLY HTML
- No Markdown
- No JSON
- No explanations
- Must be friendly and professional
- Always end with a follow-up question
"""

    USER_PROMPT = f"""
The order has been successfully placed.

Order ID: {order_id}
Total Amount: ₹{total}

Items:
{items}

Generate a friendly HTML confirmation message.
"""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])

    text = (
        response.content
        if isinstance(response.content, str)
        else response.content[0]["text"]
    )

    html_output = f"""
<h2>🎉 Order Placed Successfully</h2>

<p><strong>Order ID:</strong> {order_id}</p>

<p><strong>Total Paid:</strong> ₹{total}</p>

<p>{text}</p>

<p>Would you like to order something else? 🍽️</p>
"""

    return {
        **state,
        "response": html_output,
        "order_id": order_id,
        "cart": [],
        "last_action": "checkout"
    }
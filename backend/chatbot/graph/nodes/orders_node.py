from adapter.mcp_adapter import order_client
from services.llm import llm


async def order_node(state):

    item = state["selected_item"]
    qty = state["quantity"]

    async with order_client:
        result = await order_client.call_tool(
            "add_to_cart",
            {
                "user_id": state.get("conversation_id", "123"),
                "item_name": item,
                "quantity": qty,
            }
        )

    result_text = result.content[0].text if hasattr(result, "content") else str(result)

    SYSTEM_PROMPT = """
You are a restaurant assistant chatbot.

You MUST respond ONLY in clean HTML.

========================
RULES
========================
- Output ONLY HTML
- No markdown
- No JSON
- No tables in markdown
- No explanations
- Use proper HTML tags only
- Always end with a question to the user
"""

    USER_PROMPT = f"""
A customer has added an item to the cart.

Item: {item}
Quantity: {qty}

Backend cart response:
{result_text}

Generate a friendly HTML confirmation message.
Make it clean and user-friendly.
"""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])

    response_text = (
        response.content
        if isinstance(response.content, str)
        else response.content[0]["text"]
    )

    return {
        **state,
        "response": response_text,
        "cart": result_text,
        "last_action": "add_to_cart"
    }
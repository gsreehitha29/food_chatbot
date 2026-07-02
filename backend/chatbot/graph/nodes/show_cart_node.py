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

    SYSTEM_PROMPT = """
You are a restaurant assistant chatbot.

YOU MUST OUTPUT ONLY VALID HTML.

========================
STRICT RULES
========================
- Output ONLY HTML
- NEVER use Markdown
- NEVER use tables in Markdown format
- NEVER use | pipe tables
- Use proper HTML tags only
- Use <table> if needed
- Always end with a question
"""

    USER_PROMPT = f"""
Create a clean order summary in HTML.

Cart items:
{cart_items}

Total amount:
₹{total}

Requirements:
- Show items in a HTML <table>
- Columns: Item | Quantity | Price | Total
- Add a final row for GRAND TOTAL
- Make it visually clean and simple
- Add emojis 🍽️🛒
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

    html_output = f"""
<h2>🧾 Order Summary</h2>

{response_text}

<p><strong>Grand Total: ₹{total}</strong></p>

<p>Would you like to proceed with placing the order? 🍽️</p>
"""

    return {
        **state,
        "response": html_output,
        "total": total,
        "cart": cart_items,
        "last_action": "summary"
    }
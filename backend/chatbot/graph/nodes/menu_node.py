from adapter.mcp_adapter import menu_client
from services.llm import llm


async def menu_items_node(state):

    async with menu_client:
        items = await menu_client.call_tool(
            "get_menu_items",
            {
                "category": state["current_category"]
            }
        )

    items = items.content[0].text
    print("Menu items from MCP:", items)

    SYSTEM_PROMPT = """
You are a professional restaurant assistant chatbot.

You must present menu items in a clean, structured and attractive format.

========================
OUTPUT FORMAT (STRICT)
========================
- Output ONLY HTML
- No Markdown
- No JSON
- No explanations

========================
RENDERING RULES
========================
- Use <h2> for category title
- Use <ul><li> for items
- Use <strong> for item name
- Show price 💰 and rating ⭐ clearly
- Keep it clean and readable
- End with a question asking what the user wants to order
"""

    USER_PROMPT = f"""
Category selected:
{state['current_category']}

Menu items from database:
{items}

Format this into the required HTML structure.

Make it visually appealing and easy to read.
"""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])

    return {
        **state,
        "response": response.content,
        "waiting_for": "item_selection",
        "menu_items": items
    }
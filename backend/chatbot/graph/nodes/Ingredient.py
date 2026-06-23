from adapter.mcp_adapter import menu_client
from services.extract_item_name import extract_item_name
from services.llm import llm
async def ingredient_node(state):

    item = extract_item_name(
        state["user_message"]
    )
    item_name = item.item_name if item and hasattr(item, "item_name") else state["user_message"]

    async with menu_client:
        details = await menu_client.call_tool(
            "get_item_details",
            {
                "item_name": item_name
            }
        )

    prompt = f"""
You are a restaurant assistant.

Item Details:
{details}

Create a friendly response.

Include:
- Item name
- Description
- Ingredients (if available)
- Veg/Non Veg
- Calories
- Spice level
- Price

Keep it conversational.
"""

    response = llm.invoke(prompt)

    return {
        "response": response.content
    }
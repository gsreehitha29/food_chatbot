
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


    response = llm.invoke(
        f"""
        Category:
        {state['current_category']}

        Items:
        {items}

        Format nicely.

        Show:
        - Item name
        - Price
        - Rating

        Then ask the user
        which item they would like.
        """
    )
 

    return {
        "response": response.content,
        
    }
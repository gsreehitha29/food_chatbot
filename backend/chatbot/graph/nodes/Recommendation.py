from adapter.mcp_adapter import menu_client
from services import llm
async def recommendation_node(state):

    async with menu_client:
        dishes = await menu_client.call_tool(
            "search_menu",
            {
                "query": state["user_message"]
            }
        )

    response = llm.invoke(
        f"""
        User request:
        {state["user_message"]}

        Matching dishes:
        {dishes}

        Recommend 3 dishes.

        Explain briefly why.
        """
    )

    return {
        "response": response.content
    }
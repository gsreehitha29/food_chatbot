import json

from adapter.mcp_adapter import menu_client
from services.llm import llm
async def browse_menu_node(state):

    async with menu_client:
        categories = await menu_client.call_tool(
            "get_categories",
            {}
        )
        
    categories = categories.content[0]
    print("Categories from MCP:", categories.text)
  
    response = llm.invoke(
        f"""
        Categories:

        {categories}

        Present them in a friendly restaurant style.
        Ask the customer which category
        they would like to explore.
        """
    )
    

    return {
        **state,
        "response": response.content,
        "waiting_for": "category" ,
        "categories": categories.text
    }
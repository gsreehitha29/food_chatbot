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

    prompt = f"""
    The customer added an item to their cart.

    Item: {item}
    Quantity: {qty}

    Cart update result:
    {result}

    Generate a friendly restaurant chatbot response.
    Mention the item and quantity added.
    Ask the customer what they would like to do next.
    """

    response = llm.invoke(prompt).content
   

    return {
        "response": response,
        "cart": result
    }
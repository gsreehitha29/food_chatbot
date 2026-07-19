from ...adapter.mcp_adapter import order_client
from ...services.llm import llm
from backend.services.cart_service import add_to_cart
from ...adapter.mcp_adapter import menu_client
import json
async def order_node(state):

    item = state["selected_item"]
    qty = state["quantity"]
    user_id = state.get("conversation_id", "123")
    async with order_client:
        result = await order_client.call_tool(
            "add_to_cart",
            {
                "user_id": user_id,
                "item_name": item,
                "quantity": qty,
            }
        )
    async with menu_client:
        menu_result = await menu_client.call_tool(
            "search_menu",
            {
                "query": item
                
            }
        )
    
 

    print("Menu result:", menu_result)

# Parse MCP response
    menu_items = []

    if menu_result.content:
        menu_items = json.loads(menu_result.content[0].text)

    if not menu_items:
        raise ValueError(f"Menu item '{item}' not found.")

    menu_item = menu_items[0]

    restaurant_id = menu_item["restaurant_id"]
    price = menu_item["price"]
    item_id = menu_item["dish_id"]   # <-- Your MongoDB field is dish_id

    add_to_cart(
    user_id=user_id,
    restaurant_id=restaurant_id,
    item_id=item_id,
    item_name=item,
    price=price,
    quantity=qty,
)
    print(f"Added {qty} of {item} to cart for user {user_id}.")
    print(result)
    result_text = result.content[0].text if hasattr(result, "content") else str(result)

    SYSTEM_PROMPT = """
You are a restaurant ordering assistant.

Return ONLY valid HTML.

Rules:
- Do not use Markdown.
- Do not use JSON.
- Do not explain anything.
- Do not wrap the response inside ```html```.
- Use ONLY inline CSS.
- Do NOT use <style> tags.
- Do NOT use JavaScript.
- Follow the HTML template exactly.
- Always end by asking the customer whether they want to add more items or proceed to checkout.
"""
    USER_PROMPT = f"""
You are filling an HTML template.

Replace ONLY these placeholders:
- {{ITEM_NAME}} -> {item}
- {{QUANTITY}} -> {qty}

Do NOT modify anything else.

Return EXACTLY this HTML.

<div style="background:#1f2937;border:1px solid #374151;border-radius:12px;padding:20px;color:#ffffff;font-family:Arial,sans-serif;">

  <h2 style="margin:0 0 20px 0;padding:0;background:transparent;color:#22c55e;font-size:24px;font-weight:bold;border:none;">
    ✅ Item Added to Cart
  </h2>

  <div style="background:#111827;border-radius:10px;padding:18px;border-left:5px solid #22c55e;">

    <h3 style="margin:0 0 12px 0;padding:0;background:transparent;color:#fbbf24;font-size:22px;font-weight:700;border:none;">
      🍽️ {{ITEM_NAME}}
    </h3>

    <p style="margin:8px 0;padding:0;background:transparent;">
      <strong style="color:#fbbf24;background:transparent;">Quantity:</strong>
      {{QUANTITY}}
    </p>

    <p style="margin:8px 0;padding:0;background:transparent;">
      <strong style="color:#fbbf24;background:transparent;">Status:</strong>
      Successfully added to your cart.
    </p>

  </div>

  <p style="margin-top:18px;line-height:1.6;">
    Your cart has been updated successfully. You can continue browsing the menu or proceed to checkout.
  </p>

  <p style="margin-top:18px;font-weight:bold;color:#fbbf24;">
    🛒 Would you like to add another item or place your order?
  </p>

</div>

Rules:
1. Return ONLY the HTML above.
2. Replace only {{ITEM_NAME}} and {{QUANTITY}}.
3. Do not add or remove any HTML tags.
4. Do not add Markdown.
5. Do not add ```html.
6. Do not explain anything.
7. Do not append any extra text before or after the HTML.
8. Do not modify the inline CSS.
"""
#     response_text = f"""
# <div style="background:#1f2937;border:1px solid #374151;border-radius:12px;padding:20px;color:#ffffff;font-family:Arial,sans-serif;max-width:550px;">

#   <div style="background:#0f172a;padding:14px 18px;border-radius:10px;margin-bottom:18px;">
#     <h2 style="margin:0;color:#22c55e;font-size:24px;font-weight:bold;">
#       ✅ Item Added to Cart
#     </h2>
#   </div>

#   <table style="width:100%;border-collapse:collapse;background:#111827;border-radius:10px;overflow:hidden;">

#     <tr style="background:#1e293b;">
#       <th style="padding:12px;text-align:left;color:#fbbf24;">Item</th>
#       <th style="padding:12px;text-align:center;color:#fbbf24;">Quantity</th>
#       <th style="padding:12px;text-align:center;color:#fbbf24;">Status</th>
#     </tr>

#     <tr>
#       <td style="padding:14px;border-top:1px solid #374151;">🍽️ {item}</td>
#       <td style="padding:14px;text-align:center;border-top:1px solid #374151;">{qty}</td>
#       <td style="padding:14px;text-align:center;border-top:1px solid #374151;color:#22c55e;font-weight:bold;">
#         ✓ Added
#       </td>
#     </tr>

#   </table>

#   <div style="margin-top:18px;padding:14px;background:#0f172a;border-radius:8px;line-height:1.6;">
#     Your cart has been updated successfully. You can continue browsing our menu or proceed to checkout whenever you're ready.
#   </div>

#   <div style="margin-top:18px;font-size:17px;font-weight:bold;color:#fbbf24;">
#     🛒 Would you like to add another item or place your order?
#   </div>

# </div>
# """

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
    

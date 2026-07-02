from services.llm import llm
from pydantic import BaseModel
from typing import Literal


class Intent(BaseModel):
    intent: Literal[
        "browse_menu",
        'category_selected',
        "preference",
        "ingredients_info",
        "popular_items",
        "place_order",
        "checkout",
        "general"
    ]

    category: str | None = None
    selected_item: str | None = None

    quantity: int | None = None
    price: float | None = None


structured_llm = llm.with_structured_output(Intent)

    

def detect_intent(user_message: str):

  # print("Intent Router Loaded")
  prompt = f"""
You are a STRICT intent classification system for a restaurant chatbot.

You MUST classify the user message into EXACTLY ONE intent.

Do NOT explain anything.
Do NOT add extra text.
Return structured output only.

---

INTENTS AND DEFINITIONS:

1. browse_menu

User wants to START browsing the restaurant menu.
This means the system should show ONLY MENU CATEGORIES first.

This intent does NOT include showing food items.
It is ONLY the first step of exploration.

AVAILABLE CATEGORIES:
- Pizza
- Starters
- Main Course
- Rice & Biryani

---

FLOW RULE:
After browse_menu → system must wait for category_selected

---

RULES:
- Use ONLY when user asks for menu or food options in general
- NEVER use if user mentions a category or dish
- This is ALWAYS the ENTRY point of browsing flow

---

EXAMPLES:

User: "menu"
→ browse_menu

User: "show menu"
→ browse_menu

User: "what do you have"
→ browse_menu

User: "I want food"
→ browse_menu

User: "show me options"
→ browse_menu

---

DO NOT USE:

User: "pizza"
→ category_selected ❌

User: "starters"
→ category_selected ❌

User: "paneer tikka"
→ place_order ❌

2. category_selected

User selects a MENU CATEGORY after browsing.

This intent happens ONLY AFTER browse_menu.

After this intent:
👉 SHOW ITEMS INSIDE THE SELECTED CATEGORY

AVAILABLE CATEGORIES:
- Pizza
- Starters
- Main Course
- Rice & Biryani

---

FLOW RULE:
browse_menu → category_selected → show menu items → wait for item selection

---

RULES:
- If user mentions a category → category_selected
- If user is continuing after browse_menu → category_selected
- Must extract exact category name
- This intent ALWAYS triggers fetching items inside that category

---

EXAMPLES:

User: "pizza"
→ category_selected (Pizza)

User: "Pizza"
→ category_selected (Pizza)

User: "show pizza"
→ category_selected (Pizza)

User: "starters"
→ category_selected (Starters)

User: "what in starters"
→ category_selected (Starters)

User: "main course options"
→ category_selected (Main Course)

User: "rice biryani"
→ category_selected (Rice & Biryani)

---

IMPORTANT BEHAVIOR:

When category_selected is triggered:
→ DO NOT show categories again
→ SHOW ONLY ITEMS in that category
---

3. preference
User wants food based on preference or constraints.

EXAMPLES:
User: "something spicy"
→ find_dishes

User: "veg food under 200"
→ find_dishes

User: "low calorie meals"
→ find_dishes

User: "chicken dishes"
→ find_dishes

---

4. ingredients_info
User asks about ingredients, allergens, nutrition, or recipe details.

EXAMPLES:
User: "what is in paneer tikka"
→ ingredients_info

User: "calories in pizza"
→ ingredients_info

User: "is this veg"
→ ingredients_info

User: "does it contain gluten"
→ ingredients_info

---

5. place_order

User wants to select items, add items to cart, or order food.

EXAMPLES:

User: "Paneer Tikka"
→ place_order

User: "1 Paneer Tikka"
→ place_order

User: "add pizza to cart"
→ place_order

User: "I want 2 burgers"
→ place_order

User: "add one more pepperoni pizza"
→ place_order

User: "order pav bhaji"
→ place_order

RULES:
- User is choosing a dish
- User is adding food to cart
- User mentions quantity
- User mentions a dish name
- User wants to modify the cart by adding items

---

6. checkout

User wants to finalize the order and complete purchase.

This intent should ONLY be used when the user wants to place the final order.

EXAMPLES:

User: "checkout"
→ checkout

User: "confirm order"
→ checkout

User: "place my order"
→ checkout

User: "proceed to payment"
→ checkout

User: "complete order"
→ checkout

User: "I'm done"
→ checkout

User: "finish order"
→ checkout

User: "pay now"
→ checkout

User: "submit order"
→ checkout

RULES:
- User is NOT selecting food
- User is NOT browsing menu
- User wants to finalize the cart
- User wants payment/order confirmation
- Trigger only after items are already in cart

---

8. summary

User wants to view the cart or order summary.

EXAMPLES:

User: "show cart"
→ summary

User: "view cart"
→ summary

User: "what have I ordered"
→ summary

User: "cart"
→ summary

User: "order summary"
→ summary

User: "show my order"
→ summary

---

9. general

Anything unrelated, conversational, or unclear.

EXAMPLES:

User: "hello"
→ general

User: "hi"
→ general

User: "ok"
→ general

User: "thanks"
→ general

User: "random text"
→ general
---

CRITICAL RULES:

- If input is ONLY a category name → category_selected
- If input is ONLY a dish name → place_order
- If input contains quantity → place_order
- NEVER confuse category and dish
- NEVER guess missing context
- Always choose the MOST specific intent

---

USER MESSAGE:
{user_message}

Return structured JSON only.
"""
  
  result = structured_llm.invoke(prompt)
  # print("Intent Detection Result:", result)

  return result
from langgraph.graph import StateGraph, END

from graph.nodes.intent_node import intent_router
from graph.nodes.browse_category import browse_menu_node
from graph.nodes.menu_node import menu_items_node
from graph.nodes.Recommendation import recommendation_node
from graph.nodes.Ingredient import ingredient_node
from graph.nodes.orders_node import order_node
from graph.nodes.show_cart_node import summary_node
from graph.nodes.checkout_node import checkout_node
from graph.nodes.general_node import general_node


from graph.states import RestaurantState

builder = StateGraph(RestaurantState)

# Nodes
builder.add_node("intent_router", intent_router)

builder.add_node("browse_menu", browse_menu_node)

builder.add_node("menu", menu_items_node)

builder.add_node("recommendation", recommendation_node)

builder.add_node("ingredient", ingredient_node)

builder.add_node("add_to_cart", order_node)

builder.add_node("order_summary", summary_node)

builder.add_node("checkout", checkout_node)

builder.add_node("general", general_node)
# Entry point
builder.set_entry_point("intent_router")


def route_intent(state):
    intent = state["intent"]
    print("Routing intent:", intent)
    if intent in ["find_dishes", "popular_items"]:
        return "recommendation"
    if intent == "ingredients_info":
        return "ingredient"
    if intent == "summary":
        return "summary"
    return intent


builder.add_conditional_edges(
    "intent_router",
    route_intent,
    {
        "browse_menu": "browse_menu",
        "category_selected": "menu",
        "recommendation": "recommendation",
        "ingredient": "ingredient",
        "place_order": "add_to_cart",
        "summary": "order_summary",
        "checkout": "checkout",
        "general": "general"
    }
)

# Browse Menu → Show Categories
# Then user selects category → Menu Node


# Optional ordering flow
builder.add_edge("add_to_cart", "order_summary")

builder.add_edge("browse_menu", END)
builder.add_edge("menu", END)

builder.add_edge("recommendation", END)

builder.add_edge("ingredient", END)
builder.add_edge("checkout", END)

builder.add_edge("order_summary", END)
builder.add_edge("general", END)

graph = builder.compile()
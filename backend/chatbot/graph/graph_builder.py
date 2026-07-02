from langgraph.graph import StateGraph, END

from graph.nodes.intent_node import intent_router
from graph.nodes.browse_category import browse_menu_node
from graph.nodes.menu_node import menu_items_node
from graph.nodes.Recommendation import recommendation_node
from graph.nodes.Ingredient import ingredient_node
from graph.nodes.orders_node import order_node
from graph.nodes.show_cart_node import summary_node
from graph.nodes.checkout_node import checkout_node
from graph.nodes.preference import preference_node
from graph.nodes.retrieve_node import retrieve_node
from graph.nodes.context_node import context_node
from langgraph.checkpoint.memory import InMemorySaver 

from graph.states import RestaurantState

builder = StateGraph(RestaurantState)

# Nodes
builder.add_node("intent_router", intent_router)

builder.add_node("browse_menu", browse_menu_node)

builder.add_node("menu", menu_items_node)

builder.add_node("preference", preference_node)

builder.add_node("recommendation", recommendation_node)

builder.add_node("ingredient", ingredient_node)

builder.add_node("add_to_cart", order_node)

builder.add_node("order_summary", summary_node)

builder.add_node("checkout", checkout_node)

builder.add_node("retrieve",retrieve_node)

builder.add_node("context", context_node)
# Entry point
builder.set_entry_point("intent_router")


def route_intent(state):
    print("Routing intent:", state["intent"])
    return state["intent"]


builder.add_conditional_edges(
    "intent_router",
    route_intent,
    {
        "browse_menu": "browse_menu",
        "category_selected": "menu",
        "recommendation": "recommendation",
        "preference":"preference",
        "ingredient": "ingredient",
        "place_order": "add_to_cart",
        "summary": "order_summary",
        "checkout": "checkout",
        "general":END
        
    }
)




# Optional ordering flow
builder.add_edge("add_to_cart", "order_summary")
builder.add_edge("preference", "context")
builder.add_edge("context", "retrieve")

builder.add_edge(
    "retrieve",
    "recommendation"
)

builder.add_edge(
    "recommendation",
    END
)
builder.add_edge("browse_menu", END)
builder.add_edge("menu", END)


builder.add_edge("ingredient", END)
builder.add_edge("checkout", END)

builder.add_edge("order_summary", END)
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

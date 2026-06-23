from services.intent_router import detect_intent

def intent_router(state):

    result = detect_intent(state["user_message"])
    
   
    return {
        **state,
        "intent": result.intent,
        "current_category": result.category,
        "selected_item": result.selected_item,
        "quantity": result.quantity or 1,

        
    }
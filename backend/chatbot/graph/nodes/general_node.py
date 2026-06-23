from services.llm import llm

async def general_node(state):
    history = state.get("history", [])
    
    # Format chat history for context
    history_str = ""
    for msg in history[-5:]:  # limit context to last 5 messages
        role = "Customer" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""
You are SpiceBot, a friendly and helpful AI assistant for Spice Haven restaurant.
Answer the customer's message politely and conversationally.
Keep your answer relatively brief (1-3 sentences) unless they ask for details.

Conversation History:
{history_str}
Customer: {state["user_message"]}

Assistant:"""

    response = llm.invoke(prompt)
    
    return {
        "response": response.content
    }

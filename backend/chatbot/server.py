import asyncio
import traceback
import socketio
from fastapi import FastAPI
from pydantic import BaseModel
from services.llm import llm
from graph.graph_builder import graph

app = FastAPI()

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

socket_app = socketio.ASGIApp(sio, app)

conversations = {}


class ChatRequest(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"message": "Chatbot server running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    response = llm.invoke(request.message)
    return {
        "user_message": request.message,
        "bot_message": response.content
    }


@sio.event
async def connect(sid, environ):

    await sio.emit(
        "bot_message",
        {
            "message": "🍽️ Welcome to Spice Haven!\n\nI'm SpiceBot, your personal dining assistant."
        },
        room=sid
    )

    await sio.emit(
        "bot_message",
        {
            "message": """I can help you:
• Browse our menu
• Find dishes based on your preferences
• Check ingredients
• Recommend items
• Assist with placing an order

What are you craving today?
"""
        },
        room=sid
    )


@sio.event
async def user_message(sid, data):

    conversation_id = data.get("conversation_id")
    user_text = data.get("message")

    if not conversation_id:
        await sio.emit(
            "bot_message",
            {"message": "conversation_id missing"},
            room=sid
        )
        return

    # Initialize state
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "history": [],
            "cart": [],
            "current_category": None
        }

    try:
        state = {
            "user_message": user_text,
            "conversation_id": conversation_id,
            "history": conversations[conversation_id]["history"],
            "cart": conversations[conversation_id]["cart"],
            "current_category": conversations[conversation_id]["current_category"]
        }

        result = await graph.ainvoke(state)

        print("GRAPH RESULT:")
        print(result)

        response = result.get("response", "")

        if result.get("order_status") == "placed":
            conversations[conversation_id]["cart"] = []
            conversations[conversation_id]["current_category"] = None
        else:
            if result.get("cart") is not None:
                conversations[conversation_id]["cart"] = result["cart"]

            if result.get("current_category") is not None:
                conversations[conversation_id]["current_category"] = result["current_category"]

        conversations[conversation_id]["history"].append({
            "role": "user",
            "content": user_text
        })

        conversations[conversation_id]["history"].append({
            "role": "assistant",
            "content": response
        })


        for token in response.split():
            await sio.emit(
                "bot_stream",
                {"token": token + " "},
                room=sid
            )
            await asyncio.sleep(0.03)

        await sio.emit("bot_stream_end", {}, room=sid)

    except Exception as e:
        print("Error processing message:", e)
        traceback.print_exc()

        await sio.emit(
            "bot_message",
            {"message": str(e)},
            room=sid
        )


@sio.event
async def disconnect(sid):
    print("User disconnected:", sid)
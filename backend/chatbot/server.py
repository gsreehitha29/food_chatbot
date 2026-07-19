import os
import asyncio
import traceback
import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .services.llm import llm
from .graph.graph_builder import graph
from .services.location_service import get_city
from contextlib import asynccontextmanager
from .tools.build_index import build_index   # adjust path

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== Server startup ===")
    try:
        await build_index()
        print("=== FAISS index created ===")
    except Exception as e:
        import traceback
        print("Error building FAISS index:")
        traceback.print_exc()
    yield

app = FastAPI(lifespan=lifespan)


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
    html_path = "client/client.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
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
    welcome_message1="""
    <h2>🍽️ Welcome to Spice Haven</h2>

    <p>I'm <strong>SpiceBot</strong>, your personal dining assistant.</p>"""

    welcome_message2 = """
    <p>I can help you:</p>

    <ul>
        <li>🍽️ Browse our menu</li>
        <li>🍕 Find dishes based on your preferences</li>
        <li>🥗 Check ingredients</li>
        <li>🍛 Recommend items</li>
        <li>🛒 Assist with placing an order</li>
    </ul>

    <p><strong>What are you craving today? 🍛</strong></p>
    """

    await sio.emit(
        "bot_message",
        {"message": [welcome_message1]},
        room=sid
    )
    await sio.emit(
        "bot_message",
        {"message": [welcome_message2]},
        room=sid
    )


@sio.event
async def user_message(sid, data):
    

    location = data.get("location")

    

    conversation_id = data.get("conversation_id")
    user_text = data.get("message")
    location = data.get("location", {})

    if not conversation_id:
        await sio.emit(
            "bot_message",
            {"message": "conversation_id missing"},
            room=sid
        )
        return

    if conversation_id not in conversations:
        conversations[conversation_id] = {
        "history": [],
        "cart": [],
        "current_category": None,
        "location": location
    }
    city = get_city(location)
    
    conversations[conversation_id]["location"] = location
    conversations[conversation_id]["location_name"] = city

    try:
        state = {
    "user_message": user_text,
    "conversation_id": conversation_id,
    "history": conversations[conversation_id]["history"],
    "cart": conversations[conversation_id]["cart"],
    "current_category": conversations[conversation_id]["current_category"],

    "location": conversations[conversation_id]["location"],
    "location_name": conversations[conversation_id]["location_name"]
}
        

        result = await graph.ainvoke(state,{"configurable": {"thread_id": "{conversation_id}"}})

        response = result.get("response", "")

        # Normalize response
        if isinstance(response, list):
            response_text = response[0].get("text", "")
        elif isinstance(response, dict):
            response_text = response.get("text", "")
        else:
            response_text = str(response)

        # -----------------------------
        # Update conversation state
        # -----------------------------
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
            "content": response_text
        })

        # -----------------------------
        # print(conversations[conversation_id]["history"])


        buffer = ""
        tokens = response_text.split(" ")

        for token in tokens:
            buffer += token + " "

            await sio.emit(
        "bot_stream",
        {"token": token + " "},   # ONLY NEW TOKEN
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
#!/bin/bash

# Go to the project root (food_chatbot)
cd "$(dirname "$0")/../.."

cleanup() {
    echo "Shutting down background services..."
    kill $MENU_PID $ORDER_PID $FAQ_PID 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Starting MCP servers..."

# Start Menu MCP
./backend/chatbot/myenv/bin/python backend/chatbot/mcp/menu_mcp.py &
MENU_PID=$!

# Start Order MCP
./backend/chatbot/myenv/bin/python backend/chatbot/mcp/order_mcp.py &
ORDER_PID=$!

# Start FAQ MCP
./backend/chatbot/myenv/bin/python backend/chatbot/mcp/faq_mcp.py &
FAQ_PID=$!

# Give MCP servers time to start
sleep 3

echo "Building FAISS index..."

./backend/chatbot/myenv/bin/python -m backend.chatbot.tools.build_index

if [ $? -ne 0 ]; then
    echo "Failed to build FAISS index."
    exit 1
fi

echo "Starting main chatbot server..."

./backend/chatbot/myenv/bin/uvicorn \
    backend.chatbot.server:socket_app \
    --host 0.0.0.0 \
    --port 8005
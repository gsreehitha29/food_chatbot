#!/bin/bash

# Function to clean up background processes
cleanup() {
    echo "Shutting down background services..."
    kill $MENU_PID $ORDER_PID $SHEETS_PID $FAQ_PID 2>/dev/null || true
}

# Trap termination signals to ensure cleanup runs
trap cleanup EXIT INT TERM

echo "Starting MCP servers..."

# Start menu MCP (Port 8001)
python mcp/menu_mcp.py &
MENU_PID=$!

# Start order MCP (Port 8002)
python mcp/order_mcp.py &
ORDER_PID=$!

# Start sheets MCP (Port 8003)
python mcp/sheet_mcp.py &
SHEETS_PID=$!

# Start faq MCP (Port 8004)
python mcp/faq_mcp.py &
FAQ_PID=$!

echo "Starting main chatbot server..."
# Run the main server in the foreground
uvicorn server:socket_app --host 0.0.0.0 --port 8005

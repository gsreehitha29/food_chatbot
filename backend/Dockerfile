FROM python:3.11-slim

WORKDIR /app

# Install system utilities needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chatbot dependencies
COPY chatbot/requirement.txt chatbot/requirement.txt
RUN pip install --no-cache-dir -r chatbot/requirement.txt

COPY . .

# Make the chatbot startup script executable
RUN chmod +x chatbot/start.sh

# Backend API (8000) + MCP servers (8001-8004) + Chatbot Socket.IO (8005)
EXPOSE 8000 8001 8002 8003 8004 8005

# Start chatbot services in background, then run the main backend server
CMD bash -c "cd /app/chatbot && bash start.sh & cd /app && uvicorn main:app --host 0.0.0.0 --port 8000"

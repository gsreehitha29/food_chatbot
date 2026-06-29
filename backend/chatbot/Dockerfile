FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for building native extension packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt

COPY . .

# Make the startup script executable
RUN chmod +x start.sh

# MCP servers (8001-8004) + main chatbot Socket.IO server (8005)
EXPOSE 8001 8002 8003 8004 8005

CMD ["bash", "start.sh"]

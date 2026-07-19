import os
from fastmcp import Client

menu_client = Client(os.getenv("MENU_MCP_URL", "http://127.0.0.1:8001/mcp"))
order_client = Client(os.getenv("ORDER_MCP_URL", "http://127.0.0.1:8002/mcp"))
faq_client = Client(os.getenv("FAQ_MCP_URL", "http://127.0.0.1:8004/mcp"))

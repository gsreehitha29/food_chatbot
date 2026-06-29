
from adapter.mcp_adapter import menu_client
from services.llm import llm

async def browse_menu_node(state):

  
    async with menu_client:
        categories = await menu_client.call_tool(
            "get_categories",
            {}
        )

    categories = categories.content[0].text
    print("Categories from MCP:", categories)

    SYSTEM_PROMPT = """
You are a restaurant assistant chatbot.

You must display menu categories in a beautiful HTML UI.

========================
OUTPUT FORMAT (STRICT)
========================
- Output ONLY HTML
- No Markdown
- No JSON
- No explanations

========================
RENDERING RULES
========================
- Use <h2> for title
- Use <ul><li> for categories
- Use <strong> for category names
- Add emojis 🍽️🍕🍛🥗
- Keep it clean and user friendly
- Always end with a question

========================
EXAMPLE STYLE
========================

<h2>🍽️ Welcome to Our Restaurant</h2>

<p>Here are our available categories:</p>

<ul>
  <li><strong>Starters</strong> 🍢</li>
  <li><strong>Pizza</strong> 🍕</li>
</ul>

<p><strong>Which category would you like to explore?</strong></p>
"""

    USER_PROMPT = f"""
Use the following menu categories from the database:

{categories}

Format them into the HTML style described in the system prompt.
Make it visually appealing and user friendly.
"""

  
    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])

    return {
        **state,
        "response": response.content,   
        "waiting_for": "category",
        "categories": categories
    }
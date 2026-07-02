from services.llm import llm
from services.ranking_service import rank_dishes
from services.preference_db import get_preferences


async def recommendation_node(state):

    # Load user preferences from MongoDB if not already in state
    preferences = state.get("user_preferences")

    if preferences is None:
        user_id = state["conversation_id"]  # Use state["user_id"] if available
        preferences = await get_preferences(user_id)

    # Update state
    state["user_preferences"] = preferences

    # Rank candidate dishes
    dishes = state.get("candidate_dishes", [])
    ranked_dishes = rank_dishes(dishes, state)

    # Build menu context
    context = "\n\n".join(
        doc.page_content for doc in ranked_dishes
    )

    SYSTEM_PROMPT = """
YOU ARE A STRICT HTML GENERATOR.

ABSOLUTE RULES:
- Output ONLY valid HTML
- DO NOT write any explanation
- DO NOT use Markdown
- DO NOT include text outside HTML tags
- If you fail, output will be rejected.
"""

    USER_PROMPT = f"""
Generate restaurant recommendations in HTML format.

USER DATA:
- Preferences: {preferences}
- City: {state.get('location_name')}
- Weather: {state.get('weather')}
- Time: {state.get('time_of_day')}

MENU CONTEXT:
{context}

OUTPUT FORMAT (MUST FOLLOW EXACTLY):

<div class="recommendations">

  <h2>🍽️ Recommended Dishes</h2>

  <div class="card">
    <h3>Dish Name</h3>
    <p><strong>Reason:</strong> ...</p>
  </div>

  <div class="card">
    <h3>Dish Name</h3>
    <p><strong>Reason:</strong> ...</p>
  </div>

  <div class="card">
    <h3>Dish Name</h3>
    <p><strong>Reason:</strong> ...</p>
  </div>

  <p>👉 What would you like to order?</p>

</div>

IMPORTANT:
- Recommend dishes based on:
  1. User preferences
  2. Weather
  3. Time of day
  4. Available menu items

- Recommend ONLY dishes present in MENU CONTEXT.
- Return EXACTLY 3–5 recommendation cards.
- Do NOT include any text outside the HTML.
"""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    return {
        **state,
        "user_preferences": preferences,
        "response": response.content,
    }
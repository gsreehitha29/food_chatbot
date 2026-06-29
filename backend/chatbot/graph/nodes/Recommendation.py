from services.llm import llm
from services.ranking_service import rank_dishes


async def recommendation_node(state):

    dishes = state.get("candidate_dishes", [])

    ranked_dishes = rank_dishes(dishes, state)

    context = "\n\n".join(
        doc.page_content for doc in ranked_dishes
    )

    SYSTEM_PROMPT = """
YOU ARE A STRICT HTML GENERATOR.

ABSOLUTE RULES:
- Output ONLY valid HTML
- DO NOT write any explanation
- DO NOT use Markdown (no ###, **, -, *)
- DO NOT include text outside HTML tags
- If you fail, output will be rejected
"""

    USER_PROMPT = f"""
Generate restaurant recommendations in HTML format.

USER DATA:
- Preferences: {state.get('user_preferences')}
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
- Return EXACTLY 3–5 cards
- No extra text
"""

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT)
    ])
    print(response)

    return {
        **state,
        "response": response.content
    }
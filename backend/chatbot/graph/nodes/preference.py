from services.preference import extract_preferences
from services.preference_db import save_preferences
async def preference_node(state):

    user_id = state["conversation_id"]

    extracted = await extract_preferences(state["user_message"])
    new_preferences = extracted.model_dump(exclude_none=True)

    merged_preferences = await save_preferences(
        user_id,
        new_preferences
    )

    return {
        **state,
        "user_preferences": merged_preferences
    }
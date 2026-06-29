from services.preference import extract_preferences


async def preference_node(state):

    user_message = state["user_message"]

    preferences = await extract_preferences(
        user_message
    )


    return {
        **state,
        "preferences": preferences.model_dump()
    }
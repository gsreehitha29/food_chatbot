from tools.retriever import retrieve_dishes


async def retrieve_node(state):

    preferences = state.get(
        "user_preferences",
        {}
    )

    dishes = retrieve_dishes(preferences)

    return {
        **state,
        "candidate_dishes": dishes
    }
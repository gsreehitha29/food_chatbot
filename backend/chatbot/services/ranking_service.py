def rank_dishes(dishes, state):

    weather = state.get("weather", {})
    condition = weather.get("condition", "")

    ranked = []

    for doc in dishes:

        score = 0

        text = doc.page_content.lower()

        if condition == "Rain":
            if "soup" in text:
                score += 3

            if "tea" in text:
                score += 2

        if state["time_of_day"] == "night":
            if "biryani" in text:
                score += 2

        ranked.append((score, doc))

    ranked.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [doc for _, doc in ranked]
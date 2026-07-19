
from ...services.weather_service import get_weather
from datetime import datetime


async def context_node(state):
    
    location = state['location_name']
    
    weather = get_weather(state)
    

    hour = datetime.now().hour

    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    elif hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    return {
        **state,
        "location": location,
        "weather": weather,
        "time_of_day": time_of_day
    }
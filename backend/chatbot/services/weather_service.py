import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")


def get_weather(state):
    location=state['location']

    if not location:
        return {}

    try:
        lat = location.get("latitude")
        lon = location.get("longitude")

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        )

        data = requests.get(url).json()

        return {
            "temperature": data["main"]["temp"],
            "condition": data["weather"][0]["main"]
        }

    except Exception:
        return {}
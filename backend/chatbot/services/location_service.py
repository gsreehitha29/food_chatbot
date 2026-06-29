from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="restaurant_bot")


def get_city(location):

    if not location:
        return "Unknown"

    lat = location.get("latitude")
    lon = location.get("longitude")

    if lat is None or lon is None:
        return "Unknown"

    try:
        place = geolocator.reverse((lat, lon), timeout=10)

        if not place or "address" not in place.raw:
            return "Unknown"

        address = place.raw["address"]

        return (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("state")
            or "Unknown"
        )

    except Exception as e:
        print("❌ Geocoding error:", str(e))
        return "Unknown"
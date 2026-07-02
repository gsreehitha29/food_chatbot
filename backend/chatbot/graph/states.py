from typing import TypedDict, Optional, List, Any, Dict


class RestaurantState(TypedDict, total=False):

    # user input
    user_message: str

    # intent
    intent: Optional[str]

    # menu flow
    current_category: Optional[str]
    selected_item: Optional[str]
    quantity: Optional[int]
    categories: Optional[List[str]]

    # cart system
    cart: List[Any]

    # conversation
    history: List[dict]
    conversation_id: Optional[str]
    waiting_for: Optional[str]

    # response
    response: Optional[str]


    # raw GPS from frontend
    location: Optional[Dict[str, float]]

    # derived city name (IMPORTANT)
    location_name: Optional[str]

    # weather
    weather: Optional[Dict[str, Any]]

    time_of_day: Optional[str]

    user_preferences: Optional[Dict[str, Any]]

    context: Optional[Dict[str, Any]]

    candidate_dishes: Optional[List[Any]]
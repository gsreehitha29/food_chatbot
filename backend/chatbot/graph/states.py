from typing import TypedDict, Optional, List, Any


class RestaurantState(TypedDict, total=False):

    user_message: str

    intent: Optional[str]

    current_category: Optional[str]

    selected_item: Optional[str]

    quantity: Optional[int]

    cart: List[Any]

    response: Optional[str]

    history: List[dict]

    conversation_id: Optional[str]

    waiting_for: Optional[str]
    categories: Optional[List[str]]
 
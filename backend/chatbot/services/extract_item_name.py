from pydantic import BaseModel
from services.llm import llm

class OrderItem(BaseModel):
    item_name: str
    quantity: int

structured_llm = llm.with_structured_output(OrderItem)

def extract_item_name(user_message):

    prompt = f"""
    Extract the food item and quantity.

    User: {user_message}

    Examples:

    Add 2 Paneer Tikka
    =>
    item_name=Paneer Tikka
    quantity=2

    I want 3 prawn curry
    =>
    item_name=Prawn Curry
    quantity=3
    """

    return structured_llm.invoke(prompt)
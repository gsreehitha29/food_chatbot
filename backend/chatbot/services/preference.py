from pydantic import BaseModel, Field
from typing import Optional
from .llm import llm


class UserPreferences(BaseModel):
    cuisine: Optional[str] = Field(
        default=None,
        description="Cuisine preference like Indian, Chinese, Italian"
    )

    diet: Optional[str] = Field(
        default=None,
        description="veg or non_veg"
    )

    spice_level: Optional[str] = Field(
        default=None,
        description="low, medium, high"
    )

    budget: Optional[int] = Field(
        default=None,
        description="Maximum budget in rupees"
    )

    category: Optional[str] = Field(
        default=None,
        description="Food category like Pizza, Dessert, Drinks"
    )

    similar_to: Optional[str] = Field(
        default=None,
        description="Dish the user wants something similar to"
    )


structured_llm = llm.with_structured_output(UserPreferences)


async def extract_preferences(user_message: str):

    SYSTEM_PROMPT = """
You are a STRICT JSON extraction engine.

You MUST extract food preferences from user input.

RULES:
- Output MUST contain ONLY valid JSON
- NEVER return empty assistant messages
- NEVER omit reasoning fields silently
- If a field is unknown, explicitly set null

FIELDS:
- cuisine: string or null
- diet: "veg" | "non_veg" | null
- spice_level: "low" | "medium" | "high" | null
- budget: integer or null
- similar_to: string or null

CRITICAL:
If no preference is found, try to infer from context if possible.
If still nothing exists, return all fields as null.
"""
    
    preferences = structured_llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", user_message)
    ])

    return preferences

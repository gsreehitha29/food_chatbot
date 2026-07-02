"""
=============================================================
AI SEARCH PYDANTIC MODELS
=============================================================
This module defines Pydantic schemas for the AI retrieval and 
recommendation systems. It ensures strict request validation
and consistent, strongly-typed JSON responses.
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QueryFilters(BaseModel):
    """Extracted intent and filters from user query."""
    cuisine: Optional[str] = Field(None, description="Extracted cuisine type (e.g. Italian, Indian, Chinese)")
    max_price: Optional[float] = Field(None, description="Maximum budget/price filter")
    veg_or_nonveg: Optional[str] = Field(None, description="Vegetarian, Non-Vegetarian or any (veg/nonveg)")
    spice_level: Optional[str] = Field(None, description="Spice preference: spicy, mild, medium, none")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary filters like gluten-free, vegan, nut-free")
    taste_preference: Optional[str] = Field(None, description="Taste category: cheesy, crispy, sweet, sour, savory")
    meal_type: Optional[str] = Field(None, description="Meal category: breakfast, lunch, dinner, snack, dessert")
    semantic_intent: Optional[str] = Field(None, description="Cleaned core search phrase for vector matching")


class SearchRequest(BaseModel):
    """Request payload for semantic and hybrid search."""
    query: str = Field(..., min_length=1, description="Natural language search query")
    user_id: Optional[str] = Field(None, description="User ID for personalizing results")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "crispy vegetarian snacks under 150",
                    "user_id": "USR001"
                }
            ]
        }
    }


class AISearchResult(BaseModel):
    """Detailed search result with AI relevance explanation."""
    item_id: str
    restaurant_id: str
    restaurant_name: str
    category_id: str
    item_name: str
    description: str = ""
    price: float
    veg_or_nonveg: str
    rating: float
    availability: bool
    score: float = Field(..., description="Calculated recommendation score (0.0 to 1.0)")
    reason: Optional[str] = Field(None, description="Gemini generated reasoning for why this fits the query")
    cuisine: Optional[List[str]] = Field(None, description="Cuisine of the menu item")

class SearchResponse(BaseModel):
    """Standardized search API response."""
    status: str = "success"
    query: str
    query_understanding: QueryFilters
    total_results: int
    items: List[AISearchResult]


class RecommendationRequest(BaseModel):
    """Request payload for semantic recommendation generator."""
    user_id: str = Field(..., description="User ID to generate recommendations for")
    limit: int = Field(5, ge=1, le=20, description="Max number of items to return")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR001",
                    "limit": 5
                }
            ]
        }
    }


class RecommendationResponse(BaseModel):
    """Standardized recommendations API response."""
    status: str = "success"
    user_id: str
    recommendations: List[AISearchResult]


class ConversationRequest(BaseModel):
    """Request payload for conversational search session."""
    query: str = Field(..., min_length=1, description="Latest natural language chat message")
    session_id: str = Field(..., description="Unique session identifier for chat history")
    user_id: Optional[str] = Field(None, description="User ID for personalizing results")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "I want something cheesy",
                    "session_id": "session-1234",
                    "user_id": "USR001"
                }
            ]
        }
    }


class ConversationResponse(BaseModel):
    """Standardized conversational search response."""
    status: str = "success"
    session_id: str
    query: str
    accumulated_filters: QueryFilters
    response_text: str = Field(..., description="Natural language response from the AI assistant")
    items: List[AISearchResult]

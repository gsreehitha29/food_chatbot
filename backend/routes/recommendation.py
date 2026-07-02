"""
=============================================================
RECOMMENDATION ROUTES (Rule-Based)
=============================================================
API endpoint for rule-based food recommendations.

FIX #9: DUAL RECOMMENDATION SYSTEMS — CLARIFICATION
------------------------------------------------------
This app has two separate recommendation systems:

1. RULE-BASED (this file — GET /recommendation):
   Uses keyword pairing rules (Pizza → Coke, Biryani → Raita).
   Fast, no AI required, works without Gemini API key.
   Best for simple "what goes with this?" suggestions.

2. AI-POWERED (routes/ai_search.py — POST /search/recommendations):
   Uses Gemini embeddings + Qdrant vector search + multi-factor
   scoring. Requires GEMINI_API_KEY. Personalizes based on user
   profile and cart, generates natural language reasoning.
   Best for personalized, semantically rich recommendations.

ENDPOINT:
  GET /recommendation?user_id=USR001
=============================================================
"""

from fastapi import APIRouter, Query
from services.recommendation_service import get_recommendations

# Create router with "Recommendations" tag for Swagger docs
router = APIRouter(tags=["Recommendations"])


@router.get(
    "/recommendation",
    summary="Get rule-based food recommendations",
    description=(
        "Returns food recommendations using keyword pairing rules "
        "(e.g. Pizza → Coke, Biryani → Raita). "
        "This is a fast, rule-based system that does NOT require a Gemini API key. "
        "For AI-powered semantic recommendations, use POST /search/recommendations instead."
    )
)
def recommend(
    user_id: str = Query(
        ...,
        description="User ID to generate recommendations for"
    )
):
    """
    GET /recommendation?user_id=USR001
    
    How it works:
    1. Checks what's in the user's cart
    2. Matches cart items against pairing rules
    3. Finds matching items in the restaurant's menu
    4. Also suggests popular items from the same restaurant
    
    Sample Response:
    {
        "status": "success",
        "message": "Here are some items you might enjoy!",
        "cart_based": [
            {
                "item_id": "ITEM010",
                "item_name": "Coke",
                "price": 60,
                ...
            }
        ],
        "popular": [
            {
                "item_id": "ITEM005",
                "item_name": "Garlic Bread",
                "price": 149,
                ...
            }
        ]
    }
    """
    result = get_recommendations(user_id)

    return {
        "status": "success",
        **result
    }

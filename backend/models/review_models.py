"""
=============================================================
REVIEW PYDANTIC MODELS
=============================================================
Models for restaurant reviews and sentiment analysis results.

REVIEW FLOW:
1. User places an order and it gets delivered
2. User submits a review with rating + text + optional images
3. System can analyze all reviews for a restaurant
   to show sentiment breakdown (positive/negative/neutral)
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# -------------------------------------------------------
# REQUEST MODEL: Submit a new review
# -------------------------------------------------------
class ReviewCreateRequest(BaseModel):
    """Data required to submit a review."""
    restaurant_id: str = Field(..., description="Restaurant being reviewed")
    user_id: str = Field(..., description="User submitting the review")
    order_id: str = Field(..., description="Order this review is about")
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating from 1.0 to 5.0")
    review_text: str = Field(..., min_length=5, description="Written review")
    review_images: List[str] = Field(default=[], description="URLs of review images")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "restaurant_id": "REST001",
                    "user_id": "USR001",
                    "order_id": "ORD001",
                    "rating": 4.5,
                    "review_text": "Amazing biryani! The flavors were perfect and delivery was fast.",
                    "review_images": []
                }
            ]
        }
    }


# -------------------------------------------------------
# RESPONSE MODEL: A single review
# -------------------------------------------------------
class ReviewResponse(BaseModel):
    """Review data returned in API responses."""
    review_id: str
    restaurant_id: str
    user_id: str
    order_id: str
    rating: float
    review_text: str
    review_images: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# -------------------------------------------------------
# RESPONSE MODEL: Sentiment analysis results
# -------------------------------------------------------
class SentimentResponse(BaseModel):
    """
    Sentiment analysis breakdown for a restaurant's reviews.
    
    Example response:
    {
        "restaurant_id": "REST001",
        "total_reviews": 50,
        "positive_pct": 72.0,
        "negative_pct": 12.0,
        "neutral_pct": 16.0,
        "average_rating": 4.2,
        "top_complaints": ["slow delivery", "cold food"]
    }
    """
    restaurant_id: str
    total_reviews: int
    positive_pct: float  # percentage of positive reviews
    negative_pct: float  # percentage of negative reviews
    neutral_pct: float   # percentage of neutral reviews
    average_rating: float
    top_complaints: List[str] = []

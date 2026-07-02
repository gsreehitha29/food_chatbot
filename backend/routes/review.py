"""
=============================================================
REVIEW ROUTES
=============================================================
API endpoints for restaurant reviews and sentiment analysis.

FIX #6: Routes now delegate database access to review_service.py
instead of querying collections directly in the handler.

FIX #20: Added POST /reviews endpoint using the ReviewCreateRequest
model that was defined but never wired to an endpoint.

ENDPOINTS:
  POST /reviews                   → Submit a new review
  GET  /reviews/{restaurant_id}   → Get all reviews for a restaurant
  GET  /sentiment/{restaurant_id} → Get sentiment analysis for reviews
=============================================================
"""

from fastapi import APIRouter, HTTPException
from models.review_models import ReviewCreateRequest
from services.review_service import get_reviews_for_restaurant, create_review
from services.sentiment_service import get_restaurant_sentiment

# Create router with "Reviews" tag for Swagger docs
router = APIRouter(tags=["Reviews"])


@router.post(
    "/reviews",
    summary="Submit a review",
    description="Submit a new restaurant review. Also updates the restaurant's aggregate rating."
)
def submit_review(request: ReviewCreateRequest):
    """
    POST /reviews

    FIX #20: ReviewCreateRequest was defined in models/review_models.py
    but was never connected to an actual endpoint. This fixes that.

    Sample Request:
    {
        "restaurant_id": "REST001",
        "user_id": "USR001",
        "order_id": "ORD-SAMPLE01",
        "rating": 4.5,
        "review_text": "Amazing biryani! The flavors were perfect.",
        "review_images": []
    }

    Sample Response:
    {
        "status": "success",
        "message": "Review submitted successfully",
        "review": {
            "review_id": "REV-A1B2C3D4",
            "restaurant_id": "REST001",
            "rating": 4.5,
            ...
        }
    }
    """
    review = create_review(
        restaurant_id=request.restaurant_id,
        user_id=request.user_id,
        order_id=request.order_id,
        rating=request.rating,
        review_text=request.review_text,
        review_images=request.review_images,
    )
    return {
        "status": "success",
        "message": "Review submitted successfully",
        "review": review,
    }


@router.get(
    "/reviews/{restaurant_id}",
    summary="Get restaurant reviews",
    description="Returns all reviews for a specific restaurant, sorted by newest first."
)
def get_reviews(restaurant_id: str):
    """
    GET /reviews/REST001

    Returns all reviews for a restaurant, sorted by creation date (newest first).

    Sample Response:
    {
        "status": "success",
        "restaurant_id": "REST001",
        "total_reviews": 3,
        "reviews": [
            {
                "review_id": "REV001",
                "user_id": "USR001",
                "rating": 4.5,
                "review_text": "Amazing biryani!",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
    """
    reviews = get_reviews_for_restaurant(restaurant_id)

    if not reviews:
        raise HTTPException(
            status_code=404,
            detail=f"No reviews found for restaurant '{restaurant_id}'"
        )

    return {
        "status": "success",
        "restaurant_id": restaurant_id,
        "total_reviews": len(reviews),
        "reviews": reviews,
    }


@router.get(
    "/sentiment/{restaurant_id}",
    summary="Get sentiment analysis",
    description="Analyzes all reviews for a restaurant and returns sentiment breakdown."
)
def get_sentiment(restaurant_id: str):
    """
    GET /sentiment/REST001

    Runs sentiment analysis (VADER/TextBlob) on all reviews
    for a restaurant and returns a summary.

    Sample Response:
    {
        "status": "success",
        "sentiment": {
            "restaurant_id": "REST001",
            "total_reviews": 50,
            "positive_pct": 72.0,
            "negative_pct": 12.0,
            "neutral_pct": 16.0,
            "average_rating": 4.2,
            "top_complaints": ["slow delivery", "cold food"]
        }
    }
    """
    sentiment = get_restaurant_sentiment(restaurant_id)

    if sentiment["total_reviews"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No reviews found for restaurant '{restaurant_id}'"
        )

    return {"status": "success", "sentiment": sentiment}

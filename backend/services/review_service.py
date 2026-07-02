"""
=============================================================
REVIEW SERVICE
=============================================================
FIX #6: Business logic for review fetching and creation.
Previously routes/review.py accessed the database directly
in the route handler, violating the service-layer pattern.

FIX #20: create_review() is the implementation backing the
new POST /reviews endpoint. ReviewCreateRequest was defined
but never used before this fix.
=============================================================
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database import reviews_collection, restaurants_collection


def get_reviews_for_restaurant(restaurant_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all reviews for a restaurant, sorted newest first.

    Args:
        restaurant_id: The restaurant to fetch reviews for

    Returns:
        List of review dicts (without _id)
    """
    return list(
        reviews_collection.find(
            {"restaurant_id": restaurant_id},
            {"_id": 0}
        ).sort("created_at", -1)  # Newest first
    )


def create_review(
    restaurant_id: str,
    user_id: str,
    order_id: str,
    rating: float,
    review_text: str,
    review_images: List[str]
) -> Dict[str, Any]:
    """
    FIX #20: Create a new review for a restaurant.

    After creating the review, also updates the restaurant's
    aggregate average rating in MongoDB.

    Args:
        restaurant_id: The restaurant being reviewed
        user_id: The user submitting the review
        order_id: The order this review is for
        rating: Star rating from 1.0 to 5.0
        review_text: Written review content
        review_images: List of image URLs

    Returns:
        The created review document (without MongoDB _id)
    """
    now = datetime.now(timezone.utc)
    review_doc = {
        "review_id": f"REV-{uuid.uuid4().hex[:8].upper()}",
        "restaurant_id": restaurant_id,
        "user_id": user_id,
        "order_id": order_id,
        "rating": rating,
        "review_text": review_text,
        "review_images": review_images,
        "created_at": now,
        "updated_at": now,
    }

    reviews_collection.insert_one(review_doc)
    review_doc.pop("_id", None)

    # Recalculate and update restaurant average rating
    _update_restaurant_avg_rating(restaurant_id)

    return review_doc


def _update_restaurant_avg_rating(restaurant_id: str):
    """
    Recalculate the average rating for a restaurant based on all reviews
    and update it in the restaurants collection.

    This keeps the restaurant's cached rating in sync after each review.
    """
    all_ratings = list(
        reviews_collection.find(
            {"restaurant_id": restaurant_id},
            {"rating": 1, "_id": 0}
        )
    )
    if not all_ratings:
        return

    avg = round(sum(r["rating"] for r in all_ratings) / len(all_ratings), 1)
    restaurants_collection.update_one(
        {"restaurant_id": restaurant_id},
        {"$set": {"rating": avg, "updated_at": datetime.now(timezone.utc)}}
    )

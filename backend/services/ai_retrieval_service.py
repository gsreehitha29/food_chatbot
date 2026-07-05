"""
=============================================================
AI RETRIEVAL ORCHESTRATOR SERVICE
=============================================================
Orchestrates the entire AI retrieval and recommendation engine:
1. Extract intent and filters using Gemini.
2. Formulate hybrid query (Qdrant vector + payload filters).
3. Apply review-aware custom reranking formula.
4. Manage conversational search sessions.
5. Personalize recommendations based on user profiles and cart context.
6. Cache query and search responses for performance.

FIX #7: _rank_and_score_items() now pre-fetches all restaurant and
review data in bulk BEFORE the ranking loop. This reduces the
per-search MongoDB queries from O(N) to O(1) round-trips.

FIX #16: Sentiment analysis results are now cached in Redis/memory
via CacheService to avoid recomputing on every search request.
=============================================================
"""

import logging
from typing import List, Dict, Any, Optional

from database import (
    restaurants_collection,
    menu_collection,
    reviews_collection,
    users_collection,
    carts_collection
)
from models.ai_models import AISearchResult, QueryFilters
from services.embeddings_service import EmbeddingsService
from services.vector_service import get_qdrant_service
from services.llm_service import LLMService
from services.cache_service import CacheService
from services.sentiment_service import analyze_sentiment
from services.memory_service import get_session_history, add_message_to_session
import config

logger = logging.getLogger(__name__)


class AIRetrievalService:
    """Core AI Food Retrieval and Recommendation Engine Orchestrator."""
    
    def __init__(self):
        self.embeddings_service = EmbeddingsService()
        self.vector_service = get_qdrant_service()  # Shared singleton
        self.llm_service = LLMService()
        self.cache_service = CacheService()

    def _calculate_review_score_from_data(
        self,
        item_name: str,
        reviews: List[Dict[str, Any]]
    ) -> float:
        """
        FIX #7: Calculate review score from pre-fetched review data
        instead of making a new MongoDB query per item.

        Args:
            item_name: Name of the menu item (used for keyword matching)
            reviews: Pre-fetched list of review dicts for the restaurant

        Returns:
            float: Score between 0.0 and 1.0
        """
        if not reviews:
            return 0.5  # Neutral fallback

        # Match reviews mentioning item name keywords
        item_keywords = [w.lower() for w in item_name.split() if len(w) > 3]
        item_reviews = [
            r for r in reviews
            if any(kw in r.get("review_text", "").lower() for kw in item_keywords)
        ]

        if item_reviews:
            total_compound = sum(
                analyze_sentiment(r.get("review_text", "")).get("compound", 0.0)
                for r in item_reviews
            )
            avg_compound = total_compound / len(item_reviews)
            base_score = (avg_compound + 1.0) / 2.0
        else:
            # Fallback: use restaurant-level positive sentiment ratio
            positive = sum(
                1 for r in reviews
                if analyze_sentiment(r.get("review_text", ""))["label"] == "positive"
            )
            base_score = (positive / len(reviews)) if reviews else 0.5

        # Count positive/negative keyword signals
        pos_keywords = ["crispy", "authentic", "creamy", "juicy", "fresh", "flavorful"]
        neg_keywords = ["stale", "soggy", "cold food", "late delivery", "bad packaging"]

        target_reviews = item_reviews if item_reviews else reviews
        pos_count = sum(
            1 for r in target_reviews for kw in pos_keywords
            if kw in r.get("review_text", "").lower()
        )
        neg_count = sum(
            1 for r in target_reviews for kw in neg_keywords
            if kw in r.get("review_text", "").lower()
        )

        score = base_score + (0.05 * pos_count) - (0.1 * neg_count)
        return min(max(score, 0.0), 1.0)

    def _rank_and_score_items(
        self,
        query_or_intent: str,
        qdrant_matches: List[Dict[str, Any]],
        generate_reasoning: bool = False
    ) -> List[AISearchResult]:
        """
        Rank candidate menu items using our custom multi-factor scorer.

        FIX #7: Pre-fetches all restaurants and reviews in 2 bulk MongoDB
        queries before the loop, instead of 2 queries per item (N*2 total).
        """
        if not qdrant_matches:
            return []

        # -------------------------------------------------------
        # FIX #7: PRE-FETCH in bulk — 2 queries total regardless of N
        # -------------------------------------------------------
        unique_rest_ids = list({hit["restaurant_id"] for hit in qdrant_matches})

        restaurants_map = {
            r["restaurant_id"]: r
            for r in restaurants_collection.find(
                {"restaurant_id": {"$in": unique_rest_ids}},
                {"_id": 0}
            )
        }

        reviews_map: Dict[str, List[Dict]] = {}
        for r in reviews_collection.find(
            {"restaurant_id": {"$in": unique_rest_ids}},
            {"_id": 0}
        ):
            reviews_map.setdefault(r["restaurant_id"], []).append(r)

        ranked_items = []

        for hit in qdrant_matches:
            item_id = hit["item_id"]
            restaurant_id = hit["restaurant_id"]
            item_name = hit["item_name"]
            description = hit.get("description", "")
            price = hit["price"]
            veg_or_nonveg = hit["veg_or_nonveg"]
            category_id = hit["category_id"]
            availability = hit["availability"]
            cuisine = hit["cuisine"]
            restaurant_name = hit["restaurant_name"]

            # 1. Semantic Similarity Score (from Qdrant)
            semantic_score = hit.get("score", 0.5)

            # 2. Menu Item Rating
            menu_rating = hit.get("rating", 0.0)
            menu_rating_norm = menu_rating / 5.0

            # 3. Restaurant Rating — from pre-fetched map (FIX #7)
            restaurant = restaurants_map.get(restaurant_id, {})
            rest_rating = restaurant.get("rating", 0.0)
            rest_rating_norm = rest_rating / 5.0

            # 4. Review Sentiment Score — from pre-fetched reviews (FIX #7)
            item_reviews = reviews_map.get(restaurant_id, [])
            review_score = self._calculate_review_score_from_data(item_name, item_reviews)

            # 5. Availability Score
            availability_score = 1.0 if availability else 0.0

            # Weighted Scoring Formula
            final_score = (
                config.WEIGHT_SEMANTIC * semantic_score +
                config.WEIGHT_REVIEW * review_score +
                config.WEIGHT_MENU_RATING * menu_rating_norm +
                config.WEIGHT_RESTAURANT_RATING * rest_rating_norm +
                config.WEIGHT_AVAILABILITY * availability_score
            )

            # Generate AI Reasoning if requested
            reason = None
            if generate_reasoning:
                reviews_brief = " | ".join(
                    [r.get("review_text", "")[:100] for r in item_reviews[:3]]
                )
                reason = self.llm_service.generate_recommendation_reason(
                    query_or_intent=query_or_intent,
                    item_name=item_name,
                    restaurant_name=restaurant_name,
                    description=description,
                    rating=menu_rating,
                    price=price,
                    reviews_summary=reviews_brief
                )

            ranked_items.append(
                AISearchResult(
                    item_id=item_id,
                    restaurant_id=restaurant_id,
                    restaurant_name=restaurant_name,
                    cuisine=cuisine,
                    category_id=category_id,
                    item_name=item_name,
                    description=description,
                    price=price,
                    veg_or_nonveg=veg_or_nonveg,
                    rating=menu_rating,
                    availability=availability,
                    score=round(final_score, 4),
                    reason=reason
                )
            )

        # Sort items by final ranking score in descending order
        ranked_items.sort(key=lambda x: x.score, reverse=True)
        return ranked_items

    def search_semantic(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> List[AISearchResult]:
        """Pure semantic vector search."""
        # Check cache first
        cache_key = f"semantic_search:{query}"
        cached = self.cache_service.get_json(cache_key)
        if cached:
            logger.info(f"[CACHE HIT] semantic_search: {query}")
            return [AISearchResult(**item) for item in cached]

        # Generate embedding for full query
        query_vector = self.embeddings_service.embed_query(query)

        # Search Qdrant (no metadata filters applied)
        matches = self.vector_service.search_semantic(
            query_vector=query_vector,
            limit=10,
            filters=None
        )

        # Rank results
        results = self._rank_and_score_items(query, matches, generate_reasoning=False)

        # Cache results
        self.cache_service.set_json(cache_key, [item.model_dump() for item in results])

        return results

    def search_hybrid(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Hybrid search combining structured Mongo metadata filters and Qdrant vector retrieval."""
        cache_key = f"hybrid_search:{query}"
        cached = self.cache_service.get_json(cache_key)
        if cached:
            logger.info(f"[CACHE HIT] hybrid_search: {query}")
            return {
                "query_understanding": QueryFilters(**cached["query_understanding"]),
                "items": [AISearchResult(**item) for item in cached["items"]]
            }

        # 1. LLM Query Understanding
        filters = self.llm_service.parse_query_intent(query)

        # 2. Generate embedding for semantic intent (or full query fallback)
        vector_query = filters.semantic_intent if filters.semantic_intent else query
        query_vector = self.embeddings_service.embed_query(vector_query)

        # 3. Query Qdrant with filters parsed from LLM
        matches = self.vector_service.search_semantic(
            query_vector=query_vector,
            limit=15,
            filters=filters.model_dump()
        )
        # Backend safeguard for price filtering

        max_price = getattr(filters, "max_price", None)

        if max_price is not None:

            matches = [
                item
                for item in matches
                if item.get("price", 0) <= max_price
            ]
        food_item = getattr(filters, "food_item", None)

        if food_item:
            matches = [
                item
                for item in matches
                if food_item.lower() in item.get("item_name", "").lower()
            ]
        print("\n===== AFTER FOOD FILTER =====")
        for item in matches:
            print(item["item_name"])
        # 4. Rank and Score matching candidates
        results = self._rank_and_score_items(vector_query, matches, generate_reasoning=False)

        output = {
            "query_understanding": filters,
            "items": results
        }

        # Cache serialization
        cached_val = {
            "query_understanding": filters.model_dump(),
            "items": [item.model_dump() for item in results]
        }
        self.cache_service.set_json(cache_key, cached_val)
        print(filters.model_dump())
        return output

    def search_conversational(
        self,
        query: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Context-aware conversational search tracking query preferences across dialog turns."""
        # 1. Get history and accumulate active constraints
        print("STEP 1")
        history = get_session_history(session_id)
        print("STEP 2")
        filters = self.llm_service.accumulate_conversation_filters(query, history)

        # Add user query to conversation history
        add_message_to_session(session_id, "user", query)

        # 2. Get embeddings and query vector store
        print("STEP 3")
        vector_query = filters.semantic_intent if filters.semantic_intent else query
        query_vector = self.embeddings_service.embed_query(vector_query)
        print("STEP 4")
        # 3. Retrieve filtered vector matches
        matches = self.vector_service.search_semantic(
            query_vector=query_vector,
            limit=10,
            filters=filters.model_dump()
        )
        max_price = getattr(filters, "max_price", None)

        if max_price is not None:

            matches = [
                item
                for item in matches
                if item.get("price", 0) <= max_price
    ]

        # 4. Rank results
        print("STEP 5")
        results = self._rank_and_score_items(vector_query, matches, generate_reasoning=False)
        print("STEP 6")
        # 5. Generate conversational assistant response text
        response_text = self.llm_service.generate_conversational_response(
            current_query=query,
            history_messages=history,
            items=[r.model_dump() for r in results]
        )
        print("STEP 7")
        # Add assistant response to conversation history
        add_message_to_session(session_id, "assistant", response_text)

        return {
            "session_id": session_id,
            "query": query,
            "accumulated_filters": filters,
            "response_text": response_text,
            "items": results
        }

    def get_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[AISearchResult]:
        """Generate personalized AI recommendations based on user preferences and current cart."""
        cache_key = f"recommendations:{user_id}:{limit}"
        cached = self.cache_service.get_json(cache_key)
        if cached:
            logger.info(f"[CACHE HIT] recommendations: {user_id}")
            return [AISearchResult(**item) for item in cached]

        # 1. Fetch User Profile
        user = users_collection.find_one({"user_id": user_id})
        favorite_cuisines = user.get("favorite_cuisines", []) if user else []

        # 2. Fetch User's current cart
        cart = carts_collection.find_one({"user_id": user_id})
        cart_items = cart.get("items", []) if cart else []
        cart_item_names = [item["item_name"] for item in cart_items]

        candidate_matches = []
        query_explanation = "popular items"

        # 3. Strategy: Vector Similarity recommendation from Cart items
        if cart_items:
            logger.info(f"Generating recommendations based on cart items: {cart_item_names}")
            first_cart_item = cart_items[0]
            query_text = f"foods matching {first_cart_item['item_name']}"
            query_vector = self.embeddings_service.embed_query(query_text)

            cart_item_ids = [item["item_id"] for item in cart_items]

            candidates = self.vector_service.search_semantic(
                query_vector=query_vector,
                limit=limit + len(cart_item_ids),
                filters={"availability": True}
            )
            candidate_matches = [c for c in candidates if c["item_id"] not in cart_item_ids][:limit]
            query_explanation = f"complementary dishes to {first_cart_item['item_name']}"

        # 4. Strategy: Favorite Cuisines
        elif favorite_cuisines:
            logger.info(f"Generating recommendations based on user favorite cuisines: {favorite_cuisines}")
            cuisine_query = " OR ".join(favorite_cuisines)
            query_vector = self.embeddings_service.embed_query(cuisine_query)

            candidate_matches = self.vector_service.search_semantic(
                query_vector=query_vector,
                limit=limit,
                filters={"availability": True, "cuisine": favorite_cuisines[0]}
            )
            query_explanation = f"highly rated {favorite_cuisines[0]} cuisine"

        # 5. Default Strategy: Popular top rated items overall
        else:
            logger.info("Generating fallback popular recommendations")
            query_vector = self.embeddings_service.embed_query("popular comfort food dishes")
            candidate_matches = self.vector_service.search_semantic(
                query_vector=query_vector,
                limit=limit,
                filters={"availability": True}
            )
            query_explanation = "top rated overall menu highlights"

        # 6. Rank and Score
        results = self._rank_and_score_items(query_explanation, candidate_matches, generate_reasoning=False)

        # Cache results
        self.cache_service.set_json(cache_key, [item.model_dump() for item in results])

        return results

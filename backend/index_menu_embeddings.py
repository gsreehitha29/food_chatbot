"""
=============================================================
STANDALONE INDEXING & PIPELINE SCRIPT
=============================================================
This script reads restaurants, menu items, and reviews from MongoDB,
joins them together, generates semantic tags, generates vector embeddings,
and stores the resulting payloads in Qdrant.

HOW TO RUN:
    python index_menu_embeddings.py [--rebuild]

OPTIONS:
    --rebuild   Delete the existing collection and re-index all data.
                Without this flag, it performs an incremental update.
=============================================================
"""

import sys
import argparse
import logging
from typing import List, Dict, Any

from database import restaurants_collection, menu_collection, reviews_collection
from services.embeddings_service import EmbeddingsService
# FIX #1: Import the singleton accessor instead of QdrantService directly.
# When called from the app (via background task), this returns the same in-memory
# instance that the search endpoints use — preventing the isolation bug.
from services.vector_service import get_qdrant_service, string_to_uuid
from services.tag_service import generate_tags
import config

# FIX #15: Guard logging.basicConfig() so it only runs when executed as a
# standalone script. When imported as a module (e.g., from routes/ai_search.py),
# this avoids overriding the application's logging configuration.
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
logger = logging.getLogger(__name__)


def build_embedding_document(
    item: Dict[str, Any], 
    restaurant: Dict[str, Any], 
    reviews: List[Dict[str, Any]], 
    tags: List[str]
) -> str:
    """
    Build the detailed text document that represents the menu item for embedding.
    """
    item_name = item.get("item_name", "")
    description = item.get("description", "")
    cuisine = restaurant.get("cuisine", "") if restaurant else "Unknown"
    restaurant_name = restaurant.get("restaurant_name", "") if restaurant else "Unknown"
    category = item.get("category_id", "").replace("CAT_", "").title()
    
    # 1. Filter reviews that might refer to this specific item
    item_specific_reviews = []
    keywords = [w.lower() for w in item_name.split() if len(w) > 3]
    
    for r in reviews:
        text = r.get("review_text", "").lower()
        # If any keyword matches, or if we have general reviews
        if any(kw in text for kw in keywords):
            item_specific_reviews.append(r.get("review_text"))
            
    # If no specific reviews, grab top 2 reviews for the restaurant
    if not item_specific_reviews and reviews:
        # Sort by rating descending
        sorted_reviews = sorted(reviews, key=lambda x: x.get("rating", 0.0), reverse=True)
        item_specific_reviews = [r.get("review_text") for r in sorted_reviews[:2]]

    # 2. Compile document structure
    doc = f"Item: {item_name}\n"
    if description:
        doc += f"Description: {description}\n"
    doc += f"Cuisine: {cuisine}\n"
    doc += f"Restaurant: {restaurant_name}\n"
    doc += f"Category: {category}\n"
    
    if tags:
        doc += f"Tags: {', '.join(tags)}\n"
        
    if item_specific_reviews:
        doc += "Reviews:\n"
        for r_text in item_specific_reviews:
            doc += f"- {r_text.strip()}\n"
            
    return doc.strip()


def run_pipeline(rebuild: bool = False):
    """
    Run the indexing pipeline.
    
    Args:
        rebuild: If True, delete and recreate Qdrant collection first.
    """
    logger.info("Starting embedding pipeline...")
    
    # 1. Initialize services
    try:
        embeddings_service = EmbeddingsService()
        if not embeddings_service.enabled:
            logger.warning("[WARNING] Embeddings service is running in mock fallback mode because GEMINI_API_KEY is not set.")

        # FIX #1: Use the singleton so the app and this pipeline share the same
        # in-memory Qdrant instance when QDRANT_HOST is not configured.
        vector_service = get_qdrant_service()
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize services: {str(e)}")
        if __name__ == '__main__':
            sys.exit(1)
        raise

    # 2. Drop and recreate collection if rebuilding
    if rebuild:
        logger.info("Rebuilding vector database from scratch...")
        vector_service.recreate_collection()
    else:
        logger.info("Performing incremental update...")

    # 3. Load all Restaurants, Menu Items, and Reviews from MongoDB
    logger.info("Loading data from MongoDB...")
    restaurants = list(restaurants_collection.find({}))
    menu_items = list(menu_collection.find({}))
    reviews = list(reviews_collection.find({}))
    
    logger.info(f"Loaded {len(restaurants)} restaurants, {len(menu_items)} menu items, and {len(reviews)} reviews.")
    
    # Map restaurants for quick lookup
    restaurants_map = {r["restaurant_id"]: r for r in restaurants}
    
    # Group reviews by restaurant_id
    reviews_map = {}
    for r in reviews:
        rid = r["restaurant_id"]
        if rid not in reviews_map:
            reviews_map[rid] = []
        reviews_map[rid].append(r)

    # 4. Filter items that need indexing
    items_to_index = []
    
    for item in menu_items:
        item_id = item["item_id"]
        point_id = string_to_uuid(item_id)
        
        # Incremental check: see if point exists in Qdrant already
        if not rebuild:
            try:
                existing = vector_service.client.retrieve(
                    collection_name=config.QDRANT_COLLECTION,
                    ids=[point_id]
                )
                if existing:
                    logger.info(f"   [SKIP] Item '{item_id}' ({item['item_name']}) already indexed. Skipping.")
                    continue
            except Exception as e:
                # If error, index it to be safe
                logger.warning(f"Error checking status for {item_id}: {str(e)}. Will index.")

        restaurant = restaurants_map.get(item["restaurant_id"])
        item_reviews = reviews_map.get(item["restaurant_id"], [])
        
        # Generate tags
        review_texts = [r["review_text"] for r in item_reviews]
        tags = generate_tags(
            item_name=item["item_name"],
            description=item.get("description", ""),
            category_id=item.get("category_id", ""),
            reviews=review_texts
        )
        
        # Build document text
        doc_text = build_embedding_document(item, restaurant, item_reviews, tags)
        
        items_to_index.append({
            "item_id": item_id,
            "item": item,
            "restaurant": restaurant,
            "tags": tags,
            "doc_text": doc_text
        })

    if not items_to_index:
        logger.info("[SUCCESS] No new items to index.")
        return

    # 5. Generate embeddings and upsert in batches
    batch_size = 10
    total_items = len(items_to_index)
    logger.info(f"Indexing {total_items} items in batches of {batch_size}...")
    
    for i in range(0, total_items, batch_size):
        batch = items_to_index[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} items)...")
        
        texts = [b["doc_text"] for b in batch]
        try:
            vectors = embeddings_service.embed_documents(texts)
        except Exception as e:
            logger.error(f"[ERROR] Failed to generate embeddings for batch: {str(e)}")
            continue

        qdrant_items = []
        for idx, b in enumerate(batch):
            item = b["item"]
            restaurant = b["restaurant"]
            
            # Prepare metadata payload matching standard schema fields
            payload = {
                "item_id": item["item_id"],
                "restaurant_id": item["restaurant_id"],
                "restaurant_name": restaurant["restaurant_name"] if restaurant else "Unknown",
                "category_id": item["category_id"],
                "item_name": item["item_name"],
                "description": item.get("description", ""),
                "price": float(item["price"]),
                "veg_or_nonveg": item["veg_or_nonveg"],
                "rating": float(item.get("rating", 0.0)),
                "availability": bool(item.get("availability", True)),
                "cuisine": restaurant["cuisine"] if restaurant else "Unknown",
                "tags": b["tags"],
                "text": b["doc_text"]
            }
            
            qdrant_items.append({
                "item_id": b["item_id"],
                "vector": vectors[idx],
                "payload": payload
            })
            
        try:
            vector_service.upsert_menu_items(qdrant_items)
        except Exception as e:
            logger.error(f"[ERROR] Failed to upsert batch to Qdrant: {str(e)}")
            
    logger.info("[SUCCESS] Data indexing pipeline complete!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index menu items to Qdrant.")
    parser.add_argument(
        "--rebuild", 
        action="store_true", 
        help="Rebuild Qdrant collection from scratch (deletes existing data)"
    )
    args = parser.parse_args()
    
    run_pipeline(rebuild=args.rebuild)

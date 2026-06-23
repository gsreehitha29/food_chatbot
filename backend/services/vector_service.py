"""
=============================================================
QDRANT VECTOR SERVICE
=============================================================
Handles all operations with the Qdrant Vector database, including
collection initialization, document upserting, and executing semantic
search queries with native metadata filters.
=============================================================
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue, 
    Range
)
import config

logger = logging.getLogger(__name__)


def string_to_uuid(string_id: str) -> str:
    """Generate a deterministic UUID from a custom string ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, string_id))


class QdrantService:
    """Service to interface with Qdrant Vector Database."""
    
    def __init__(self):
        # 1. Connect to Qdrant. Fallback to in-memory if no host specified.
        if config.QDRANT_HOST:
            try:
                self.client = QdrantClient(
                    host=config.QDRANT_HOST,
                    port=config.QDRANT_PORT,
                    api_key=config.QDRANT_API_KEY
                )
                logger.info(f"[OK] Connected to Qdrant server at {config.QDRANT_HOST}:{config.QDRANT_PORT}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to connect to Qdrant server. Falling back to in-memory mode: {str(e)}")
                self.client = QdrantClient(":memory:")
        else:
            logger.info("[INFO] QDRANT_HOST not set. Initializing Qdrant client in in-memory mode (:memory:)")
            self.client = QdrantClient(":memory:")

        # 2. Ensure collection exists with correct parameters (3072 dimensions for gemini-embedding-001)
        self.vector_dim = 3072
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Creates the collection if it does not already exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if config.QDRANT_COLLECTION not in collection_names:
                logger.info(f"Creating Qdrant collection: {config.QDRANT_COLLECTION} (dim: {self.vector_dim})")
                self.client.create_collection(
                    collection_name=config.QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"[OK] Created Qdrant collection: {config.QDRANT_COLLECTION}")
            else:
                logger.info(f"[OK] Qdrant collection '{config.QDRANT_COLLECTION}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {str(e)}")

    def recreate_collection(self):
        """Force delete and recreate the collection (used for full rebuilds)."""
        try:
            logger.warning(f"Recreating Qdrant collection: {config.QDRANT_COLLECTION}")
            self.client.delete_collection(collection_name=config.QDRANT_COLLECTION)
            self.client.create_collection(
                collection_name=config.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=self.vector_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"[OK] Recreated Qdrant collection: {config.QDRANT_COLLECTION}")
        except Exception as e:
            logger.error(f"Error recreating collection: {str(e)}")
            raise e

    def upsert_menu_items(self, items: List[Dict[str, Any]]):
        """
        Upsert a batch of menu items with their vector embeddings and payloads.
        
        Args:
            items: List of dicts, each containing:
                - item_id: str
                - vector: List[float]
                - payload: Dict[str, Any]
        """
        points = []
        for item in items:
            point_id = string_to_uuid(item["item_id"])
            points.append(
                PointStruct(
                    id=point_id,
                    vector=item["vector"],
                    payload=item["payload"]
                )
            )
        
        try:
            self.client.upsert(
                collection_name=config.QDRANT_COLLECTION,
                wait=True,
                points=points
            )
            logger.info(f"[OK] Successfully upserted {len(points)} points into Qdrant collection '{config.QDRANT_COLLECTION}'")
        except Exception as e:
            logger.error(f"Error upserting points to Qdrant: {str(e)}")
            raise e

    def build_qdrant_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """
        Build a Qdrant Filter query from structured filters.
        
        Supported filters:
            - cuisine (str)
            - max_price (float)
            - veg_or_nonveg (str: 'veg' | 'nonveg')
            - availability (bool)
        """
        if not filters:
            return None
            
        conditions = []
        
        # 1. Cuisine Filter (Case-insensitive match if stored correctly, or exact match)
        if filters.get("cuisine"):
            # Capitalize to match seed data format (e.g. Italian, Indian)
            cuisine_val = filters["cuisine"].strip().title()
            conditions.append(
                FieldCondition(
                    key="cuisine",
                    match=MatchValue(value=cuisine_val)
                )
            )
            
        # 2. Veg/Nonveg Filter
        if filters.get("veg_or_nonveg"):
            veg_val = filters["veg_or_nonveg"].strip().lower()
            if veg_val in ["veg", "nonveg"]:
                conditions.append(
                    FieldCondition(
                        key="veg_or_nonveg",
                        match=MatchValue(value=veg_val)
                    )
                )

        # 3. Price/Budget Filter
        if filters.get("max_price") is not None:
            try:
                max_price = float(filters["max_price"])
                conditions.append(
                    FieldCondition(
                        key="price",
                        range=Range(lte=max_price)
                    )
                )
            except ValueError:
                pass
                
        # 4. Availability Filter (by default only return available items unless specified)
        avail = filters.get("availability", True)
        if avail is not None:
            conditions.append(
                FieldCondition(
                    key="availability",
                    match=MatchValue(value=bool(avail))
                )
            )

        if not conditions:
            return None
            
        return Filter(must=conditions)

    def search_semantic(
        self, 
        query_vector: List[float], 
        limit: int = 10, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute semantic search in Qdrant.
        
        Args:
            query_vector: Dense vector query
            limit: Max results to return
            filters: Structured payload filter dict
            
        Returns:
            List[Dict[str, Any]]: Matching records including payload and score.
        """
        qdrant_filter = self.build_qdrant_filter(filters) if filters else None
        
        try:
            results = self.client.search(
                collection_name=config.QDRANT_COLLECTION,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True
            )
            
            output = []
            for hit in results:
                # Combine payload data with structural details
                item = dict(hit.payload)
                item["score"] = hit.score
                output.append(item)
                
            return output
        except Exception as e:
            logger.error(f"Error performing semantic search in Qdrant: {str(e)}")
            return []


# ===========================================================
# FIX #10: THREAD-SAFE SINGLETON (double-checked locking)
# ===========================================================
# All modules must call get_qdrant_service() instead of
# instantiating QdrantService() directly. This ensures a single
# shared client is used — critical when running in :memory: mode.
# The threading.Lock prevents two workers from creating separate
# instances simultaneously in a concurrent environment.
# ===========================================================
import threading

_qdrant_lock = threading.Lock()
_qdrant_service_instance: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Return the shared thread-safe singleton QdrantService instance."""
    global _qdrant_service_instance
    if _qdrant_service_instance is None:
        with _qdrant_lock:
            # Double-check inside the lock to handle the race condition window
            if _qdrant_service_instance is None:
                _qdrant_service_instance = QdrantService()
    return _qdrant_service_instance

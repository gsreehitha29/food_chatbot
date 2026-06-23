"""
=============================================================
CONFIGURATION MODULE
=============================================================
This module manages all configuration options for the application,
including API keys, Qdrant/Redis details, and the custom weights
for the review-aware food ranking engine.
=============================================================
"""

import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# MongoDB Config (reusing existing variables)
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_database")

# Google Gemini API Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# Qdrant Vector DB Config
# If QDRANT_HOST is not specified, we will fall back to in-memory mode (:memory:)
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "food_menu_items")

# Redis Caching Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # Default cache duration: 1 hour

# Custom Food Reranking Weights
# Formula: Final Score = w_sem * Semantic + w_rev * Review + w_menu * MenuRating + w_rest * RestRating + w_avail * Availability
WEIGHT_SEMANTIC = float(os.getenv("WEIGHT_SEMANTIC", "0.4"))
WEIGHT_REVIEW = float(os.getenv("WEIGHT_REVIEW", "0.2"))
WEIGHT_MENU_RATING = float(os.getenv("WEIGHT_MENU_RATING", "0.2"))
WEIGHT_RESTAURANT_RATING = float(os.getenv("WEIGHT_RESTAURANT_RATING", "0.1"))
WEIGHT_AVAILABILITY = float(os.getenv("WEIGHT_AVAILABILITY", "0.1"))

# FIX #13: Order Processing Constants (previously hardcoded in order_service.py)
DELIVERY_FEE = float(os.getenv("DELIVERY_FEE", "40.0"))    # Flat delivery fee in ₹
TAX_RATE = float(os.getenv("TAX_RATE", "0.05"))             # 5% GST


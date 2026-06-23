"""
=============================================================
DATABASE CONNECTION MODULE
=============================================================
This module handles the MongoDB Atlas connection using pymongo.
It reads the connection URI from the .env file and provides
a reusable database object for all other modules.

How it works:
1. Loads environment variables from .env
2. Connects to MongoDB Atlas using the URI
3. Selects the 'chatbot_database' database
4. Creates indexes for fast queries
5. Exports collection references for use everywhere
=============================================================
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

# Load environment variables from .env file
load_dotenv()

# Read MongoDB connection string and database name from environment
MONGODB_URI = os.getenv("MONGODB_URI")
# Default aligned to "chatbot_database" — matches config.py and .env
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_database")

# FIX #4: Guard against missing MONGODB_URI instead of crashing with a cryptic pymongo error
if not MONGODB_URI:
    raise EnvironmentError(
        "MONGODB_URI is not set. Please configure your .env file. "
        "See .env.example for the required format."
    )

# -------------------------------------------------------
# Create a MongoDB client connection
# MongoClient manages a pool of connections automatically
# -------------------------------------------------------
client = MongoClient(MONGODB_URI)

# Select the database
db = client[DATABASE_NAME]

# =============================================================
# COLLECTION REFERENCES
# =============================================================
# These are shortcuts to each collection in the database.
# Import these in your routes/services to read/write data.
# =============================================================

restaurants_collection = db["RESTAURANTS"]
menu_collection = db["MENU"]
carts_collection = db["CART"]
orders_collection = db["ORDERS"]
reviews_collection = db["REVIEW"]
users_collection = db["USERS"]


def create_indexes():
    """
    Create database indexes for faster queries.
    
    WHY INDEXES?
    Without indexes, MongoDB scans every document in a collection
    to find matches (called a "collection scan"). Indexes let 
    MongoDB jump directly to matching documents, like a book index.
    
    WHEN TO CALL:
    Call this once when the application starts up.
    MongoDB will skip creating an index if it already exists.
    """
    # Restaurant lookups by restaurant_id
    restaurants_collection.create_index(
        [("restaurant_id", ASCENDING)], unique=True
    )
    # Searching restaurants by cuisine type
    restaurants_collection.create_index([("cuisine", ASCENDING)])

    # Menu lookups by item_id
    menu_collection.create_index(
        [("item_id", ASCENDING)], unique=True
    )
    # Fetching all menu items for a restaurant
    menu_collection.create_index([("restaurant_id", ASCENDING)])
    # Compound index for restaurant + category filtering
    menu_collection.create_index(
        [("restaurant_id", ASCENDING), ("category_id", ASCENDING)]
    )
    # Text index for searching menu items by name/description
    menu_collection.create_index(
        [("item_name", "text"), ("description", "text")]
    )

    # Cart lookups by cart_id and user_id
    carts_collection.create_index(
        [("cart_id", ASCENDING)], unique=True
    )
    carts_collection.create_index([("user_id", ASCENDING)])

    # Order lookups by order_id and user_id
    orders_collection.create_index(
        [("order_id", ASCENDING)], unique=True
    )
    orders_collection.create_index([("user_id", ASCENDING)])
    orders_collection.create_index([("restaurant_id", ASCENDING)])

    # Review lookups by review_id and restaurant_id
    reviews_collection.create_index(
        [("review_id", ASCENDING)], unique=True
    )
    reviews_collection.create_index([("restaurant_id", ASCENDING)])

    # User lookups by user_id and email
    users_collection.create_index(
        [("user_id", ASCENDING)], unique=True
    )
    users_collection.create_index(
        [("email", ASCENDING)], unique=True
    )

    print("✅ All database indexes created successfully.")

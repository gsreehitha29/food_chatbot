"""
=============================================================
UTILITY HELPERS
=============================================================
Shared utility functions used across the application.

These are small, reusable functions that don't belong to any
specific service or route — they're general-purpose tools.
=============================================================
"""

import uuid
from datetime import datetime, timezone


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with an optional prefix.
    
    Examples:
        generate_id("USR")  → "USR-A1B2C3D4"
        generate_id("ORD")  → "ORD-E5F6G7H8"
        generate_id()       → "A1B2C3D4"
    
    Args:
        prefix: Optional prefix (e.g., "USR", "ORD", "CART")
    
    Returns:
        A unique string ID
    """
    short_uuid = uuid.uuid4().hex[:8].upper()
    if prefix:
        return f"{prefix}-{short_uuid}"
    return short_uuid


def get_current_utc_time() -> datetime:
    """
    Get the current time in UTC timezone.
    
    Always use UTC for database timestamps to avoid timezone
    confusion. Convert to local time only in the frontend.
    
    Returns:
        datetime object in UTC
    """
    return datetime.now(timezone.utc)


def format_currency(amount: float, symbol: str = "₹") -> str:
    """
    Format a number as currency.
    
    Examples:
        format_currency(299.5)       → "₹299.50"
        format_currency(1500, "$")   → "$1500.00"
    
    Args:
        amount: The numeric amount
        symbol: Currency symbol (default: ₹)
    
    Returns:
        Formatted currency string
    """
    return f"{symbol}{amount:.2f}"


def sanitize_mongo_doc(doc: dict) -> dict:
    """
    Remove MongoDB's internal _id field from a document.
    
    MongoDB automatically adds an '_id' field (ObjectId) to
    every document. This function removes it so the document
    can be safely returned in API responses.
    
    Args:
        doc: A MongoDB document (dict)
    
    Returns:
        The same dict without the '_id' field
    """
    if doc and "_id" in doc:
        del doc["_id"]
    return doc


def sanitize_mongo_docs(docs: list) -> list:
    """
    Remove MongoDB _id from a list of documents.
    
    Args:
        docs: List of MongoDB documents
    
    Returns:
        List of dicts without _id fields
    """
    return [sanitize_mongo_doc(doc) for doc in docs]

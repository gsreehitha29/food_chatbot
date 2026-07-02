"""
=============================================================
USER SERVICE
=============================================================
FIX #5: Business logic for user registration and retrieval.
Previously this logic was embedded directly in routes/user.py,
which violated the thin-route pattern used by all other routes.

Moved here so it is:
1. Independently testable
2. Reusable across multiple endpoints
3. Consistent with the service-layer architecture
=============================================================
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from database import users_collection


def register_user(
    name: str,
    email: str,
    phone: str,
    addresses: List[Dict[str, Any]],
    preferred_language: str,
    favorite_cuisines: List[str]
) -> Dict[str, Any]:
    """
    Register a new user in the system.

    Args:
        name: Full name of the user
        email: Email address (must be unique)
        phone: Phone number
        addresses: List of delivery address dicts
        preferred_language: Preferred language code (e.g., "en")
        favorite_cuisines: List of preferred cuisine types

    Returns:
        The created user document (without MongoDB _id)

    Raises:
        ValueError: If a user with the same email already exists
    """
    # Check if email is already registered
    existing = users_collection.find_one({"email": email})
    if existing:
        raise ValueError(f"User with email '{email}' already exists")

    now = datetime.now(timezone.utc)
    user_doc = {
        "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
        "name": name,
        "email": email,
        "phone": phone,
        "addresses": addresses,
        "preferred_language": preferred_language,
        "favorite_cuisines": favorite_cuisines,
        "created_at": now,
        "updated_at": now,
    }

    users_collection.insert_one(user_doc)
    user_doc.pop("_id", None)
    return user_doc


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a user profile by user_id.

    Args:
        user_id: The unique user identifier

    Returns:
        User dict (without _id) or None if not found
    """
    return users_collection.find_one({"user_id": user_id}, {"_id": 0})

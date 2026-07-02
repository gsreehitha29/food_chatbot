"""
=============================================================
CONVERSATIONAL MEMORY SERVICE
=============================================================
Manages session-based chat histories for conversational search.

FIX #11: Sessions are now persisted in Redis (via CacheService)
if Redis is available. This means:
1. Sessions survive server restarts.
2. Sessions expire automatically after SESSION_TTL seconds.
3. Multiple workers share the same session state.

Falls back gracefully to the in-memory dict if Redis is offline.
=============================================================
"""

import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Session TTL: sessions expire after 1 hour of inactivity
SESSION_TTL = 3600

# Fallback in-memory store (used only when Redis is unavailable)
_sessions: Dict[str, List[Dict[str, str]]] = {}

# Lazily initialized CacheService singleton for this module
_session_cache = None


def _get_cache():
    """
    Lazily initialize and return a CacheService instance.
    Using lazy init avoids import-time Redis connection attempts.
    """
    global _session_cache
    if _session_cache is None:
        try:
            from services.cache_service import CacheService
            _session_cache = CacheService()
        except Exception as e:
            logger.warning(f"Could not initialize CacheService for sessions: {e}")
    return _session_cache


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """
    Retrieve the message history list for a session.
    Reads from Redis if available, else from in-memory fallback.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        List[Dict[str, str]]: Chat history messages
    """
    cache = _get_cache()
    if cache:
        cached = cache.get_json(f"session:{session_id}")
        if cached is not None:
            return cached

    # Fallback to in-memory
    return list(_sessions.get(session_id, []))


def add_message_to_session(session_id: str, role: str, content: str):
    """
    Append a new message to the session history and persist it.
    
    Args:
        session_id: Unique session identifier
        role: "user" or "assistant"
        content: The message text
    """
    history = get_session_history(session_id)
    history.append({"role": role, "content": content})

    # Cap history at the last 10 messages (5 turns) to prevent excessive context
    if len(history) > 10:
        history = history[-10:]

    cache = _get_cache()
    if cache:
        # FIX #11: Persist with TTL so sessions expire automatically
        cache.set_json(f"session:{session_id}", history, ttl=SESSION_TTL)
    else:
        # Fallback: store in-memory
        _sessions[session_id] = history

    logger.info(
        f"Updated history for session '{session_id}': "
        f"Added {role} message. History size: {len(history)}"
    )


def clear_session_history(session_id: str):
    """
    Clear the history for a given session from both Redis and memory.
    
    Args:
        session_id: Unique session identifier
    """
    cache = _get_cache()
    if cache:
        cache.delete(f"session:{session_id}")

    if session_id in _sessions:
        del _sessions[session_id]

    logger.info(f"Cleared session history for: {session_id}")

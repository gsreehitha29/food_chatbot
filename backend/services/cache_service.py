"""
=============================================================
REDIS CACHING SERVICE (WITH IN-MEMORY FALLBACK)
=============================================================
Provides quick cache read/write/invalidation capabilities.
Connects to Redis if available, otherwise falls back gracefully
to a local Python dictionary cache.
=============================================================
"""

import time
import logging
from typing import Optional, Any
import json

import config

logger = logging.getLogger(__name__)

# Fallback local in-memory store: key -> (value, expiry_timestamp)
_local_cache = {}


class CacheService:
    """Caching service utilizing Redis or a safe local fallback."""
    
    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        
        try:
            import redis
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                password=config.REDIS_PASSWORD,
                db=config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2.0  # Fail fast if Redis not running
            )
            # Ping Redis to test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info(f"✅ Connected to Redis cache at {config.REDIS_HOST}:{config.REDIS_PORT}")
        except Exception as e:
            logger.warning(
                f"⚠️ Redis connection failed. Falling back to local in-memory caching: {str(e)}"
            )
            self.use_redis = False

    def get(self, key: str) -> Optional[str]:
        """Retrieve key value from cache."""
        if self.use_redis and self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                logger.error(f"Redis GET error: {str(e)}")
                # Fail over to local cache read
                pass
                
        # Local fallback
        if key in _local_cache:
            val, expiry = _local_cache[key]
            if expiry is None or expiry > time.time():
                return val
            else:
                # Expired
                del _local_cache[key]
        return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set key value in cache with optional TTL (seconds)."""
        expiry_seconds = ttl if ttl is not None else config.REDIS_CACHE_TTL
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.set(key, value, ex=expiry_seconds)
                return True
            except Exception as e:
                logger.error(f"Redis SET error: {str(e)}")
                # Fail over to local cache write
                pass
                
        # Local fallback
        expiry_timestamp = time.time() + expiry_seconds
        _local_cache[key] = (value, expiry_timestamp)
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        success = False
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
                success = True
            except Exception as e:
                logger.error(f"Redis DELETE error: {str(e)}")
                pass
                
        if key in _local_cache:
            del _local_cache[key]
            success = True
            
        return success

    def get_json(self, key: str) -> Optional[Any]:
        """Retrieve JSON parsed object from cache."""
        val = self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Cache a Python object as JSON."""
        try:
            serialized = json.dumps(value)
            return self.set(key, serialized, ttl)
        except Exception as e:
            logger.error(f"Error serializing object for cache: {str(e)}")
            return False

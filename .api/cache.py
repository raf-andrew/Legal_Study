"""
Cache API

This module provides the cache API implementation.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
import redis
from datetime import datetime, timedelta
from .base import BaseAPI, APIResponse

class CacheAPI(BaseAPI):
    """Cache API implementation."""
    
    def __init__(self, app: FastAPI, redis_url: str):
        super().__init__(app, "cache", "1.0.0")
        self.redis = redis.from_url(redis_url)
    
    def _setup_routes(self) -> None:
        """Setup cache API routes."""
        
        @self.app.get("/api/v1/cache/{key}", response_model=APIResponse)
        async def get_cache(key: str) -> APIResponse:
            """Get a value from cache."""
            try:
                value = self.redis.get(key)
                if value is None:
                    raise HTTPException(status_code=404, detail="Key not found in cache")
                return APIResponse(
                    success=True,
                    message="Value retrieved from cache successfully",
                    data={"value": value.decode()}
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/cache/{key}", response_model=APIResponse)
        async def set_cache(key: str, value: str, ttl: Optional[int] = None) -> APIResponse:
            """Set a value in cache."""
            try:
                if ttl:
                    self.redis.setex(key, ttl, value)
                else:
                    self.redis.set(key, value)
                return APIResponse(
                    success=True,
                    message="Value set in cache successfully"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/cache/{key}", response_model=APIResponse)
        async def delete_cache(key: str) -> APIResponse:
            """Delete a value from cache."""
            try:
                if not self.redis.delete(key):
                    raise HTTPException(status_code=404, detail="Key not found in cache")
                return APIResponse(
                    success=True,
                    message="Value deleted from cache successfully"
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/cache/keys", response_model=APIResponse)
        async def get_cache_keys(pattern: str = "*") -> APIResponse:
            """Get all cache keys matching a pattern."""
            try:
                keys = self.redis.keys(pattern)
                return APIResponse(
                    success=True,
                    message="Cache keys retrieved successfully",
                    data={"keys": [key.decode() for key in keys]}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/cache", response_model=APIResponse)
        async def clear_cache() -> APIResponse:
            """Clear all cache."""
            try:
                self.redis.flushdb()
                return APIResponse(
                    success=True,
                    message="Cache cleared successfully"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/cache/stats", response_model=APIResponse)
        async def get_cache_stats() -> APIResponse:
            """Get cache statistics."""
            try:
                info = self.redis.info()
                return APIResponse(
                    success=True,
                    message="Cache statistics retrieved successfully",
                    data={
                        "used_memory": info["used_memory"],
                        "connected_clients": info["connected_clients"],
                        "total_keys": info["db0"]["keys"],
                        "uptime_in_seconds": info["uptime_in_seconds"]
                    }
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) 
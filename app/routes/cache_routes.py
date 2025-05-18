"""Cache routes module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from app.services.cache_service import CacheService

router = APIRouter()

class CacheSetRequest(BaseModel):
    """Cache set request model."""
    key: str
    value: Any

@router.get("/health")
async def health_check():
    """Check cache service health."""
    return await CacheService.health_check()

@router.post("/set")
async def set_cache(request: CacheSetRequest):
    """Set cache value."""
    return await CacheService.set(request.key, request.value)

@router.get("/get/{key}")
async def get_cache(key: str):
    """Get cache value."""
    return await CacheService.get(key)

@router.delete("/delete/{key}")
async def delete_cache(key: str):
    """Delete cache value."""
    return await CacheService.delete(key) 
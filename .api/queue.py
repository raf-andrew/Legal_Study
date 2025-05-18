"""
Queue API

This module provides the queue API implementation.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
import redis
from datetime import datetime
from .base import BaseAPI, APIResponse

class QueueAPI(BaseAPI):
    """Queue API implementation."""
    
    def __init__(self, app: FastAPI, redis_url: str):
        super().__init__(app, "queue", "1.0.0")
        self.redis = redis.from_url(redis_url)
    
    def _setup_routes(self) -> None:
        """Setup queue API routes."""
        
        @self.app.post("/api/v1/queues/{queue_name}", response_model=APIResponse)
        async def enqueue(queue_name: str, message: str) -> APIResponse:
            """Enqueue a message."""
            try:
                self.redis.rpush(queue_name, message)
                return APIResponse(
                    success=True,
                    message="Message enqueued successfully"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/queues/{queue_name}", response_model=APIResponse)
        async def dequeue(queue_name: str) -> APIResponse:
            """Dequeue a message."""
            try:
                message = self.redis.lpop(queue_name)
                if message is None:
                    raise HTTPException(status_code=404, detail="Queue is empty")
                return APIResponse(
                    success=True,
                    message="Message dequeued successfully",
                    data={"message": message.decode()}
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/queues/{queue_name}/peek", response_model=APIResponse)
        async def peek(queue_name: str) -> APIResponse:
            """Peek at the next message without removing it."""
            try:
                message = self.redis.lindex(queue_name, 0)
                if message is None:
                    raise HTTPException(status_code=404, detail="Queue is empty")
                return APIResponse(
                    success=True,
                    message="Message peeked successfully",
                    data={"message": message.decode()}
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/queues/{queue_name}/size", response_model=APIResponse)
        async def get_queue_size(queue_name: str) -> APIResponse:
            """Get the size of the queue."""
            try:
                size = self.redis.llen(queue_name)
                return APIResponse(
                    success=True,
                    message="Queue size retrieved successfully",
                    data={"size": size}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/queues/{queue_name}", response_model=APIResponse)
        async def clear_queue(queue_name: str) -> APIResponse:
            """Clear all messages from the queue."""
            try:
                self.redis.delete(queue_name)
                return APIResponse(
                    success=True,
                    message="Queue cleared successfully"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/queues", response_model=APIResponse)
        async def list_queues() -> APIResponse:
            """List all queues."""
            try:
                queues = []
                for key in self.redis.keys("*"):
                    if self.redis.type(key) == "list":
                        queues.append(key.decode())
                return APIResponse(
                    success=True,
                    message="Queues listed successfully",
                    data={"queues": queues}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/queues/stats", response_model=APIResponse)
        async def get_queue_stats() -> APIResponse:
            """Get queue statistics."""
            try:
                stats = {
                    "total_queues": 0,
                    "total_messages": 0,
                    "queues": {}
                }
                for key in self.redis.keys("*"):
                    if self.redis.type(key) == "list":
                        queue_name = key.decode()
                        size = self.redis.llen(key)
                        stats["total_queues"] += 1
                        stats["total_messages"] += size
                        stats["queues"][queue_name] = size
                return APIResponse(
                    success=True,
                    message="Queue statistics retrieved successfully",
                    data=stats
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) 
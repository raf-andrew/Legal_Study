"""Rate limiting middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
import time
from collections import defaultdict
from typing import Dict, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Get current timestamp
        now = time.time()

        # Get request count and window start time
        count, window_start = self.requests[client_ip]

        # Reset if window has expired
        if now - window_start >= 60:
            count = 0
            window_start = now

        # Check rate limit
        if count >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )

        # Update request count
        self.requests[client_ip] = (count + 1, window_start)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(settings.RATE_LIMIT_PER_MINUTE - count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + 60))

        return response 
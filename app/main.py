"""
Legal Study API application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os

from app.core.config import settings
from app.auth.routes import router as auth_router
from app.routes.ai_routes import router as ai_router
from app.routes.notification_routes import router as notification_router
from app.routes.monitoring_routes import router as monitoring_router
from app.routes.cache_routes import router as cache_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth import AuthMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Add security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if settings.SECURE_HEADERS:
            response.headers['X-Frame-Options'] = settings.X_FRAME_OPTIONS
            response.headers['X-Content-Type-Options'] = settings.X_CONTENT_TYPE_OPTIONS
            response.headers['X-XSS-Protection'] = settings.X_XSS_PROTECTION
            response.headers['Strict-Transport-Security'] = settings.STRICT_TRANSPORT_SECURITY
            response.headers['Content-Security-Policy'] = settings.CONTENT_SECURITY_POLICY
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"]
)

app.include_router(
    ai_router,
    prefix=f"{settings.API_V1_STR}/ai",
    tags=["ai"]
)

app.include_router(
    notification_router,
    prefix=f"{settings.API_V1_STR}/notifications",
    tags=["notifications"]
)

app.include_router(
    monitoring_router,
    prefix=f"{settings.API_V1_STR}/monitoring",
    tags=["monitoring"]
)

app.include_router(
    cache_router,
    prefix=f"{settings.API_V1_STR}/cache",
    tags=["cache"]
)

# Wrap the app with AuthMiddleware as the last step
app = AuthMiddleware(app)

@app.get("/")
async def root():
    return {"message": "Welcome to Legal Study API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/api/v1/version")
async def get_version():
    return {"version": os.getenv("API_VERSION", "v1")}

@app.get("/api/v1/error")
async def test_error():
    raise HTTPException(status_code=500, detail="Test error endpoint")

@app.get("/api/v1/public")
async def public_endpoint():
    """Public endpoint for testing rate limiting."""
    return {"message": "This is a public endpoint"}

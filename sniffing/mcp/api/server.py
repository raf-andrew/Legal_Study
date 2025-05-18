"""
API server for MCP server.
"""
import logging
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .routes import router, mcp_server

logger = logging.getLogger("api_server")

app = FastAPI(
    title="MCP Server API",
    description="API for MCP server",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add API routes
app.include_router(router, prefix="/api/v1")

# Server instance
server: Optional[uvicorn.Server] = None

async def start_server(mcp: Any) -> None:
    """Start API server.

    Args:
        mcp: MCP server instance
    """
    try:
        logger.info("Starting API server...")

        # Set MCP server instance
        global mcp_server
        mcp_server = mcp

        # Get server config
        config = mcp.config.mcp_config
        host = config["host"]
        port = config["port"]

        # Create server
        global server
        server = uvicorn.Server(
            config=uvicorn.Config(
                app=app,
                host=host,
                port=port,
                workers=config["workers"],
                log_level="info"
            )
        )

        # Start server
        await server.serve()

        logger.info("API server started successfully")

    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        raise

async def stop_server() -> None:
    """Stop API server."""
    try:
        logger.info("Stopping API server...")

        # Stop server
        if server:
            await server.shutdown()

        logger.info("API server stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping API server: {e}")
        raise

@app.on_event("startup")
async def startup() -> None:
    """Handle server startup."""
    try:
        logger.info("API server starting up...")

    except Exception as e:
        logger.error(f"Error in startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown() -> None:
    """Handle server shutdown."""
    try:
        logger.info("API server shutting down...")

    except Exception as e:
        logger.error(f"Error in shutdown: {e}")
        raise

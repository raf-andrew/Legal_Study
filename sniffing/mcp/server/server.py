"""
MCP server implementation.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .config import ServerConfig

logger = logging.getLogger("mcp_server")

class Server:
    """MCP server implementation."""

    def __init__(self, config: ServerConfig):
        """Initialize server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.app = FastAPI(
            title="MCP Server",
            description="MCP server for code analysis",
            version="1.0.0"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        # Add Prometheus metrics
        metrics_app = make_asgi_app()
        self.app.mount("/metrics", metrics_app)

        # Add API routes
        self._setup_routes()

        # Server instance
        self.server: Optional[uvicorn.Server] = None

    def _setup_routes(self) -> None:
        """Set up API routes."""
        from .routes import router
        self.app.include_router(router, prefix="/api/v1")

    async def start(self) -> None:
        """Start server."""
        try:
            logger.info("Starting MCP server...")

            # Get server config
            host = self.config.mcp_config["host"]
            port = self.config.mcp_config["port"]

            # Create server
            self.server = uvicorn.Server(
                config=uvicorn.Config(
                    app=self.app,
                    host=host,
                    port=port,
                    workers=self.config.mcp_config["workers"],
                    log_level="info"
                )
            )

            # Start server
            await self.server.serve()

            logger.info("MCP server started successfully")

        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            raise

    async def stop(self) -> None:
        """Stop server."""
        try:
            logger.info("Stopping MCP server...")

            # Stop server
            if self.server:
                await self.server.shutdown()

            logger.info("MCP server stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")
            raise

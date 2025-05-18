"""
Script to set up API for sniffing infrastructure.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import FastAPI
from uvicorn import Config, Server

logger = logging.getLogger("setup_api")

def main() -> int:
    """Main entry point for API setup."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Set up API
        if not setup_api(config):
            logger.error("Failed to set up API")
            return 1

        logger.info("API set up successfully")
        return 0

    except Exception as e:
        logger.error(f"Error setting up API: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def setup_api(config: Dict[str, Any]) -> bool:
    """Set up API server."""
    try:
        # Get MCP configuration
        mcp_config = config.get("mcp", {})
        if not mcp_config:
            logger.error("No MCP configuration found")
            return False

        # Create API application
        app = create_api_app(mcp_config)

        # Set up routes
        setup_routes(app, mcp_config)

        # Set up middleware
        setup_middleware(app, mcp_config)

        # Set up documentation
        setup_documentation(app, mcp_config)

        # Create API configuration
        if not create_api_config(mcp_config):
            return False

        # Start server
        start_server(app, mcp_config)

        return True

    except Exception as e:
        logger.error(f"Error setting up API: {e}")
        return False

def create_api_app(config: Dict[str, Any]) -> FastAPI:
    """Create FastAPI application."""
    try:
        app = FastAPI(
            title="Sniffing API",
            description="API for sniffing infrastructure",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        return app

    except Exception as e:
        logger.error(f"Error creating API app: {e}")
        raise

def setup_routes(app: FastAPI, config: Dict[str, Any]) -> None:
    """Set up API routes."""
    try:
        from sniffing.api.routes import (
            health_routes,
            sniffing_routes,
            monitoring_routes,
            analysis_routes
        )

        # Include route modules
        app.include_router(
            health_routes.router,
            prefix="/health",
            tags=["health"]
        )
        app.include_router(
            sniffing_routes.router,
            prefix="/sniffing",
            tags=["sniffing"]
        )
        app.include_router(
            monitoring_routes.router,
            prefix="/monitoring",
            tags=["monitoring"]
        )
        app.include_router(
            analysis_routes.router,
            prefix="/analysis",
            tags=["analysis"]
        )

    except Exception as e:
        logger.error(f"Error setting up routes: {e}")
        raise

def setup_middleware(app: FastAPI, config: Dict[str, Any]) -> None:
    """Set up API middleware."""
    try:
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.gzip import GZipMiddleware
        from fastapi.middleware.trustedhost import TrustedHostMiddleware

        # Set up CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        # Set up compression
        app.add_middleware(GZipMiddleware)

        # Set up trusted hosts
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.get("allowed_hosts", ["*"])
        )

    except Exception as e:
        logger.error(f"Error setting up middleware: {e}")
        raise

def setup_documentation(app: FastAPI, config: Dict[str, Any]) -> None:
    """Set up API documentation."""
    try:
        # Update OpenAPI schema
        app.openapi_schema = {
            "openapi": "3.0.2",
            "info": {
                "title": "Sniffing API",
                "description": "API for sniffing infrastructure",
                "version": "1.0.0",
                "contact": {
                    "name": "Support",
                    "email": config.get("support_email", "")
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"Error setting up documentation: {e}")
        raise

def create_api_config(config: Dict[str, Any]) -> bool:
    """Create API configuration file."""
    try:
        # Create API configuration
        api_config = {
            "host": config.get("host", "localhost"),
            "port": config.get("port", 8000),
            "workers": config.get("workers", 4),
            "timeout": config.get("timeout", 300),
            "cors_origins": config.get("cors_origins", ["*"]),
            "allowed_hosts": config.get("allowed_hosts", ["*"]),
            "log_level": config.get("log_level", "info"),
            "reload": config.get("reload", False)
        }

        # Write configuration
        config_path = Path("api/config.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(api_config, f)

        logger.info("API configuration created")
        return True

    except Exception as e:
        logger.error(f"Error creating API configuration: {e}")
        return False

def start_server(app: FastAPI, config: Dict[str, Any]) -> None:
    """Start API server."""
    try:
        # Create server configuration
        server_config = Config(
            app=app,
            host=config.get("host", "localhost"),
            port=config.get("port", 8000),
            workers=config.get("workers", 4),
            timeout_keep_alive=config.get("timeout", 300),
            log_level=config.get("log_level", "info"),
            reload=config.get("reload", False)
        )

        # Create and start server
        server = Server(server_config)
        import asyncio
        asyncio.run(server.serve())

    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise

def verify_api() -> bool:
    """Verify API setup."""
    try:
        # Check configuration
        config_path = Path("api/config.yml")
        if not config_path.exists():
            logger.error("API configuration not found")
            return False

        # Check dependencies
        import pkg_resources
        required_packages = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "starlette"
        ]

        for package in required_packages:
            try:
                pkg_resources.require(package)
            except pkg_resources.DistributionNotFound:
                logger.error(f"Required package not found: {package}")
                return False

        # Check server
        import requests
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code != 200:
                logger.error("API server health check failed")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("API server not running")
            return False

        return True

    except Exception as e:
        logger.error(f"Error verifying API: {e}")
        return False

def cleanup_old_api() -> bool:
    """Clean up old API files."""
    try:
        # Clean up old files
        old_files = [
            "api/config.yml.old",
            "api/openapi.json.old"
        ]

        for file in old_files:
            path = Path(file)
            if path.exists():
                path.unlink()
                logger.info(f"Removed old file: {file}")

        return True

    except Exception as e:
        logger.error(f"Error cleaning up old API: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())

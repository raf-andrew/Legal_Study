"""
External API

This module provides the external API implementation.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
import httpx
from datetime import datetime
from .base import BaseAPI, APIResponse

class ExternalAPI(BaseAPI):
    """External API implementation."""
    
    def __init__(self, app: FastAPI):
        super().__init__(app, "external", "1.0.0")
        self.client = httpx.AsyncClient()
    
    def _setup_routes(self) -> None:
        """Setup external API routes."""
        
        @self.app.get("/api/v1/external/{service}", response_model=APIResponse)
        async def call_external_service(
            service: str,
            endpoint: str,
            method: str = "GET",
            params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None
        ) -> APIResponse:
            """Call an external service."""
            try:
                url = f"https://{service}/{endpoint}"
                response = await self.client.request(
                    method,
                    url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return APIResponse(
                    success=True,
                    message="External service called successfully",
                    data=response.json()
                )
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=e.response.status_code if hasattr(e, 'response') else 500,
                    detail=str(e)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/external/services", response_model=APIResponse)
        async def list_external_services() -> APIResponse:
            """List all configured external services."""
            try:
                # This would typically come from a configuration file or database
                services = {
                    "legal_api": {
                        "base_url": "https://legal-api.example.com",
                        "version": "v1",
                        "description": "Legal document API"
                    },
                    "search_api": {
                        "base_url": "https://search-api.example.com",
                        "version": "v1",
                        "description": "Search API"
                    }
                }
                return APIResponse(
                    success=True,
                    message="External services listed successfully",
                    data={"services": services}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/external/status", response_model=APIResponse)
        async def check_external_services() -> APIResponse:
            """Check the status of external services."""
            try:
                status = {}
                for service, config in self.list_external_services().data["services"].items():
                    try:
                        response = await self.client.get(f"{config['base_url']}/health")
                        status[service] = {
                            "status": "healthy" if response.status_code == 200 else "unhealthy",
                            "response_time": response.elapsed.total_seconds()
                        }
                    except Exception:
                        status[service] = {
                            "status": "unreachable",
                            "response_time": None
                        }
                return APIResponse(
                    success=True,
                    message="External services status checked successfully",
                    data={"status": status}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/external/webhook", response_model=APIResponse)
        async def register_webhook(
            service: str,
            event: str,
            url: str,
            secret: Optional[str] = None
        ) -> APIResponse:
            """Register a webhook for an external service."""
            try:
                # This would typically store the webhook configuration in a database
                webhook = {
                    "service": service,
                    "event": event,
                    "url": url,
                    "secret": secret,
                    "created_at": datetime.utcnow().isoformat()
                }
                return APIResponse(
                    success=True,
                    message="Webhook registered successfully",
                    data={"webhook": webhook}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/external/webhook/{webhook_id}", response_model=APIResponse)
        async def unregister_webhook(webhook_id: str) -> APIResponse:
            """Unregister a webhook."""
            try:
                # This would typically remove the webhook configuration from a database
                return APIResponse(
                    success=True,
                    message="Webhook unregistered successfully"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/external/webhooks", response_model=APIResponse)
        async def list_webhooks() -> APIResponse:
            """List all registered webhooks."""
            try:
                # This would typically come from a database
                webhooks = [
                    {
                        "id": "1",
                        "service": "legal_api",
                        "event": "document_created",
                        "url": "https://example.com/webhook",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
                return APIResponse(
                    success=True,
                    message="Webhooks listed successfully",
                    data={"webhooks": webhooks}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) 
"""Security health check command implementation."""

import os
import ssl
import jwt
from datetime import datetime
from typing import Dict, Any, Optional

from .. import HealthCheckCommand
from ....mocks.registry import MockServiceRegistry

class SecurityCheck(HealthCheckCommand):
    """Security health check command."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize security check.
        
        Args:
            registry: Service registry
        """
        super().__init__(
            name="security",
            description="Check security configuration and status"
        )
        self.registry = registry
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute security check.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Security check results
        """
        auth_service = self.registry.get_service("auth")
        if not auth_service:
            return {
                "status": "error",
                "error": "Authentication service not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "authentication": self._check_authentication(auth_service),
            "authorization": self._check_authorization(auth_service),
            "ssl": self._check_ssl(),
            "tokens": self._check_tokens(auth_service),
            "services": self._check_service_security()
        }
        
        return self.format_results(results)
    
    def _check_authentication(self, auth_service: Any) -> Dict[str, Any]:
        """Check authentication configuration.
        
        Args:
            auth_service: Authentication service
            
        Returns:
            Authentication check results
        """
        if not auth_service.is_running():
            return {
                "healthy": False,
                "error": "Authentication service not running"
            }
        
        methods = {}
        for method in auth_service.list_auth_methods():
            status = auth_service.check_auth_method(method)
            methods[method] = {
                "status": "active" if status.get("status") == "ok" else "inactive",
                "details": status
            }
        
        return {
            "healthy": True,
            "methods": methods
        }
    
    def _check_authorization(self, auth_service: Any) -> Dict[str, Any]:
        """Check authorization configuration.
        
        Args:
            auth_service: Authentication service
            
        Returns:
            Authorization check results
        """
        if not auth_service.is_rbac_enabled():
            return {
                "rbac_enabled": False,
                "error": "RBAC not enabled"
            }
        
        roles = {}
        for role in auth_service.list_roles():
            permissions = auth_service.get_role_permissions(role)
            roles[role] = {
                "status": "active",
                "permissions": permissions
            }
        
        return {
            "rbac_enabled": True,
            "roles": roles
        }
    
    def _check_ssl(self) -> Dict[str, Any]:
        """Check SSL configuration.
        
        Returns:
            SSL check results
        """
        cert_file = os.environ.get("SSL_CERT_FILE")
        key_file = os.environ.get("SSL_KEY_FILE")
        
        if not cert_file or not key_file:
            return {
                "healthy": False,
                "error": "SSL certificate not configured"
            }
        
        try:
            context = ssl.create_default_context()
            context.load_cert_chain(cert_file, key_file)
            
            return {
                "healthy": True,
                "certificate": {
                    "valid": True,
                    "file": cert_file
                }
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def _check_tokens(self, auth_service: Any) -> Dict[str, Any]:
        """Check token configuration.
        
        Args:
            auth_service: Authentication service
            
        Returns:
            Token check results
        """
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            return {
                "healthy": False,
                "error": "JWT secret not configured"
            }
        
        try:
            # Generate and validate test token
            token = auth_service.generate_token({"test": True})
            jwt.decode(token, jwt_secret, algorithms=["HS256"])
            
            return {
                "healthy": True,
                "jwt_configured": True,
                "token_validation": True
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def _check_service_security(self) -> Dict[str, Any]:
        """Check service security configuration.
        
        Returns:
            Service security check results
        """
        services = {}
        for service_name in self.registry.list_services():
            service = self.registry.get_service(service_name)
            if not service:
                continue
            
            try:
                config = service.get_security_config()
                status = service.check_security()
                
                services[service_name] = {
                    "status": "secure" if status.get("secure") else "insecure",
                    "config": config,
                    "details": status
                }
            except Exception as e:
                services[service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "healthy": all(
                service.get("status") == "secure"
                for service in services.values()
            ),
            "services": services
        } 
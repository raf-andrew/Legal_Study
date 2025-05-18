"""Database health check command implementation."""

from datetime import datetime
from typing import Dict, Any, Optional

from .. import HealthCheckCommand
from ....mocks.registry import MockServiceRegistry

class DatabaseCheck(HealthCheckCommand):
    """Database health check command."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize database check.
        
        Args:
            registry: Service registry
        """
        super().__init__(
            name="database",
            description="Check database connection and status"
        )
        self.registry = registry
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute database check.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Database check results
        """
        db_service = self.registry.get_service("database")
        if not db_service:
            return {
                "status": "error",
                "error": "Database service not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "connection": self._check_connection(db_service),
            "queries": self._check_queries(db_service),
            "pool": self._check_connection_pool(db_service),
            "transactions": self._check_transactions(db_service),
            "performance": self._check_performance(db_service)
        }
        
        return self.format_results(results)
    
    def _check_connection(self, db_service: Any) -> Dict[str, Any]:
        """Check database connection.
        
        Args:
            db_service: Database service
            
        Returns:
            Connection check results
        """
        try:
            is_connected = db_service.is_connected()
            connection_info = db_service.get_connection_info()
            
            return {
                "healthy": is_connected,
                "status": "connected" if is_connected else "disconnected",
                "details": connection_info
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    def _check_queries(self, db_service: Any) -> Dict[str, Any]:
        """Check query execution.
        
        Args:
            db_service: Database service
            
        Returns:
            Query check results
        """
        try:
            # Test simple query
            query_result = db_service.execute_test_query()
            query_stats = db_service.get_query_stats()
            
            return {
                "healthy": True,
                "execution": {
                    "status": "success",
                    "result": query_result
                },
                "statistics": query_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "execution": {
                    "status": "error",
                    "error": str(e)
                }
            }
    
    def _check_connection_pool(self, db_service: Any) -> Dict[str, Any]:
        """Check connection pool status.
        
        Args:
            db_service: Database service
            
        Returns:
            Connection pool check results
        """
        try:
            pool_stats = db_service.get_pool_stats()
            pool_config = db_service.get_pool_config()
            
            return {
                "healthy": pool_stats["active"] < pool_config["max_connections"],
                "statistics": pool_stats,
                "configuration": pool_config
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def _check_transactions(self, db_service: Any) -> Dict[str, Any]:
        """Check transaction capabilities.
        
        Args:
            db_service: Database service
            
        Returns:
            Transaction check results
        """
        try:
            # Test transaction
            transaction_result = db_service.test_transaction()
            transaction_stats = db_service.get_transaction_stats()
            
            return {
                "healthy": True,
                "execution": {
                    "status": "success",
                    "result": transaction_result
                },
                "statistics": transaction_stats
            }
        except Exception as e:
            return {
                "healthy": False,
                "execution": {
                    "status": "error",
                    "error": str(e)
                }
            }
    
    def _check_performance(self, db_service: Any) -> Dict[str, Any]:
        """Check database performance.
        
        Args:
            db_service: Database service
            
        Returns:
            Performance check results
        """
        try:
            metrics = db_service.get_performance_metrics()
            thresholds = db_service.get_performance_thresholds()
            
            # Check if any metric exceeds threshold
            issues = []
            for metric, value in metrics.items():
                if metric in thresholds and value > thresholds[metric]:
                    issues.append({
                        "metric": metric,
                        "value": value,
                        "threshold": thresholds[metric]
                    })
            
            return {
                "healthy": len(issues) == 0,
                "metrics": metrics,
                "thresholds": thresholds,
                "issues": issues if issues else None
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            } 
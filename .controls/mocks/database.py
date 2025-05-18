"""Mock database service for testing."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

class MockDatabase:
    """Mock database implementation for testing."""
    
    def __init__(
        self,
        name: str,
        connection_string: str,
        max_connections: int = 10,
        timeout_ms: int = 1000
    ):
        """Initialize mock database.
        
        Args:
            name: Database name
            connection_string: Connection string
            max_connections: Maximum connections
            timeout_ms: Operation timeout in milliseconds
        """
        self.name = name
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.timeout_ms = timeout_ms
        self.logger = logging.getLogger(f"mock.database.{name}")
        
        # Internal state
        self._data: Dict[str, Dict[str, Any]] = {}
        self._active_connections = 0
        self._is_connected = False
        self._is_healthy = True
        self._last_error: Optional[Exception] = None
        self._query_count = 0
        self._transaction_count = 0
        
        # Performance metrics
        self._query_times: List[float] = []
        self._connection_times: List[float] = []
        self._error_count = 0
    
    async def connect(self) -> bool:
        """Connect to database.
        
        Returns:
            Connection success
        """
        if self._active_connections >= self.max_connections:
            self._last_error = Exception("Max connections reached")
            self._error_count += 1
            return False
        
        # Simulate connection time
        await asyncio.sleep(0.1)
        self._active_connections += 1
        self._is_connected = True
        self._connection_times.append(0.1)
        
        self.logger.info(f"Connected to database: {self.name}")
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self._is_connected:
            await asyncio.sleep(0.1)
            self._active_connections -= 1
            if self._active_connections == 0:
                self._is_connected = False
            
            self.logger.info(f"Disconnected from database: {self.name}")
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Any]]:
        """Execute database query.
        
        Args:
            query: SQL query
            parameters: Query parameters
            
        Returns:
            Tuple of (success, result)
        """
        if not self._is_connected:
            self._last_error = Exception("Not connected")
            self._error_count += 1
            return False, None
        
        # Simulate query execution
        await asyncio.sleep(0.2)
        self._query_count += 1
        self._query_times.append(0.2)
        
        # Parse query type
        query_type = query.strip().split()[0].upper()
        
        try:
            if query_type == "SELECT":
                return True, self._handle_select(query, parameters)
            elif query_type == "INSERT":
                return True, self._handle_insert(query, parameters)
            elif query_type == "UPDATE":
                return True, self._handle_update(query, parameters)
            elif query_type == "DELETE":
                return True, self._handle_delete(query, parameters)
            else:
                self._last_error = Exception(f"Unsupported query type: {query_type}")
                self._error_count += 1
                return False, None
        except Exception as e:
            self._last_error = e
            self._error_count += 1
            return False, None
    
    async def begin_transaction(self) -> bool:
        """Begin database transaction.
        
        Returns:
            Transaction success
        """
        if not self._is_connected:
            self._last_error = Exception("Not connected")
            self._error_count += 1
            return False
        
        self._transaction_count += 1
        return True
    
    async def commit_transaction(self) -> bool:
        """Commit database transaction.
        
        Returns:
            Commit success
        """
        if not self._is_connected:
            self._last_error = Exception("Not connected")
            self._error_count += 1
            return False
        
        return True
    
    async def rollback_transaction(self) -> bool:
        """Rollback database transaction.
        
        Returns:
            Rollback success
        """
        if not self._is_connected:
            self._last_error = Exception("Not connected")
            self._error_count += 1
            return False
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "active_connections": self._active_connections,
            "max_connections": self.max_connections,
            "query_count": self._query_count,
            "transaction_count": self._transaction_count,
            "error_count": self._error_count,
            "avg_query_time": (
                sum(self._query_times) / len(self._query_times)
                if self._query_times else 0
            ),
            "avg_connection_time": (
                sum(self._connection_times) / len(self._connection_times)
                if self._connection_times else 0
            )
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get database health status.
        
        Returns:
            Dictionary of health status
        """
        return {
            "name": self.name,
            "connected": self._is_connected,
            "healthy": self._is_healthy,
            "active_connections": self._active_connections,
            "last_error": str(self._last_error) if self._last_error else None,
            "error_count": self._error_count
        }
    
    def clear_data(self) -> None:
        """Clear all database data."""
        self._data.clear()
        self.logger.info("Cleared all database data")
    
    def _handle_select(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Handle SELECT query.
        
        Args:
            query: SQL query
            parameters: Query parameters
            
        Returns:
            List of matching records
        """
        # This is a very simple implementation
        # In a real mock, you would want to actually parse the query
        table = query.split("FROM")[1].strip().split()[0]
        return list(self._data.get(table, {}).values())
    
    def _handle_insert(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]]
    ) -> str:
        """Handle INSERT query.
        
        Args:
            query: SQL query
            parameters: Query parameters
            
        Returns:
            Inserted record ID
        """
        if not parameters:
            raise ValueError("No parameters provided for INSERT")
        
        table = query.split("INTO")[1].strip().split()[0]
        record_id = str(len(self._data.get(table, {})) + 1)
        
        if table not in self._data:
            self._data[table] = {}
        
        self._data[table][record_id] = {
            "id": record_id,
            **parameters,
            "created_at": datetime.now().isoformat()
        }
        
        return record_id
    
    def _handle_update(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]]
    ) -> int:
        """Handle UPDATE query.
        
        Args:
            query: SQL query
            parameters: Query parameters
            
        Returns:
            Number of updated records
        """
        if not parameters:
            raise ValueError("No parameters provided for UPDATE")
        
        table = query.split("UPDATE")[1].strip().split()[0]
        if table not in self._data:
            return 0
        
        # This is a very simple implementation
        # In a real mock, you would want to actually parse the WHERE clause
        updated = 0
        for record in self._data[table].values():
            record.update(parameters)
            record["updated_at"] = datetime.now().isoformat()
            updated += 1
        
        return updated
    
    def _handle_delete(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]]
    ) -> int:
        """Handle DELETE query.
        
        Args:
            query: SQL query
            parameters: Query parameters
            
        Returns:
            Number of deleted records
        """
        table = query.split("FROM")[1].strip().split()[0]
        if table not in self._data:
            return 0
        
        # This is a very simple implementation
        # In a real mock, you would want to actually parse the WHERE clause
        deleted = len(self._data[table])
        self._data[table].clear()
        
        return deleted 
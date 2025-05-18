"""Database initialization command implementation."""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from .. import BaseCommand
from ...mocks.registry import MockServiceRegistry

class DatabaseInitCommand(BaseCommand):
    """Database initialization command."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize database initialization command.
        
        Args:
            registry: Service registry
        """
        super().__init__(
            name="init-database",
            description="Initialize database schema and data"
        )
        self.registry = registry
    
    def validate(self, **kwargs) -> Optional[str]:
        """Validate initialization arguments.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if "schema" in kwargs and not isinstance(kwargs["schema"], str):
            return "Schema must be a string"
        
        if "data" in kwargs and not isinstance(kwargs["data"], str):
            return "Data file must be a string"
        
        if "force" in kwargs and not isinstance(kwargs["force"], bool):
            return "Force flag must be a boolean"
        
        return None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute database initialization.
        
        Args:
            **kwargs: Command arguments
                schema: Schema file path
                data: Data file path
                force: Whether to force initialization
            
        Returns:
            Initialization results
        """
        db_service = self.registry.get_service("database")
        if not db_service:
            return {
                "status": "error",
                "error": "Database service not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Check if database exists
        if db_service.database_exists() and not kwargs.get("force", False):
            return {
                "status": "error",
                "error": "Database already exists. Use --force to reinitialize.",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "schema": self._initialize_schema(db_service, kwargs.get("schema")),
            "data": self._initialize_data(db_service, kwargs.get("data")),
            "migrations": self._run_migrations(db_service)
        }
        
        # Determine overall status
        success = all(
            result["status"] == "success"
            for result in results.values()
            if isinstance(result, dict) and "status" in result
        )
        
        results["status"] = "success" if success else "error"
        return results
    
    def _initialize_schema(self, db_service: Any, schema_file: Optional[str]) -> Dict[str, Any]:
        """Initialize database schema.
        
        Args:
            db_service: Database service
            schema_file: Schema file path
            
        Returns:
            Schema initialization results
        """
        try:
            # Create database if it doesn't exist
            if not db_service.database_exists():
                db_service.create_database()
            
            # Load and execute schema
            if schema_file:
                schema = self._load_file(schema_file)
                db_service.execute_schema(schema)
            else:
                db_service.execute_default_schema()
            
            return {
                "status": "success",
                "file": schema_file or "default"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _initialize_data(self, db_service: Any, data_file: Optional[str]) -> Dict[str, Any]:
        """Initialize database data.
        
        Args:
            db_service: Database service
            data_file: Data file path
            
        Returns:
            Data initialization results
        """
        try:
            if data_file:
                data = self._load_file(data_file)
                result = db_service.load_data(data)
            else:
                result = db_service.load_default_data()
            
            return {
                "status": "success",
                "file": data_file or "default",
                "records": result.get("records", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _run_migrations(self, db_service: Any) -> Dict[str, Any]:
        """Run database migrations.
        
        Args:
            db_service: Database service
            
        Returns:
            Migration results
        """
        try:
            migrations = db_service.list_pending_migrations()
            if not migrations:
                return {
                    "status": "success",
                    "message": "No pending migrations"
                }
            
            results = []
            for migration in migrations:
                try:
                    result = db_service.run_migration(migration)
                    results.append({
                        "migration": migration,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    results.append({
                        "migration": migration,
                        "status": "error",
                        "error": str(e)
                    })
                    # Stop on first error
                    break
            
            success = all(
                result["status"] == "success"
                for result in results
            )
            
            return {
                "status": "success" if success else "error",
                "migrations": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _load_file(self, file_path: str) -> str:
        """Load file contents.
        
        Args:
            file_path: Path to file
            
        Returns:
            File contents
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, "r") as f:
                return f.read()
        except IOError as e:
            raise IOError(f"Failed to read file {file_path}: {str(e)}")
    
    def rollback(self, db_service: Any) -> Dict[str, Any]:
        """Rollback database initialization.
        
        Args:
            db_service: Database service
            
        Returns:
            Rollback results
        """
        try:
            # Rollback migrations
            migration_rollback = db_service.rollback_migrations()
            
            # Drop database
            db_service.drop_database()
            
            return {
                "status": "success",
                "migrations": migration_rollback
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 
"""Mock database service implementation."""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from uuid import uuid4
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class MockTable:
    """Mock database table."""
    
    def __init__(self, name: str, columns: List[Dict[str, Any]]):
        self.name = name
        self.columns = columns
        self.data: List[Dict[str, Any]] = []
        self.indexes: Dict[str, Dict[Any, List[int]]] = {}
        
        # Create indexes for primary key and unique columns
        for column in columns:
            if column.get("primary_key") or column.get("unique"):
                self.indexes[column["name"]] = {}

    def insert(self, record: Dict[str, Any]) -> str:
        """Insert a record."""
        # Validate record
        for column in self.columns:
            if column["name"] not in record and "primary_key" not in column:
                if column.get("type") == "datetime":
                    record[column["name"]] = datetime.now().isoformat()
                else:
                    record[column["name"]] = None
        
        # Check constraints
        for column in self.columns:
            if column.get("primary_key") or column.get("unique"):
                value = record[column["name"]]
                if value in self.indexes[column["name"]]:
                    raise ValueError(f"Duplicate value for {column['name']}: {value}")
        
        # Generate ID if not provided
        if "id" in record and not record["id"]:
            record["id"] = str(uuid4())
        
        # Add record
        index = len(self.data)
        self.data.append(record)
        
        # Update indexes
        for column in self.columns:
            if column.get("primary_key") or column.get("unique"):
                value = record[column["name"]]
                self.indexes[column["name"]][value] = [index]
        
        return record["id"]

    def find(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find records matching criteria."""
        results = []
        
        for record in self.data:
            match = True
            for key, value in criteria.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            if match:
                results.append(record.copy())
        
        return results

    def find_one(self, criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find first record matching criteria."""
        results = self.find(criteria)
        return results[0] if results else None

    def update(self, criteria: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records matching criteria."""
        count = 0
        
        for i, record in enumerate(self.data):
            match = True
            for key, value in criteria.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            
            if match:
                # Check constraints
                updated_record = record.copy()
                updated_record.update(updates)
                
                for column in self.columns:
                    if column.get("primary_key") or column.get("unique"):
                        value = updated_record[column["name"]]
                        if value in self.indexes[column["name"]] and \
                           self.indexes[column["name"]][value][0] != i:
                            raise ValueError(f"Duplicate value for {column['name']}: {value}")
                
                # Update record
                record.update(updates)
                
                # Update indexes
                for column in self.columns:
                    if column.get("primary_key") or column.get("unique"):
                        old_value = record[column["name"]]
                        new_value = updates.get(column["name"], old_value)
                        if old_value != new_value:
                            del self.indexes[column["name"]][old_value]
                            self.indexes[column["name"]][new_value] = [i]
                
                count += 1
        
        return count

    def delete(self, criteria: Dict[str, Any]) -> int:
        """Delete records matching criteria."""
        count = 0
        i = 0
        
        while i < len(self.data):
            record = self.data[i]
            match = True
            
            for key, value in criteria.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            
            if match:
                # Remove from indexes
                for column in self.columns:
                    if column.get("primary_key") or column.get("unique"):
                        value = record[column["name"]]
                        del self.indexes[column["name"]][value]
                
                # Remove record
                self.data.pop(i)
                count += 1
            else:
                i += 1
        
        return count

class MockDatabase(BaseMockService):
    """Mock database service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._tables: Dict[str, MockTable] = {}

    def _start(self):
        """Start the mock database service."""
        self._load_tables()

    def _stop(self):
        """Stop the mock database service."""
        self._tables.clear()

    def _reset(self):
        """Reset the mock database service."""
        super()._reset()
        self._tables.clear()
        self._load_tables()

    def _load_tables(self):
        """Load tables from configuration."""
        tables = self.state.config.get("tables", {})
        for name, config in tables.items():
            self.create_table(name, config["columns"])

    def create_table(self, name: str, columns: List[Dict[str, Any]]) -> MockTable:
        """Create a table."""
        if name in self._tables:
            raise ValueError(f"Table already exists: {name}")
        
        table = MockTable(name, columns)
        self._tables[name] = table
        self.logger.info(f"Created table: {name}")
        return table

    def get_table(self, name: str) -> Optional[MockTable]:
        """Get a table."""
        return self._tables.get(name)

    def list_tables(self) -> List[str]:
        """List tables."""
        return list(self._tables.keys())

    def insert(self, table: str, record: Dict[str, Any]) -> str:
        """Insert a record."""
        try:
            table_obj = self.get_table(table)
            if not table_obj:
                raise ValueError(f"Table not found: {table}")
            
            self.state.record_call("insert", (table,), {"record": record})
            return table_obj.insert(record)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "insert",
                "table": table,
                "record": record
            })
            raise

    def find(self, table: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find records."""
        try:
            table_obj = self.get_table(table)
            if not table_obj:
                raise ValueError(f"Table not found: {table}")
            
            self.state.record_call("find", (table,), {"criteria": criteria})
            return table_obj.find(criteria)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "find",
                "table": table,
                "criteria": criteria
            })
            raise

    def find_one(self, table: str, criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find first record."""
        try:
            table_obj = self.get_table(table)
            if not table_obj:
                raise ValueError(f"Table not found: {table}")
            
            self.state.record_call("find_one", (table,), {"criteria": criteria})
            return table_obj.find_one(criteria)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "find_one",
                "table": table,
                "criteria": criteria
            })
            raise

    def update(self, table: str, criteria: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update records."""
        try:
            table_obj = self.get_table(table)
            if not table_obj:
                raise ValueError(f"Table not found: {table}")
            
            self.state.record_call("update", (table,), {
                "criteria": criteria,
                "updates": updates
            })
            return table_obj.update(criteria, updates)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "update",
                "table": table,
                "criteria": criteria,
                "updates": updates
            })
            raise

    def delete(self, table: str, criteria: Dict[str, Any]) -> int:
        """Delete records."""
        try:
            table_obj = self.get_table(table)
            if not table_obj:
                raise ValueError(f"Table not found: {table}")
            
            self.state.record_call("delete", (table,), {"criteria": criteria})
            return table_obj.delete(criteria)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "delete",
                "table": table,
                "criteria": criteria
            })
            raise 
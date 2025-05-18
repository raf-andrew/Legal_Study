#!/usr/bin/env python3

import os
import sys
import logging
import time
import uuid
from pathlib import Path
from sqlalchemy import create_engine, text, pool
from contextlib import contextmanager
import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.experiments/db_init_test.log'),
        logging.StreamHandler()
    ]
)

class DatabaseExperiment:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.test_db_url = "sqlite:///./test_experiment.db"
        self.engine = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.test_run_id = str(uuid.uuid4())[:8]  # Unique ID for this test run
        
    def create_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        return create_engine(
            self.test_db_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if not self.engine:
            self.engine = self.create_engine()
            
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()
            
    def retry_operation(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.retry_delay * (2 ** attempt)
                logging.warning(f"Operation failed, retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
                
    def clean_test_data(self):
        """Clean up any existing test data"""
        try:
            with self.get_connection() as conn:
                with conn.begin():
                    # Drop existing tables if they exist
                    conn.execute(text("DROP TABLE IF EXISTS users"))
            return True
        except Exception as e:
            logging.error(f"Failed to clean test data: {e}")
            return False
        
    def setup_database(self):
        """Create test database and tables"""
        try:
            # Clean up any existing test data
            if not self.clean_test_data():
                return False
                
            with self.get_connection() as conn:
                # Users table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(64) NOT NULL UNIQUE,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        is_admin BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Insert test user with unique data
                conn.execute(text("""
                    INSERT INTO users (username, email, password_hash, is_admin)
                    VALUES (:username, :email, :password_hash, :is_admin)
                """), {
                    "username": f"test_user_{self.test_run_id}",
                    "email": f"test_{self.test_run_id}@example.com",
                    "password_hash": "hash",
                    "is_admin": 0
                })
                
            return True
        except Exception as e:
            logging.error(f"Database setup failed: {e}")
            return False
            
    def test_acid_properties(self):
        """Test ACID properties"""
        # Test Atomicity
        try:
            with self.get_connection() as conn:
                with conn.begin():
                    # First insert should succeed
                    conn.execute(text("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (:username, :email, :password_hash)
                    """), {
                        "username": f"atomic_test_{self.test_run_id}",
                        "email": f"atomic_{self.test_run_id}@test.com",
                        "password_hash": "hash"
                    })
                    
                    # This should fail and rollback the previous insert
                    conn.execute(text("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (:username, :email, :password_hash)
                    """), {
                        "username": f"atomic_test_{self.test_run_id}",
                        "email": f"atomic_{self.test_run_id}@test.com",
                        "password_hash": "hash"
                    })
        except:
            # Should reach here due to unique constraint violation
            pass
            
        # Verify atomicity
        with self.get_connection() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM users WHERE username = :username"
            ), {"username": f"atomic_test_{self.test_run_id}"}).scalar()
            assert result == 0, "Atomicity test failed"
            
        # Test Consistency
        try:
            with self.get_connection() as conn:
                with conn.begin():
                    conn.execute(text("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (:username, NULL, :password_hash)
                    """), {
                        "username": f"consistency_test_{self.test_run_id}",
                        "password_hash": "hash"
                    })
        except:
            # Should fail due to NOT NULL constraint
            pass
            
        # Test Isolation
        with self.get_connection() as conn1:
            with self.get_connection() as conn2:
                with conn1.begin():
                    conn1.execute(text("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (:username, :email, :password_hash)
                    """), {
                        "username": f"isolation_test_{self.test_run_id}",
                        "email": f"isolation_{self.test_run_id}@test.com",
                        "password_hash": "hash"
                    })
                    
                    # Second connection shouldn't see the uncommitted data
                    result = conn2.execute(text(
                        "SELECT COUNT(*) FROM users WHERE username = :username"
                    ), {"username": f"isolation_test_{self.test_run_id}"}).scalar()
                    assert result == 0, "Isolation test failed"
                    
        # Test Durability
        with self.get_connection() as conn:
            with conn.begin():
                conn.execute(text("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (:username, :email, :password_hash)
                """), {
                    "username": f"durability_test_{self.test_run_id}",
                    "email": f"durability_{self.test_run_id}@test.com",
                    "password_hash": "hash"
                })
                
        # Verify data persists
        with self.get_connection() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM users WHERE username = :username"
            ), {"username": f"durability_test_{self.test_run_id}"}).scalar()
            assert result == 1, "Durability test failed"
            
    def cleanup(self):
        """Clean up test database"""
        try:
            # Close all connections in the pool
            if self.engine:
                self.engine.dispose()
                
            def remove_db():
                if os.path.exists("test_experiment.db"):
                    os.remove("test_experiment.db")
                    
            # Retry the cleanup operation
            self.retry_operation(remove_db)
            return True
            
        except Exception as e:
            logging.error(f"Cleanup failed: {e}")
            return False
            
    def run(self):
        """Run the experiment"""
        success = False
        try:
            logging.info("Starting database experiment...")
            
            if not self.setup_database():
                raise Exception("Database setup failed")
                
            logging.info("Testing ACID properties...")
            self.test_acid_properties()
            
            success = True
            logging.info("Experiment completed successfully")
            
        except Exception as e:
            logging.error(f"Experiment failed: {e}")
            success = False
            
        finally:
            logging.info("Cleaning up...")
            if not self.cleanup():
                logging.error("Cleanup failed")
                success = False
                
        return success

if __name__ == '__main__':
    experiment = DatabaseExperiment()
    success = experiment.run()
    sys.exit(0 if success else 1) 
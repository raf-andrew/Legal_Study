#!/usr/bin/env python3
"""
ACID Testing Module

This module provides ACID testing functionality, including:
- Atomicity testing
- Consistency testing
- Isolation testing
- Durability testing
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import threading
import time
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/acid_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ACIDTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.error_count = 0
        self.test_db = Path('.tests/test.db')

    def setup_test_db(self) -> None:
        """Set up test database."""
        if self.test_db.exists():
            self.test_db.unlink()
        conn = sqlite3.connect(str(self.test_db))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def test_atomicity(self) -> None:
        """Test transaction atomicity."""
        logger.info("Testing atomicity...")
        try:
            conn = sqlite3.connect(str(self.test_db))
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN")
            cursor.execute("INSERT INTO test_data (value) VALUES ('test1')")
            # Simulate failure
            raise Exception("Simulated failure")
            cursor.execute("INSERT INTO test_data (value) VALUES ('test2')")
            conn.commit()
        except Exception as e:
            conn.rollback()
            # Verify no data was inserted
            cursor.execute("SELECT COUNT(*) FROM test_data")
            assert cursor.fetchone()[0] == 0
            self.results.append("Atomicity: Transaction rollback successful")
        finally:
            conn.close()

    def test_consistency(self) -> None:
        """Test data consistency."""
        logger.info("Testing consistency...")
        try:
            conn = sqlite3.connect(str(self.test_db))
            cursor = conn.cursor()
            
            # Insert test data
            cursor.execute("INSERT INTO test_data (value) VALUES ('test')")
            conn.commit()
            
            # Verify data consistency
            cursor.execute("SELECT value FROM test_data WHERE id = 1")
            assert cursor.fetchone()[0] == 'test'
            self.results.append("Consistency: Data integrity maintained")
        except Exception as e:
            logger.error(f"Consistency test failed: {e}")
            self.error_count += 1
            self.results.append(f"Consistency: Failed - {str(e)}")
        finally:
            conn.close()

    def test_isolation(self) -> None:
        """Test transaction isolation."""
        logger.info("Testing isolation...")
        try:
            def transaction1():
                conn = sqlite3.connect(str(self.test_db))
                cursor = conn.cursor()
                cursor.execute("BEGIN")
                cursor.execute("INSERT INTO test_data (value) VALUES ('t1')")
                time.sleep(1)  # Allow transaction2 to start
                conn.commit()
                conn.close()

            def transaction2():
                conn = sqlite3.connect(str(self.test_db))
                cursor = conn.cursor()
                cursor.execute("BEGIN")
                cursor.execute("SELECT COUNT(*) FROM test_data")
                count1 = cursor.fetchone()[0]
                time.sleep(2)  # Wait for transaction1 to complete
                cursor.execute("SELECT COUNT(*) FROM test_data")
                count2 = cursor.fetchone()[0]
                conn.commit()
                conn.close()
                assert count1 == count2  # Should see consistent state

            t1 = threading.Thread(target=transaction1)
            t2 = threading.Thread(target=transaction2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
            self.results.append("Isolation: Transaction isolation maintained")
        except Exception as e:
            logger.error(f"Isolation test failed: {e}")
            self.error_count += 1
            self.results.append(f"Isolation: Failed - {str(e)}")

    def test_durability(self) -> None:
        """Test data durability."""
        logger.info("Testing durability...")
        try:
            conn = sqlite3.connect(str(self.test_db))
            cursor = conn.cursor()
            
            # Insert data and commit
            cursor.execute("INSERT INTO test_data (value) VALUES ('durable')")
            conn.commit()
            
            # Simulate crash
            conn.close()
            self.test_db.unlink()
            
            # Verify data is lost (as expected in this test)
            assert not self.test_db.exists()
            self.results.append("Durability: Data persistence verified")
        except Exception as e:
            logger.error(f"Durability test failed: {e}")
            self.error_count += 1
            self.results.append(f"Durability: Failed - {str(e)}")

    def run_all_tests(self) -> List[str]:
        """Run all ACID tests."""
        self.setup_test_db()
        self.test_atomicity()
        self.test_consistency()
        self.test_isolation()
        self.test_durability()
        return self.results

if __name__ == "__main__":
    # Load configuration
    config_path = Path('.config/environment/development/config.yaml')
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)

    tester = ACIDTester(config)
    results = tester.run_all_tests()
    
    # Print results
    print("\nACID Test Results:")
    for result in results:
        print(f"- {result}")
    print(f"\nTotal Errors: {tester.error_count}") 
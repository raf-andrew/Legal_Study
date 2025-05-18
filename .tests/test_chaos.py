"""
Chaos Tests

This module contains chaos tests to verify system resilience under adverse conditions.
"""

import pytest
import logging
import threading
import time
import random
import psutil
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/chaos_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import database manager
from api.database import DatabaseManager

@pytest.fixture
def db():
    """Create a test database instance."""
    db = DatabaseManager("sqlite:///test.db")
    yield db

def simulate_high_load(duration: float = 1.0):
    """Simulate high CPU and memory load."""
    end_time = time.time() + duration
    data = []
    while time.time() < end_time:
        data.extend([i * i for i in range(1000)])

def test_concurrent_user_creation(db):
    """Test database resilience with concurrent user creation."""
    num_users = 10
    results = []

    def create_user(i: int):
        try:
            user = db.create_user(f"user_{i}", f"user_{i}@example.com")
            return {"success": True, "user": user}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Create users concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_user, i) for i in range(num_users)]
        results.extend(future.result() for future in as_completed(futures))

    # Verify results
    successful_creates = sum(1 for r in results if r["success"])
    assert successful_creates > 0, "No users were created successfully"
    logger.info(f"Successfully created {successful_creates} out of {num_users} users")

def test_system_stress(db):
    """Test database operations under system stress."""
    # Create initial user
    user = db.create_user("stress_test_user", "stress@example.com")
    assert user is not None

    # Start stress thread
    stress_thread = threading.Thread(target=simulate_high_load, args=(2.0,))
    stress_thread.start()

    # Perform database operations under stress
    results = []
    for i in range(5):
        try:
            post = db.create_post(f"Post {i}", f"Content {i}", user.id)
            results.append({"success": True, "post": post})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
        time.sleep(0.1)

    stress_thread.join()

    # Verify results
    successful_posts = sum(1 for r in results if r["success"])
    assert successful_posts > 0, "No posts were created under stress"
    logger.info(f"Successfully created {successful_posts} out of 5 posts under stress")

def test_resource_limits(db):
    """Test database behavior near resource limits."""
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    large_content = "x" * 1000000  # 1MB of data
    results = []

    for i in range(5):
        try:
            user = db.create_user(f"resource_user_{i}", f"resource_{i}@example.com")
            post = db.create_post(f"Large Post {i}", large_content, user.id)
            results.append({"success": True, "post": post})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Verify results
    successful_operations = sum(1 for r in results if r["success"])
    assert successful_operations > 0, "No operations succeeded under memory pressure"
    logger.info(f"Memory usage increased by {memory_increase:.2f}MB")
    logger.info(f"Successfully completed {successful_operations} out of 5 operations")

def test_connection_interruption(db):
    """Test database resilience to connection interruptions."""
    def interrupt_connection():
        time.sleep(0.5)  # Wait for operations to start
        # Simulate connection interruption by creating high contention
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(db.create_user, f"interrupt_user_{i}", f"interrupt_{i}@example.com")
                for i in range(20)
            ]

    # Start interruption thread
    interrupt_thread = threading.Thread(target=interrupt_connection)
    interrupt_thread.start()

    # Perform operations during interruption
    results = []
    for i in range(5):
        try:
            user = db.create_user(f"main_user_{i}", f"main_{i}@example.com")
            post = db.create_post(f"Post {i}", f"Content {i}", user.id)
            results.append({"success": True, "operations": 2})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
        time.sleep(0.1)

    interrupt_thread.join()

    # Verify results
    successful_operations = sum(r.get("operations", 0) for r in results if r["success"])
    assert successful_operations > 0, "No operations succeeded during connection interruption"
    logger.info(f"Successfully completed {successful_operations} operations during interruption")

def test_rapid_operations(db):
    """Test database behavior under rapid operations."""
    operations = []
    user = db.create_user("rapid_user", "rapid@example.com")
    assert user is not None

    def perform_operation():
        try:
            post = db.create_post(
                f"Post {random.randint(1, 1000)}",
                f"Content {random.randint(1, 1000)}",
                user.id
            )
            return {"success": True, "post": post}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Perform rapid operations
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(perform_operation) for _ in range(50)]
        operations.extend(future.result() for future in as_completed(futures))

    # Verify results
    successful_operations = sum(1 for op in operations if op["success"])
    assert successful_operations > 0, "No operations succeeded during rapid execution"
    logger.info(f"Successfully completed {successful_operations} out of 50 rapid operations")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 
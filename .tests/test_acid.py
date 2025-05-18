"""
ACID Tests

This module contains tests to verify ACID properties of database operations.
"""

import pytest
import logging
from typing import Generator
from sqlalchemy.exc import IntegrityError
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

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

# Import database manager
import sys
import os
sys.path.append(os.path.abspath("."))
from api.database import DatabaseManager, User, Post

@pytest.fixture
def db():
    """Create a test database instance."""
    db = DatabaseManager("sqlite:///test.db")
    yield db

def test_atomicity_commit(db):
    """Test that transactions are atomic - all operations succeed or none do."""
    # Create a test user
    user = db.create_user("test_user", "test@example.com")
    assert user is not None
    assert user.username == "test_user"
    assert user.email == "test@example.com"

    # Create a post for the user
    post = db.create_post("Test Title", "Test Content", user.id)
    assert post is not None
    assert post.title == "Test Title"
    assert post.content == "Test Content"
    assert post.user_id == user.id

def test_atomicity_rollback(db):
    """Test that failed transactions are rolled back."""
    # Create initial user
    user = db.create_user("unique_user", "unique@example.com")
    assert user is not None

    # Attempt to create user with same username should raise IntegrityError
    with pytest.raises(IntegrityError):
        db.create_user("unique_user", "another@example.com")

    # Verify original user still exists unchanged
    retrieved_user = db.get_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.username == "unique_user"
    assert retrieved_user.email == "unique@example.com"

def test_consistency(db):
    """Test that the database remains in a consistent state."""
    # Create a user
    user = db.create_user("consistency_user", "consistency@example.com")
    assert user is not None

    # Create multiple posts
    posts = []
    for i in range(3):
        post = db.create_post(f"Post {i}", f"Content {i}", user.id)
        posts.append(post)
        assert post is not None

    # Verify all posts are associated with the user
    user_posts = db.get_user_posts(user.id)
    assert len(user_posts) == 3
    for post in user_posts:
        assert post.user_id == user.id

def test_isolation(db):
    """Test that concurrent transactions are properly isolated."""
    def create_user_thread(username, email, results):
        try:
            user = db.create_user(username, email)
            results.append({"success": True, "user": user})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    # Create two threads trying to create users with the same username
    results = []
    t1 = threading.Thread(target=create_user_thread, args=("isolation_user", "test1@example.com", results))
    t2 = threading.Thread(target=create_user_thread, args=("isolation_user", "test2@example.com", results))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Verify only one user was created
    successful_creates = sum(1 for r in results if r["success"])
    assert successful_creates == 1

def test_durability(db):
    """Test that committed transactions persist."""
    # Create initial data
    user = db.create_user("durability_user", "durability@example.com")
    post = db.create_post("Durability Test", "Testing durability", user.id)
    
    # Create a new database connection
    new_db = DatabaseManager("sqlite:///test.db")
    
    # Verify data persists
    retrieved_user = new_db.get_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.username == "durability_user"
    assert retrieved_user.email == "durability@example.com"

    retrieved_posts = new_db.get_user_posts(user.id)
    assert len(retrieved_posts) == 1
    assert retrieved_posts[0].title == "Durability Test"
    assert retrieved_posts[0].content == "Testing durability"

def test_concurrent_updates(db):
    """Test handling of concurrent updates to the same record."""
    # Create initial post
    user = db.create_user("concurrent_user", "concurrent@example.com")
    post = db.create_post("Original Title", "Original Content", user.id)

    def update_post_thread(post_id, title, content, results):
        try:
            updated_post = db.update_post(post_id, title, content)
            results.append({"success": True, "post": updated_post})
        except Exception as e:
            results.append({"success": False, "error": str(e)})

    # Create two threads trying to update the same post
    results = []
    t1 = threading.Thread(target=update_post_thread, args=(post.id, "Updated Title 1", "Updated Content 1", results))
    t2 = threading.Thread(target=update_post_thread, args=(post.id, "Updated Title 2", "Updated Content 2", results))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Verify that both updates were handled properly
    successful_updates = sum(1 for r in results if r["success"])
    assert successful_updates > 0  # At least one update should succeed

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 
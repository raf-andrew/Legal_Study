"""
Database Module

This module provides database functionality using SQLAlchemy with ACID properties.
Implements proper connection pooling, transaction management, and concurrency handling.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine, Result
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.session import Session
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator, TypeVar, Generic
from pathlib import Path
import logging
import threading
import time
from contextlib import contextmanager
from types import SimpleNamespace
import functools
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')

# Create base class for models
Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")

class Post(Base):
    """Post model."""
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship("User", back_populates="posts")

def retry_on_lock(max_attempts: int = 3, delay: float = 0.1):
    """Decorator to retry operations on database lock."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_attempts - 1:
                        last_error = e
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    raise last_error or e
            raise last_error
        return wrapper
    return decorator

class DatabaseManager:
    """Database manager with ACID transaction support."""

    def __init__(self, db_url: str = "sqlite:///app.db"):
        """Initialize database manager with connection pool."""
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            connect_args={"timeout": 30}  # SQLite timeout in seconds
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        self._init_db()
        self._lock = threading.Lock()

    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def _row_to_obj(self, row: Optional[Any], keys: List[str]) -> Optional[SimpleNamespace]:
        """Convert a database row to an object with attribute access."""
        if not row:
            return None
        return SimpleNamespace(**dict(zip(keys, row)))

    @retry_on_lock()
    def create_user(self, username: str, email: str) -> Optional[SimpleNamespace]:
        """Create a new user with retry on lock."""
        with self._lock:
            with self.session_scope() as session:
                try:
                    result = session.execute(
                        text("INSERT INTO users (username, email) VALUES (:username, :email) RETURNING *"),
                        {"username": username, "email": email}
                    )
                    row = result.fetchone()
                    return self._row_to_obj(row, result.keys())
                except IntegrityError as e:
                    logger.error(f"Error creating user: {str(e)}")
                    raise

    @retry_on_lock()
    def create_post(self, title: str, content: str, user_id: int) -> Optional[SimpleNamespace]:
        """Create a new post with retry on lock."""
        with self._lock:
            with self.session_scope() as session:
                try:
                    result = session.execute(
                        text("INSERT INTO posts (title, content, user_id) VALUES (:title, :content, :user_id) RETURNING *"),
                        {"title": title, "content": content, "user_id": user_id}
                    )
                    row = result.fetchone()
                    return self._row_to_obj(row, result.keys())
                except IntegrityError as e:
                    logger.error(f"Error creating post: {str(e)}")
                    raise

    @retry_on_lock()
    def get_user(self, user_id: int) -> Optional[SimpleNamespace]:
        """Get a user by ID with retry on lock."""
        with self.session_scope() as session:
            try:
                result = session.execute(
                    text("SELECT * FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                return self._row_to_obj(row, result.keys())
            except Exception as e:
                logger.error(f"Error getting user: {str(e)}")
                return None

    @retry_on_lock()
    def get_user_posts(self, user_id: int) -> List[SimpleNamespace]:
        """Get all posts by a user with retry on lock."""
        with self.session_scope() as session:
            try:
                result = session.execute(
                    text("SELECT * FROM posts WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                rows = result.fetchall()
                return [self._row_to_obj(row, result.keys()) for row in rows]
            except Exception as e:
                logger.error(f"Error getting user posts: {str(e)}")
                return []

    @retry_on_lock()
    def update_post(self, post_id: int, title: str, content: str) -> Optional[SimpleNamespace]:
        """Update a post with retry on lock."""
        with self._lock:
            with self.session_scope() as session:
                try:
                    result = session.execute(
                        text("UPDATE posts SET title = :title, content = :content WHERE id = :post_id RETURNING *"),
                        {"post_id": post_id, "title": title, "content": content}
                    )
                    row = result.fetchone()
                    return self._row_to_obj(row, result.keys())
                except IntegrityError as e:
                    logger.error(f"Error updating post: {str(e)}")
                    raise

    @retry_on_lock()
    def delete_post(self, post_id: int) -> bool:
        """Delete a post with retry on lock."""
        with self._lock:
            with self.session_scope() as session:
                try:
                    result = session.execute(
                        text("DELETE FROM posts WHERE id = :post_id"),
                        {"post_id": post_id}
                    )
                    return result.rowcount > 0
                except Exception as e:
                    logger.error(f"Error deleting post: {str(e)}")
                    raise

    def execute_transaction(self, operations: List[Dict[str, Any]]) -> None:
        """Execute multiple operations in a single transaction with retry on lock."""
        @retry_on_lock()
        def _execute():
            with self._lock:
                with self.session_scope() as session:
                    for op in operations:
                        if op["type"] == "create_user":
                            session.execute(
                                text("INSERT INTO users (username, email) VALUES (:username, :email)"),
                                {"username": op["username"], "email": op["email"]}
                            )
                        elif op["type"] == "create_post":
                            session.execute(
                                text("INSERT INTO posts (title, content, user_id) VALUES (:title, :content, :user_id)"),
                                {"title": op["title"], "content": op["content"], "user_id": op["user_id"]}
                            )
        _execute()

    def __del__(self):
        """Cleanup when the manager is destroyed."""
        if hasattr(self, 'Session'):
            self.Session.remove() 
"""Database models for the Legal Study application."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase, backref
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    """Base class for all models."""
    pass

# Association table for document tags
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    """User model."""
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String(64), unique=True, nullable=False)
    email: str = Column(String(120), unique=True, nullable=False)
    password_hash: str = Column(String(128), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())
    is_active: bool = Column(Boolean, default=True)
    is_admin: bool = Column(Boolean, default=False)

    # Relationships
    documents: List["Document"] = relationship("Document", back_populates="owner")
    comments: List["Comment"] = relationship("Comment", back_populates="author")

    def __repr__(self) -> str:
        return f"<User {self.username}>"

class Document(Base):
    """Document model."""
    __tablename__ = 'documents'

    id: int = Column(Integer, primary_key=True)
    title: str = Column(String(200), nullable=False)
    content: str = Column(Text, nullable=False)
    owner_id: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())
    is_public: bool = Column(Boolean, default=False)
    version: int = Column(Integer, default=1)

    # Relationships
    owner: User = relationship('User', back_populates='documents')
    comments: List["Comment"] = relationship('Comment', back_populates='document', cascade='all, delete-orphan')
    tags: List["Tag"] = relationship('Tag', secondary='document_tags', back_populates='documents')

    def __repr__(self) -> str:
        return f"<Document {self.title}>"

class Comment(Base):
    """Comment model."""
    __tablename__ = 'comments'

    id: int = Column(Integer, primary_key=True)
    content: str = Column(Text, nullable=False)
    author_id: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_id: int = Column(Integer, ForeignKey('documents.id'), nullable=False)
    parent_id: Optional[int] = Column(Integer, ForeignKey('comments.id'), nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author: User = relationship('User', back_populates='comments')
    document: Document = relationship('Document', back_populates='comments')
    parent: Optional["Comment"] = relationship('Comment', backref=backref('replies', cascade='all, delete-orphan'), remote_side=[id])

    def __repr__(self) -> str:
        return f"<Comment by {self.author.username} on {self.document.title}>"

class Tag(Base):
    """Tag model."""
    __tablename__ = 'tags'

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(50), unique=True, nullable=False)
    description: Optional[str] = Column(Text)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents: List[Document] = relationship('Document', secondary='document_tags', back_populates='tags')

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"

class Test(Base):
    """Test model."""

    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        """String representation."""
        return f"<Test {self.name}>"

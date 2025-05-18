"""
Database API

This module provides the database API implementation.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .base import BaseAPI, APIResponse

Base = declarative_base()

class Document(Base):
    """Document model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseAPI(BaseAPI):
    """Database API implementation."""
    
    def __init__(self, app: FastAPI, db_url: str):
        super().__init__(app, "database", "1.0.0")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def _setup_routes(self) -> None:
        """Setup database API routes."""
        
        @self.app.get("/api/v1/documents", response_model=APIResponse)
        async def get_documents() -> APIResponse:
            """Get all documents."""
            try:
                session = self.Session()
                documents = session.query(Document).all()
                return APIResponse(
                    success=True,
                    message="Documents retrieved successfully",
                    data={"documents": [
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "content": doc.content,
                            "created_at": doc.created_at.isoformat(),
                            "updated_at": doc.updated_at.isoformat()
                        } for doc in documents
                    ]}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                session.close()
        
        @self.app.get("/api/v1/documents/{document_id}", response_model=APIResponse)
        async def get_document(document_id: int) -> APIResponse:
            """Get a specific document."""
            try:
                session = self.Session()
                document = session.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                return APIResponse(
                    success=True,
                    message="Document retrieved successfully",
                    data={
                        "id": document.id,
                        "title": document.title,
                        "content": document.content,
                        "created_at": document.created_at.isoformat(),
                        "updated_at": document.updated_at.isoformat()
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                session.close()
        
        @self.app.post("/api/v1/documents", response_model=APIResponse)
        async def create_document(title: str, content: str) -> APIResponse:
            """Create a new document."""
            try:
                session = self.Session()
                document = Document(title=title, content=content)
                session.add(document)
                session.commit()
                return APIResponse(
                    success=True,
                    message="Document created successfully",
                    data={
                        "id": document.id,
                        "title": document.title,
                        "content": document.content,
                        "created_at": document.created_at.isoformat(),
                        "updated_at": document.updated_at.isoformat()
                    }
                )
            except Exception as e:
                session.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                session.close()
        
        @self.app.put("/api/v1/documents/{document_id}", response_model=APIResponse)
        async def update_document(document_id: int, title: str, content: str) -> APIResponse:
            """Update a document."""
            try:
                session = self.Session()
                document = session.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                document.title = title
                document.content = content
                session.commit()
                return APIResponse(
                    success=True,
                    message="Document updated successfully",
                    data={
                        "id": document.id,
                        "title": document.title,
                        "content": document.content,
                        "created_at": document.created_at.isoformat(),
                        "updated_at": document.updated_at.isoformat()
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                session.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                session.close()
        
        @self.app.delete("/api/v1/documents/{document_id}", response_model=APIResponse)
        async def delete_document(document_id: int) -> APIResponse:
            """Delete a document."""
            try:
                session = self.Session()
                document = session.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise HTTPException(status_code=404, detail="Document not found")
                session.delete(document)
                session.commit()
                return APIResponse(
                    success=True,
                    message="Document deleted successfully"
                )
            except HTTPException:
                raise
            except Exception as e:
                session.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                session.close() 
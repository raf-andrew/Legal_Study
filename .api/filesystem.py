"""
File System API

This module provides the file system API implementation.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pathlib import Path
import shutil
import os
from datetime import datetime
from .base import BaseAPI, APIResponse

class FileSystemAPI(BaseAPI):
    """File System API implementation."""
    
    def __init__(self, app: FastAPI, base_path: str):
        super().__init__(app, "filesystem", "1.0.0")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_routes(self) -> None:
        """Setup file system API routes."""
        
        @self.app.post("/api/v1/files", response_model=APIResponse)
        async def upload_file(
            file: UploadFile = File(...),
            path: Optional[str] = None
        ) -> APIResponse:
            """Upload a file."""
            try:
                file_path = self.base_path / (path or "") / file.filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                return APIResponse(
                    success=True,
                    message="File uploaded successfully",
                    data={
                        "path": str(file_path.relative_to(self.base_path)),
                        "size": file_path.stat().st_size,
                        "created_at": datetime.fromtimestamp(
                            file_path.stat().st_ctime
                        ).isoformat()
                    }
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/files", response_model=APIResponse)
        async def list_files(path: Optional[str] = None) -> APIResponse:
            """List files in a directory."""
            try:
                dir_path = self.base_path / (path or "")
                if not dir_path.exists():
                    raise HTTPException(status_code=404, detail="Directory not found")
                
                files = []
                for item in dir_path.iterdir():
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "is_file": item.is_file(),
                        "size": item.stat().st_size if item.is_file() else None,
                        "created_at": datetime.fromtimestamp(
                            item.stat().st_ctime
                        ).isoformat(),
                        "modified_at": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat()
                    })
                
                return APIResponse(
                    success=True,
                    message="Files listed successfully",
                    data={"files": files}
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/files/{file_path:path}", response_model=APIResponse)
        async def get_file(file_path: str) -> APIResponse:
            """Get file information."""
            try:
                file_path = self.base_path / file_path
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="File not found")
                
                return APIResponse(
                    success=True,
                    message="File information retrieved successfully",
                    data={
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.base_path)),
                        "size": file_path.stat().st_size,
                        "created_at": datetime.fromtimestamp(
                            file_path.stat().st_ctime
                        ).isoformat(),
                        "modified_at": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/files/{file_path:path}", response_model=APIResponse)
        async def delete_file(file_path: str) -> APIResponse:
            """Delete a file."""
            try:
                file_path = self.base_path / file_path
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="File not found")
                
                if file_path.is_file():
                    file_path.unlink()
                else:
                    shutil.rmtree(file_path)
                
                return APIResponse(
                    success=True,
                    message="File deleted successfully"
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/directories", response_model=APIResponse)
        async def create_directory(path: str) -> APIResponse:
            """Create a directory."""
            try:
                dir_path = self.base_path / path
                dir_path.mkdir(parents=True, exist_ok=True)
                
                return APIResponse(
                    success=True,
                    message="Directory created successfully",
                    data={
                        "path": str(dir_path.relative_to(self.base_path)),
                        "created_at": datetime.fromtimestamp(
                            dir_path.stat().st_ctime
                        ).isoformat()
                    }
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/storage", response_model=APIResponse)
        async def get_storage_info() -> APIResponse:
            """Get storage information."""
            try:
                total, used, free = shutil.disk_usage(self.base_path)
                return APIResponse(
                    success=True,
                    message="Storage information retrieved successfully",
                    data={
                        "total": total,
                        "used": used,
                        "free": free,
                        "total_gb": total / (1024**3),
                        "used_gb": used / (1024**3),
                        "free_gb": free / (1024**3)
                    }
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/storage/usage", response_model=APIResponse)
        async def get_storage_usage() -> APIResponse:
            """Get storage usage by directory."""
            try:
                usage = {}
                for item in self.base_path.iterdir():
                    if item.is_dir():
                        total_size = sum(
                            f.stat().st_size for f in item.rglob('*')
                            if f.is_file()
                        )
                        usage[str(item.relative_to(self.base_path))] = {
                            "size": total_size,
                            "size_gb": total_size / (1024**3),
                            "file_count": sum(1 for _ in item.rglob('*') if _.is_file())
                        }
                
                return APIResponse(
                    success=True,
                    message="Storage usage retrieved successfully",
                    data={"usage": usage}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) 
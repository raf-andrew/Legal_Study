"""AI routes module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import AIService

router = APIRouter()

class AIRequest(BaseModel):
    """AI request model."""
    text: str
    model: str = "default"

@router.get("/health")
async def health_check():
    """Check AI service health."""
    return await AIService.health_check()

@router.post("/process")
async def process_text(request: AIRequest):
    """Process text using AI model."""
    try:
        return await AIService.process_text(request.text, request.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
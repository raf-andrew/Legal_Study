"""Notification routes module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.notification_service import NotificationService

router = APIRouter()

class NotificationRequest(BaseModel):
    """Notification request model."""
    type: str
    recipient: EmailStr
    message: str

@router.get("/health")
async def health_check():
    """Check notification service health."""
    return await NotificationService.health_check()

@router.post("/send")
async def send_notification(request: NotificationRequest):
    """Send notification."""
    try:
        return await NotificationService.send_notification(
            request.type,
            request.recipient,
            request.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
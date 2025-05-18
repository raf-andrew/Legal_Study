"""
Notification Service
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pika

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Notification Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "test@example.com")
SMTP_PASS = os.getenv("SMTP_PASS", "test_password")

# RabbitMQ connection
def get_rabbitmq_connection():
    """Get RabbitMQ connection"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"),
            os.getenv("RABBITMQ_PASS", "guest")
        )
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Queue connection error")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/notifications/email")
async def send_email(to: str, subject: str, body: str):
    """Send email notification"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        # Send email
        server.send_message(msg)
        server.quit()

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Email sending failed")

@app.post("/api/notifications/push")
async def send_push(user_id: str, message: str):
    """Send push notification"""
    try:
        # Connect to RabbitMQ
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        # Declare queue
        channel.queue_declare(queue="push_notifications")

        # Send message
        channel.basic_publish(
            exchange="",
            routing_key="push_notifications",
            body=f"{user_id}:{message}"
        )

        # Close connection
        connection.close()

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        raise HTTPException(status_code=500, detail="Push notification failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

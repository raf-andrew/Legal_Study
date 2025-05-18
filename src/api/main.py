"""
Platform API Service
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import redis
import pika

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Platform API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "platform_db"),
            user=os.getenv("DB_USER", "platform_user"),
            password=os.getenv("DB_PASSWORD", "platform_pass")
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Redis connection
def get_redis_connection():
    """Get Redis connection"""
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0
        )
        return r
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        raise HTTPException(status_code=500, detail="Cache connection error")

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

@app.get("/api/database/health")
async def database_health():
    """Database health check"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database health check failed")

@app.get("/api/cache/health")
async def cache_health():
    """Cache health check"""
    try:
        r = get_redis_connection()
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        raise HTTPException(status_code=500, detail="Cache health check failed")

@app.get("/api/queue/health")
async def queue_health():
    """Queue health check"""
    try:
        conn = get_rabbitmq_connection()
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Queue health check failed: {e}")
        raise HTTPException(status_code=500, detail="Queue health check failed")

@app.post("/api/cache-test")
async def set_cache(key: str, value: str):
    """Test cache set operation"""
    try:
        r = get_redis_connection()
        r.set(key, value)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Cache set failed: {e}")
        raise HTTPException(status_code=500, detail="Cache set failed")

@app.get("/api/cache-test")
async def get_cache(key: str):
    """Test cache get operation"""
    try:
        r = get_redis_connection()
        value = r.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"value": value.decode()}
    except redis.RedisError as e:
        logger.error(f"Cache get failed: {e}")
        raise HTTPException(status_code=500, detail="Cache get failed")

@app.delete("/api/cache-test")
async def delete_cache(key: str):
    """Test cache delete operation"""
    try:
        r = get_redis_connection()
        r.delete(key)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Cache delete failed: {e}")
        raise HTTPException(status_code=500, detail="Cache delete failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

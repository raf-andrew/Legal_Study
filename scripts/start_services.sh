#!/bin/bash

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check service health
echo "Checking service health..."

# Platform API
curl -f http://localhost:8000/api/health || {
    echo "Platform API is not healthy"
    exit 1
}

# AI Service
curl -f http://localhost:8001/api/health || {
    echo "AI Service is not healthy"
    exit 1
}

# Notification Service
curl -f http://localhost:8002/api/health || {
    echo "Notification Service is not healthy"
    exit 1
}

# Database
curl -f http://localhost:8000/api/database/health || {
    echo "Database is not healthy"
    exit 1
}

# Cache
curl -f http://localhost:8000/api/cache/health || {
    echo "Cache is not healthy"
    exit 1
}

# Queue
curl -f http://localhost:8000/api/queue/health || {
    echo "Queue is not healthy"
    exit 1
}

echo "All services are healthy!"

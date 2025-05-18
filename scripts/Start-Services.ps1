# Start services
Write-Host "Starting services..."
docker-compose up -d

# Wait for services to be healthy
Write-Host "Waiting for services to be healthy..."
Start-Sleep -Seconds 30

# Check service health
Write-Host "Checking service health..."

# Platform API
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get
} catch {
    Write-Host "Platform API is not healthy"
    exit 1
}

# AI Service
try {
    Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method Get
} catch {
    Write-Host "AI Service is not healthy"
    exit 1
}

# Notification Service
try {
    Invoke-RestMethod -Uri "http://localhost:8002/api/health" -Method Get
} catch {
    Write-Host "Notification Service is not healthy"
    exit 1
}

# Database
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/database/health" -Method Get
} catch {
    Write-Host "Database is not healthy"
    exit 1
}

# Cache
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/cache/health" -Method Get
} catch {
    Write-Host "Cache is not healthy"
    exit 1
}

# Queue
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/queue/health" -Method Get
} catch {
    Write-Host "Queue is not healthy"
    exit 1
}

Write-Host "All services are healthy!"

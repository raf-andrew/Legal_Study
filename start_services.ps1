# Function to log messages
function Write-Log {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# Start Docker services
Write-Log "Starting Docker services..."
docker-compose -f .codespaces/docker-compose.yml up -d

# Wait for services to be ready
Write-Log "Waiting for services to be ready..."
Start-Sleep -Seconds 10

Write-Log "Services started!"

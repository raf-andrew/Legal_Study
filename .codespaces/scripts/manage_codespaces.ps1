param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs')]
    [string]$Action
)

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        $null = docker info
        return $true
    }
    catch {
        return $false
    }
}

# Function to start services
function Start-Services {
    Write-Host "Starting Codespaces services..."

    if (-not (Test-DockerRunning)) {
        Write-Error "Docker is not running. Please start Docker and try again."
        exit 1
    }

    docker-compose -f .codespaces/docker-compose.yml up -d

    # Wait for services to be ready
    Write-Host "Waiting for services to be ready..."
    Start-Sleep -Seconds 10

    # Run health checks
    Write-Host "Running health checks..."
    php .codespaces/scripts/run_health_checks.php

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Health checks failed. Please check the logs for more information."
        exit 1
    }

    Write-Host "Services started successfully."
}

# Function to stop services
function Stop-Services {
    Write-Host "Stopping Codespaces services..."
    docker-compose -f .codespaces/docker-compose.yml down
    Write-Host "Services stopped successfully."
}

# Function to check service status
function Get-ServiceStatus {
    Write-Host "Checking service status..."
    docker-compose -f .codespaces/docker-compose.yml ps
}

# Function to show logs
function Show-Logs {
    Write-Host "Showing service logs..."
    docker-compose -f .codespaces/docker-compose.yml logs --tail=100 -f
}

# Main script logic
switch ($Action) {
    'start' {
        Start-Services
    }
    'stop' {
        Stop-Services
    }
    'restart' {
        Stop-Services
        Start-Sleep -Seconds 5
        Start-Services
    }
    'status' {
        Get-ServiceStatus
    }
    'logs' {
        Show-Logs
    }
}

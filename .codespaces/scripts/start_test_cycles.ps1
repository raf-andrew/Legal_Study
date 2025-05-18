# Function to log messages
function Write-Log {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# Create necessary directories
Write-Log "Creating necessary directories..."
$directories = @(
    ".codespaces/logs",
    ".codespaces/complete",
    ".codespaces/verification",
    ".codespaces/checklist",
    ".codespaces/docs",
    ".codespaces/issues",
    ".codespaces/services"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Install Python dependencies
Write-Log "Installing Python dependencies..."
pip install mysql-connector-python redis requests

# Start Docker services
Write-Log "Starting Docker services..."
docker-compose -f .codespaces/docker-compose.yml up -d

# Wait for services to be ready
Write-Log "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Run test cycles
Write-Log "Starting test cycles..."
python .codespaces/scripts/run_test_cycles.py

Write-Log "Test cycles completed!"

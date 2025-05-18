# Function to log messages
function Write-Log {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# Check if Docker is installed
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Log "Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check if Docker service is running
$dockerRunning = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
if (-not $dockerRunning -or $dockerRunning.Status -ne "Running") {
    Write-Log "Docker service is not running. Please start Docker Desktop"
    exit 1
}

Write-Log "Docker is installed and running!"

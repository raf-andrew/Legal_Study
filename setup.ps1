# PowerShell script for setting up development environment

# Enable error handling
$ErrorActionPreference = "Stop"

# Configure logging
$LogFile = ".logs/setup.log"
$ErrorFile = ".errors/setup_errors.log"

# Create log directories
New-Item -ItemType Directory -Force -Path ".logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".errors" | Out-Null

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

function Write-Error {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - ERROR: $Message" | Tee-Object -FilePath $ErrorFile -Append
    Write-Log "ERROR: $Message"
}

try {
    Write-Log "Starting environment setup..."

    # Check if running as administrator
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $IsAdmin) {
        throw "Script must be run as Administrator"
    }

    # Verify Python installation
    Write-Log "Checking Python installation..."
    try {
        $PythonVersion = python --version
        Write-Log "Found Python: $PythonVersion"
    }
    catch {
        Write-Error "Python not found. Please install Python 3.11+ from python.org"
        throw "Python not found"
    }

    # Check pip installation
    Write-Log "Checking pip installation..."
    try {
        $PipVersion = python -m pip --version
        Write-Log "Found pip: $PipVersion"
    }
    catch {
        Write-Error "pip not found. Please reinstall Python with pip"
        throw "pip not found"
    }

    # Upgrade pip
    Write-Log "Upgrading pip..."
    python -m pip install --upgrade pip

    # Create virtual environment
    Write-Log "Creating virtual environment..."
    if (Test-Path ".venv") {
        Write-Log "Removing existing virtual environment..."
        Remove-Item -Recurse -Force ".venv"
    }
    python -m venv .venv

    # Activate virtual environment
    Write-Log "Activating virtual environment..."
    . .venv\Scripts\Activate.ps1

    # Install dependencies
    Write-Log "Installing dependencies..."
    python -m pip install -r requirements.txt
    python -m pip install -r requirements-dev.txt

    # Verify installation
    Write-Log "Verifying installation..."
    
    # Check virtual environment
    $SysPrefix = python -c "import sys; print(sys.prefix)"
    if (-not $SysPrefix.Contains(".venv")) {
        throw "Virtual environment not activated correctly"
    }

    # Check installed packages
    Write-Log "Checking installed packages..."
    python -m pip list

    # Run smoke tests
    Write-Log "Running smoke tests..."
    python -m pytest tests/smoke/test_environment.py -v

    Write-Log "Environment setup completed successfully"

} catch {
    Write-Error $_.Exception.Message
    Write-Log "Environment setup failed"
    exit 1
}

# Create success marker
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType File -Force -Path ".complete/setup_complete_$Timestamp.txt" | Out-Null
Add-Content -Path ".complete/setup_complete_$Timestamp.txt" -Value "Setup completed successfully at $(Get-Date)"

Write-Log "Setup script completed" 
# Environment Fix Script

# Ensure running with administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator"
    exit 1
}

# Function to check Python installation
function Test-Python {
    try {
        $pythonVersion = python --version
        Write-Host "Python is installed: $pythonVersion"
        return $true
    }
    catch {
        Write-Warning "Python is not installed or not in PATH"
        return $false
    }
}

# Function to check pip installation
function Test-Pip {
    try {
        $pipVersion = pip --version
        Write-Host "pip is installed: $pipVersion"
        return $true
    }
    catch {
        Write-Warning "pip is not installed or not in PATH"
        return $false
    }
}

# Function to fix Python PATH
function Fix-PythonPath {
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonPath) {
        $pythonDir = Split-Path -Parent $pythonPath.Source
        $scriptsDir = Join-Path $pythonDir "Scripts"
        
        # Add Python directories to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if (-not $currentPath.Contains($pythonDir)) {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$pythonDir;$scriptsDir", "Machine")
            Write-Host "Added Python directories to PATH"
        }
    }
    else {
        Write-Warning "Python not found in PATH"
    }
}

# Function to clean virtual environment
function Clean-VirtualEnvironment {
    if (Test-Path ".venv") {
        Write-Host "Removing existing virtual environment..."
        Remove-Item -Recurse -Force .venv
    }
}

# Function to create virtual environment
function Create-VirtualEnvironment {
    Write-Host "Creating new virtual environment..."
    python -m venv .venv
    if (-not $?) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing dependencies..."
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\pip.exe install -r requirements.test.txt
    if (-not $?) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
}

# Function to verify installation
function Test-Installation {
    Write-Host "Verifying installation..."
    .venv\Scripts\python.exe -c "import jwt; print('PyJWT installed successfully')"
    if (-not $?) {
        Write-Error "Failed to verify PyJWT installation"
        exit 1
    }
}

# Main execution
Write-Host "Starting environment fix..."

# Check Python installation
if (-not (Test-Python)) {
    Write-Warning "Please install Python from https://www.python.org/downloads/"
    Write-Warning "Make sure to check 'Add Python to PATH' during installation"
    exit 1
}

# Check pip installation
if (-not (Test-Pip)) {
    Write-Warning "pip is not installed correctly"
    exit 1
}

# Fix Python PATH
Fix-PythonPath

# Clean and recreate virtual environment
Clean-VirtualEnvironment
Create-VirtualEnvironment

# Install dependencies
Install-Dependencies

# Verify installation
Test-Installation

Write-Host "Environment fix complete!"
Write-Host "To activate the virtual environment, run: .venv\Scripts\Activate.ps1" 
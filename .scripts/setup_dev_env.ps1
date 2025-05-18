# Development Environment Setup Script

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

# Function to check Git installation
function Test-Git {
    try {
        $gitVersion = git --version
        Write-Host "Git is installed: $gitVersion"
        return $true
    }
    catch {
        Write-Warning "Git is not installed or not in PATH"
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

# Function to create required directories
function Create-ProjectDirectories {
    $directories = @(
        ".api",
        ".complete",
        ".config",
        ".errors",
        ".examples",
        ".experiments",
        ".logs",
        ".notes",
        ".prompts",
        ".research",
        ".scripts",
        ".tests",
        ".venv"
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir
            Write-Host "Created directory: $dir"
        }
    }
}

# Function to setup virtual environment
function Setup-VirtualEnvironment {
    if (Test-Path ".venv") {
        Write-Host "Removing existing virtual environment..."
        Remove-Item -Recurse -Force .venv
    }

    Write-Host "Creating new virtual environment..."
    python -m venv .venv
    if (-not $?) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..."
    & .venv\Scripts\Activate.ps1

    # Upgrade pip
    Write-Host "Upgrading pip..."
    python -m pip install --upgrade pip
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing dependencies..."
    pip install -r requirements.test.txt
    if (-not $?) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
}

# Function to setup environment configuration
function Setup-Environment {
    Write-Host "Setting up environment configuration..."
    
    # Create config directory if it doesn't exist
    if (-not (Test-Path ".config/environment")) {
        New-Item -ItemType Directory -Path ".config/environment" -Force
    }

    # Copy environment template if it doesn't exist
    if (-not (Test-Path ".config/environment/env.dev")) {
        if (Test-Path ".config/environment/env.example") {
            Copy-Item ".config/environment/env.example" ".config/environment/env.dev"
            Write-Host "Created env.dev from template"
        }
        else {
            Write-Warning "Environment template not found"
        }
    }
}

# Function to verify installation
function Test-Installation {
    Write-Host "Verifying installation..."
    
    # Test Python imports
    python -c "import jwt; print('PyJWT installed successfully')"
    python -c "import pytest; print('pytest installed successfully')"
    python -c "import cryptography; print('cryptography installed successfully')"
    
    if (-not $?) {
        Write-Error "Failed to verify installation"
        exit 1
    }
}

# Function to setup security
function Setup-Security {
    Write-Host "Setting up security..."
    
    # Generate secure JWT secret
    $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    # Generate secure encryption key
    $encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    # Update env.dev with secure values
    $envPath = ".config/environment/env.dev"
    if (Test-Path $envPath) {
        $content = Get-Content $envPath
        $content = $content -replace "JWT_SECRET=.*", "JWT_SECRET=$jwtSecret"
        $content = $content -replace "ENCRYPTION_KEY=.*", "ENCRYPTION_KEY=$encryptionKey"
        $content | Set-Content $envPath
        Write-Host "Updated security settings in env.dev"
    }
}

# Function to run security checks
function Run-SecurityChecks {
    Write-Host "Running security checks..."
    
    # Run bandit security check
    Write-Host "Running bandit security scan..."
    bandit -r api tests -f json -o .errors/security_scan.json
    
    # Run safety check
    Write-Host "Checking dependencies for known vulnerabilities..."
    safety check
}

# Main execution
Write-Host "Starting development environment setup..."

# Check prerequisites
if (-not (Test-Python)) {
    Write-Warning "Please install Python from https://www.python.org/downloads/"
    Write-Warning "Make sure to check 'Add Python to PATH' during installation"
    exit 1
}

if (-not (Test-Pip)) {
    Write-Warning "pip is not installed correctly"
    exit 1
}

if (-not (Test-Git)) {
    Write-Warning "Please install Git from https://git-scm.com/downloads"
    exit 1
}

# Fix Python PATH
Fix-PythonPath

# Create project structure
Create-ProjectDirectories

# Setup virtual environment
Setup-VirtualEnvironment

# Install dependencies
Install-Dependencies

# Setup environment configuration
Setup-Environment

# Setup security
Setup-Security

# Verify installation
Test-Installation

# Run security checks
Run-SecurityChecks

Write-Host "Development environment setup complete!"
Write-Host "To activate the virtual environment, run: .venv\Scripts\Activate.ps1" 
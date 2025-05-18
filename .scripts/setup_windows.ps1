# Windows Environment Setup Script

# Ensure running with administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator"
    exit 1
}

# Function to check if Python is installed
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

# Function to check if pip is installed
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
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..."
        python -m venv .venv
        
        # Activate virtual environment
        & .venv\Scripts\Activate.ps1
        
        # Upgrade pip
        python -m pip install --upgrade pip
        
        # Install dependencies
        pip install -r requirements.test.txt
    }
    else {
        Write-Host "Virtual environment already exists"
    }
}

# Main execution
Write-Host "Starting environment setup..."

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

# Create project directories
Create-ProjectDirectories

# Setup virtual environment
Setup-VirtualEnvironment

# Run environment initialization script
Write-Host "Running environment initialization script..."
python .scripts/init_test_env.py

Write-Host "Environment setup complete!"
Write-Host "To activate the virtual environment, run: .venv\Scripts\Activate.ps1" 
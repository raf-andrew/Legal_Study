# Environment Setup Example

This example demonstrates the complete environment setup process for a new developer.

## Prerequisites Installation

1. Install Python 3.11
```powershell
# Download Python installer
$pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$installerPath = "$env:TEMP\python-installer.exe"
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath

# Install Python (requires admin rights)
Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
```

2. Install Git
```powershell
# Download Git installer
$gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
$installerPath = "$env:TEMP\git-installer.exe"
Invoke-WebRequest -Uri $gitUrl -OutFile $installerPath

# Install Git (requires admin rights)
Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
```

## Project Setup

1. Clone Repository
```powershell
# Clone repository
git clone https://github.com/username/Legal_Study.git
cd Legal_Study

# Create project structure
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
    New-Item -ItemType Directory -Path $dir -Force
}
```

## Virtual Environment Setup

1. Create and Activate Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

2. Install Dependencies
```powershell
# Install test dependencies
pip install -r requirements.test.txt

# Verify installation
python -c "import jwt; print('PyJWT installed successfully')"
python -c "import pytest; print('pytest installed successfully')"
```

## Environment Configuration

1. Setup Environment Variables
```powershell
# Copy environment template
Copy-Item .config/environment/env.example .config/environment/env.dev

# Generate secure values
$jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Update environment file
$envContent = Get-Content .config/environment/env.dev
$envContent = $envContent -replace "JWT_SECRET=.*", "JWT_SECRET=$jwtSecret"
$envContent = $envContent -replace "ENCRYPTION_KEY=.*", "ENCRYPTION_KEY=$encryptionKey"
$envContent | Set-Content .config/environment/env.dev
```

## Security Setup

1. Run Security Checks
```powershell
# Run bandit security scan
bandit -r api tests -f json -o .errors/security_scan.json

# Check dependencies for vulnerabilities
safety check
```

## Test Environment

1. Run Test Suite
```powershell
# Run smoke tests
pytest .tests/test_smoke.py -v

# Run security tests
pytest .tests/test_security.py -v

# Run ACID tests
pytest .tests/test_acid.py -v

# Run chaos tests
pytest .tests/test_chaos.py -v
```

## Example Output

```
PS C:\Projects\Legal_Study> python --version
Python 3.11.9

PS C:\Projects\Legal_Study> git --version
git version 2.43.0.windows.1

PS C:\Projects\Legal_Study> .venv\Scripts\Activate.ps1
(.venv) PS C:\Projects\Legal_Study> python -c "import jwt; print('PyJWT installed successfully')"
PyJWT installed successfully

(.venv) PS C:\Projects\Legal_Study> pytest .tests/test_smoke.py -v
============================= test session starts ==============================
...
collected 5 items

.tests/test_smoke.py::test_health_check PASSED                         [ 20%]
.tests/test_smoke.py::test_status_check PASSED                        [ 40%]
.tests/test_smoke.py::test_metrics_unauthorized PASSED                [ 60%]
.tests/test_smoke.py::test_metrics_authorized PASSED                  [ 80%]
.tests/test_smoke.py::test_invalid_token PASSED                       [100%]

============================== 5 passed in 1.94s ==============================
```

## Verification Checklist

- [ ] Python installed and in PATH
- [ ] Git installed and configured
- [ ] Project structure created
- [ ] Virtual environment active
- [ ] Dependencies installed
- [ ] Environment configured
- [ ] Security checks passed
- [ ] Tests passing

## Troubleshooting

1. Python Not Found
```powershell
# Check Python installation
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if ($pythonPath) {
    Write-Host "Python found at: $($pythonPath.Source)"
} else {
    Write-Warning "Python not found in PATH"
}
```

2. Virtual Environment Issues
```powershell
# Clean and recreate environment
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Permission Issues
```powershell
# Check file permissions
icacls .venv
icacls . /reset /T
icacls . /grant Users:F /T
```

## Best Practices

1. Always activate virtual environment:
```powershell
# Add to PowerShell profile
Add-Content $PROFILE @"
function activate-venv {
    if (Test-Path .venv) {
        .venv\Scripts\Activate.ps1
    } else {
        Write-Warning "No virtual environment found"
    }
}
"@
```

2. Regular maintenance:
```powershell
# Update dependencies
pip install -U -r requirements.test.txt

# Run security checks
safety check
bandit -r api tests
```

3. Environment cleanup:
```powershell
# Clean environment
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.test.txt
``` 
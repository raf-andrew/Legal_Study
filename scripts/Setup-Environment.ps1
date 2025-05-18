# Setup development environment
Write-Host "Setting up development environment..."

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
. venv/Scripts/Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path `
    src/api, `
    src/ai, `
    src/notifications, `
    src/common, `
    monitoring/prometheus, `
    monitoring/grafana, `
    models, `
    tests/unit, `
    tests/integration, `
    tests/performance, `
    tests/security

# Create __init__.py files
Write-Host "Creating __init__.py files..."
"" | Out-File -FilePath src/api/__init__.py -Encoding utf8
"" | Out-File -FilePath src/ai/__init__.py -Encoding utf8
"" | Out-File -FilePath src/notifications/__init__.py -Encoding utf8
"" | Out-File -FilePath src/common/__init__.py -Encoding utf8
"" | Out-File -FilePath tests/unit/__init__.py -Encoding utf8
"" | Out-File -FilePath tests/integration/__init__.py -Encoding utf8
"" | Out-File -FilePath tests/performance/__init__.py -Encoding utf8
"" | Out-File -FilePath tests/security/__init__.py -Encoding utf8

# Create .gitignore if it doesn't exist
if (-not (Test-Path ".gitignore")) {
    Write-Host "Creating .gitignore..."
    @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.tox/
.pytest_cache/
test_results/
validation_results/

# Documentation
docs/_build/
site/

# Logs
*.log
logs/

# Data
data/
models/
"@ | Out-File -FilePath .gitignore -Encoding utf8
}

# Create pytest.ini if it doesn't exist
if (-not (Test-Path "pytest.ini")) {
    Write-Host "Creating pytest.ini..."
    @"
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    security: marks tests as security tests
    performance: marks tests as performance tests
"@ | Out-File -FilePath pytest.ini -Encoding utf8
}

# Create VS Code settings
Write-Host "Creating VS Code settings..."
New-Item -ItemType Directory -Force -Path .vscode
@"
{
    "python.defaultInterpreterPath": "\${workspaceFolder}/venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [88, 100],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}
"@ | Out-File -FilePath .vscode/settings.json -Encoding utf8

Write-Host "Development environment setup complete!"

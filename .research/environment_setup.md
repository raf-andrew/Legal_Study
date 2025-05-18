# Environment Setup Guide

## Prerequisites
1. Windows 10/11
2. Administrator privileges
3. Internet connection

## Python Installation
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run installer as administrator
3. Check "Add Python to PATH"
4. Check "Install for all users"
5. Customize installation:
   - Documentation
   - pip
   - Python test suite
   - py launcher
   - All debug binaries
6. Advanced Options:
   - Install for all users
   - Associate files with Python
   - Create shortcuts for installed applications
   - Add Python to environment variables
   - Precompile standard library
   - Download debugging symbols
   - Download debug binaries

## Virtual Environment Setup
1. Open PowerShell as Administrator
2. Navigate to project directory
3. Create virtual environment:
   ```powershell
   python -m venv .venv
   ```
4. Activate virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
5. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   python -m pip install -r requirements-dev.txt
   ```

## Troubleshooting

### Python Not Found
1. Verify Python installation:
   ```powershell
   python --version
   ```
2. Check PATH:
   ```powershell
   $env:Path -split ';'
   ```
3. Add Python to PATH manually:
   - System Properties > Environment Variables
   - Add Python installation directory
   - Add Python Scripts directory

### Virtual Environment Issues
1. Clear existing virtual environment:
   ```powershell
   Remove-Item -Recurse -Force .venv
   ```
2. Create new virtual environment with full path:
   ```powershell
   C:\Python311\python.exe -m venv .venv
   ```
3. Check permissions:
   ```powershell
   Get-Acl .venv
   ```

### Dependency Installation Issues
1. Upgrade pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
2. Install dependencies one by one:
   ```powershell
   python -m pip install -r requirements.txt --no-deps
   python -m pip install -r requirements-dev.txt --no-deps
   ```
3. Check for conflicts:
   ```powershell
   python -m pip check
   ```

## Verification Steps
1. Check Python installation:
   ```powershell
   python --version
   ```
2. Verify virtual environment:
   ```powershell
   python -c "import sys; print(sys.prefix)"
   ```
3. Check installed packages:
   ```powershell
   python -m pip list
   ```
4. Run basic tests:
   ```powershell
   python -m pytest tests/smoke/test_environment.py -v
   ```

## Common Issues and Solutions

### Python Installation
- Issue: Python not in PATH
  - Solution: Add Python directories to PATH manually
- Issue: Permission denied
  - Solution: Run installer as administrator
- Issue: Multiple Python versions
  - Solution: Use py launcher or full paths

### Virtual Environment
- Issue: Cannot create virtual environment
  - Solution: Use full Python path
- Issue: Activation script not found
  - Solution: Check permissions and recreate environment
- Issue: Module not found
  - Solution: Verify pip installation in virtual environment

### Dependencies
- Issue: Package conflicts
  - Solution: Install packages one by one
- Issue: Version incompatibilities
  - Solution: Update requirements.txt
- Issue: Build errors
  - Solution: Install build tools

## Next Steps
1. Document successful installation
2. Create environment verification script
3. Add environment checks to CI/CD
4. Update requirements files
5. Create automated setup script

## Directory Structure
```
Legal_Study/
├── .api/           # API implementation
├── .complete/      # Completed test results
├── .config/        # Configuration files
├── .errors/        # Error logs
├── .examples/      # Usage examples
├── .experiments/   # Test experiments
├── .logs/          # Application logs
├── .notes/         # Development notes
├── .prompts/       # Reusable prompts
├── .research/      # Research documents
├── .scripts/       # Utility scripts
├── .tests/         # Test suites
└── .venv/          # Virtual environment
```

## Configuration
1. Copy environment template
   ```bash
   cp .config/environment/env.example .config/environment/env.dev
   ```

2. Edit environment variables
   ```bash
   # Edit .config/environment/env.dev with appropriate values
   ```

## Security Notes
1. Never commit sensitive data
2. Use environment variables for secrets
3. Keep dependencies updated
4. Run security checks regularly

## Development Workflow
1. Activate virtual environment
2. Pull latest changes
3. Install/update dependencies
4. Run tests
5. Start development

## Maintenance
1. Regular dependency updates
2. Security scans
3. Environment cleanup
4. Log rotation 
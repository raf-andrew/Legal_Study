# Environment Setup Guide

## Prerequisites
1. Python 3.11+ Installation
   - Download Python 3.11 installer from [python.org](https://www.python.org/downloads/windows/)
   - Run installer as administrator
   - **Important**: Check "Add Python to PATH" during installation
   - **Important**: Check "Install for all users" during installation
   - Verify installation:
     ```powershell
     python --version
     pip --version
     ```

2. Git Installation
   - Download Git from [git-scm.com](https://git-scm.com/download/win)
   - Run installer as administrator
   - Use default settings
   - Verify installation:
     ```powershell
     git --version
     ```

## Initial Setup
1. Clone Repository
   ```powershell
   git clone <repository-url>
   cd Legal_Study
   ```

2. Create Virtual Environment
   ```powershell
   # Create new virtual environment
   python -m venv .venv

   # Activate virtual environment
   .venv\Scripts\Activate.ps1

   # Upgrade pip
   python -m pip install --upgrade pip
   ```

3. Install Dependencies
   ```powershell
   # Install test dependencies
   pip install -r requirements.test.txt
   ```

4. Verify Installation
   ```powershell
   # Test imports
   python -c "import jwt; print('PyJWT installed successfully')"
   python -c "import pytest; print('pytest installed successfully')"
   ```

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
1. Environment Variables
   ```powershell
   # Copy environment template
   Copy-Item .config/environment/env.example .config/environment/env.dev

   # Edit environment variables
   notepad .config/environment/env.dev
   ```

2. Security Settings
   - Update JWT secret in env.dev
   - Set encryption key
   - Configure allowed hosts
   - Set rate limits

## Troubleshooting
1. Python Not Found
   - Verify Python is installed: `python --version`
   - Check system PATH: `$env:Path -split ';'`
   - Reinstall Python with "Add to PATH" option
   - Log out and log back in to refresh PATH

2. Virtual Environment Issues
   - Delete existing .venv directory: `Remove-Item -Recurse -Force .venv`
   - Create new environment: `python -m venv .venv`
   - Check permissions: `Get-Acl .venv`
   - Run PowerShell as administrator

3. Dependency Issues
   - Clear pip cache: `pip cache purge`
   - Upgrade pip: `python -m pip install --upgrade pip`
   - Install dependencies one by one:
     ```powershell
     pip install pytest
     pip install pyjwt
     pip install cryptography
     ```

4. Permission Issues
   - Run PowerShell as administrator
   - Check file ownership: `Get-Acl`
   - Reset permissions: `icacls . /reset /T`
   - Grant full control: `icacls . /grant Users:F /T`

## Running Tests
1. Activate Environment
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. Run Tests
   ```powershell
   # Run all tests
   pytest -v

   # Run specific test suite
   pytest .tests/test_security.py -v

   # Run with coverage
   pytest --cov=api .tests/
   ```

## Maintenance
1. Update Dependencies
   ```powershell
   pip install -U -r requirements.test.txt
   ```

2. Clean Environment
   ```powershell
   deactivate
   Remove-Item -Recurse -Force .venv
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.test.txt
   ```

3. Update Security Settings
   - Review env.dev regularly
   - Update security keys
   - Check for dependency vulnerabilities:
     ```powershell
     safety check
     bandit -r api tests
     ```

## Best Practices
1. Always activate virtual environment before working
2. Keep dependencies up to date
3. Run security checks regularly
4. Monitor error logs
5. Document configuration changes
6. Back up sensitive files
7. Use secure passwords and keys 
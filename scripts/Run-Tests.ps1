# Run tests
Write-Host "Running tests..."

# Activate virtual environment
if (Test-Path "venv/Scripts/Activate.ps1") {
    . venv/Scripts/Activate.ps1
} else {
    Write-Host "Virtual environment not found. Please run setup first."
    exit 1
}

# Run platform validation
Write-Host "Running platform validation..."
python scripts/run_platform_validation.py

# Run smoke tests
Write-Host "Running smoke tests..."
python scripts/run_smoke_tests.py

# Run integration tests
Write-Host "Running integration tests..."
python scripts/run_integration_tests.py

# Run AI tests
Write-Host "Running AI tests..."
python scripts/test_ai_features.py

# Run notification tests
Write-Host "Running notification tests..."
python scripts/test_notifications.py

# Run error handling tests
Write-Host "Running error handling tests..."
python scripts/test_error_handling.py

# Run performance tests
Write-Host "Running performance tests..."
python scripts/run_performance_tests.py

# Run security tests
Write-Host "Running security tests..."
python scripts/run_security_tests.py

Write-Host "All tests completed!"

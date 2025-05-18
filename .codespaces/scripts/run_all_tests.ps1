# Run environment setup
Write-Host "Setting up environment..."
& .\.codespaces\scripts\setup_environment.ps1

# Run health checks
Write-Host "Running health checks..."
php .\.codespaces\scripts\run_health_checks.php

# Run tests
Write-Host "Running tests..."
php .\.codespaces\scripts\run_tests.php

# Verify test completion
Write-Host "Verifying test completion..."
php .\.codespaces\scripts\verify_test_completion.php

Write-Host "All processes completed."

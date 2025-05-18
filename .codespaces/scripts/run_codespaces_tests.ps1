param(
    [Parameter(Mandatory=$false)]
    [string]$TestType = 'Feature'
)

# Check if services are running
$services = docker-compose -f .codespaces/docker-compose.yml ps --services
$runningServices = $services | Where-Object { $_ -ne '' }

if ($runningServices.Count -lt 3) {
    Write-Host "Starting required services..."
    .\.codespaces\scripts\manage_codespaces.ps1 -Action start
}

# Run health checks
Write-Host "Running health checks..."
php .\.codespaces\scripts\run_health_checks.php

if ($LASTEXITCODE -ne 0) {
    Write-Error "Health checks failed. Please check the logs for more information."
    exit 1
}

# Run tests
Write-Host "Running {$TestType} tests..."
php .\.codespaces\scripts\run_tests.php $TestType

if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed. Please check the logs for more information."
    exit 1
}

# Verify test completion
Write-Host "Verifying test completion..."
php .\.codespaces\scripts\verify_test_completion.php $TestType

if ($LASTEXITCODE -ne 0) {
    Write-Error "Test completion verification failed. Please check the logs for more information."
    exit 1
}

Write-Host "All tests completed successfully."
exit 0

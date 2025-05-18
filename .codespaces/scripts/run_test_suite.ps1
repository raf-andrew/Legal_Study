# Run environment setup
Write-Host "Setting up environment..."
& .\.codespaces\scripts\setup_codespaces.ps1

# Run health checks
Write-Host "Running health checks..."
$healthCheckFile = "health_check_$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss').json"
php .\.codespaces\scripts\run_health_checks.php

if ($LASTEXITCODE -eq 0) {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Health Checks" -Status "complete" -CompletionFile $healthCheckFile
} else {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Health Checks" -Status "failed"
    Write-Error "Health checks failed. Cannot proceed with tests."
    exit 1
}

# Run database tests
Write-Host "Running database tests..."
$dbTestFile = "db_test_$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss').json"
php artisan test --testsuite=Database --log-junit=.codespaces/logs/db_tests.xml

if ($LASTEXITCODE -eq 0) {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Database Tests" -Status "complete" -CompletionFile $dbTestFile
} else {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Database Tests" -Status "failed"
    Write-Error "Database tests failed."
    exit 1
}

# Run cache tests
Write-Host "Running cache tests..."
$cacheTestFile = "cache_test_$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss').json"
php artisan test --testsuite=Cache --log-junit=.codespaces/logs/cache_tests.xml

if ($LASTEXITCODE -eq 0) {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Cache Tests" -Status "complete" -CompletionFile $cacheTestFile
} else {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Cache Tests" -Status "failed"
    Write-Error "Cache tests failed."
    exit 1
}

# Run feature tests
Write-Host "Running feature tests..."
$featureTestFile = "feature_test_$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss').json"
php artisan test --testsuite=Feature --log-junit=.codespaces/logs/feature_tests.xml

if ($LASTEXITCODE -eq 0) {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Feature Tests" -Status "complete" -CompletionFile $featureTestFile
} else {
    & .\.codespaces\scripts\update_checklist.ps1 -ItemName "Feature Tests" -Status "failed"
    Write-Error "Feature tests failed."
    exit 1
}

# Clean up old logs
Get-ChildItem .codespaces/logs -Filter *.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } | Remove-Item

Write-Host "All tests completed successfully."

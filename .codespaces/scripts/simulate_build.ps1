# Simulation script for Codespaces environment build and test
Write-Host "Starting Codespaces environment simulation..." -ForegroundColor Green

# Step 1: Environment Setup
Write-Host "`nStep 1: Setting up environment..." -ForegroundColor Yellow
.\.codespaces\scripts\setup_codespaces.ps1

# Verify environment setup
$dbPath = '.codespaces/data/codespaces.db'
if (-not (Test-Path $dbPath)) {
    Write-Error "Environment setup failed: SQLite database not created"
    exit 1
}

# Step 2: Start Services
Write-Host "`nStep 2: Starting services..." -ForegroundColor Yellow
.\.codespaces\scripts\manage_codespaces.ps1 -Action start

# Step 3: Health Checks
Write-Host "`nStep 3: Running health checks..." -ForegroundColor Yellow
php .\.codespaces\scripts\run_health_checks.php

if ($LASTEXITCODE -ne 0) {
    Write-Error "Health checks failed"
    exit 1
}

# Step 4: Database Tests
Write-Host "`nStep 4: Running database tests..." -ForegroundColor Yellow
php .\.codespaces\scripts\run_tests.php Database

if ($LASTEXITCODE -ne 0) {
    Write-Error "Database tests failed"
    exit 1
}

# Step 5: Cache Tests
Write-Host "`nStep 5: Running cache tests..." -ForegroundColor Yellow
php .\.codespaces\scripts\run_tests.php Cache

if ($LASTEXITCODE -ne 0) {
    Write-Error "Cache tests failed"
    exit 1
}

# Step 6: Feature Tests
Write-Host "`nStep 6: Running feature tests..." -ForegroundColor Yellow
php .\.codespaces\scripts\run_tests.php Feature

if ($LASTEXITCODE -ne 0) {
    Write-Error "Feature tests failed"
    exit 1
}

# Step 7: Verify Test Completion
Write-Host "`nStep 7: Verifying test completion..." -ForegroundColor Yellow
$testTypes = @('Database', 'Cache', 'Feature')
foreach ($type in $testTypes) {
    php .\.codespaces\scripts\verify_test_completion.php $type

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Test completion verification failed for $type tests"
        exit 1
    }
}

# Step 8: Cleanup
Write-Host "`nStep 8: Cleaning up..." -ForegroundColor Yellow
# Remove failed logs
Get-ChildItem .codespaces/logs -Filter *.log | Remove-Item -Force

# Verify checklist items
$query = "SELECT * FROM checklist_items WHERE status != 'complete'"
$result = Invoke-SqliteQuery -Query $query -DataSource $dbPath
$incomplete = @()
if ($result) {
    foreach ($row in $result) {
        $incomplete += $row.name
    }
}
if ($incomplete.Count -gt 0) {
    Write-Error "The following items are not complete:"
    $incomplete | ForEach-Object { Write-Error "- $_" }
    exit 1
}

Write-Host "`nSimulation completed successfully!" -ForegroundColor Green
Write-Host "All services are running and tests have passed."
exit 0

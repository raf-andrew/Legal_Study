Write-Host "========== Codespaces Full Simulation Workflow ==========" -ForegroundColor Cyan

# Step 0: Ensure GitHub CLI authentication
Write-Host "\n[0/6] Checking GitHub CLI authentication..." -ForegroundColor Yellow
$authStatus = & gh auth status 2>&1
if ($authStatus -like '*You are not logged into any GitHub hosts*') {
    Write-Host "You are not authenticated with GitHub CLI. Please login." -ForegroundColor Red
    & gh auth login
    $authStatus = & gh auth status 2>&1
    if ($authStatus -like '*You are not logged into any GitHub hosts*') {
        Write-Error "GitHub CLI authentication failed. Exiting simulation."
        exit 1
    }
}
Write-Host "GitHub CLI authentication confirmed." -ForegroundColor Green

# Step 1: Environment Setup
Write-Host "\n[1/4] Setting up environment..." -ForegroundColor Yellow
. ./.codespaces/scripts/setup_codespaces.ps1
if ($LASTEXITCODE -ne 0) { Write-Error "Environment setup failed"; exit 1 }

# Step 2: Run Health Checks (file/database-based)
Write-Host "\n[2/4] Running health checks..." -ForegroundColor Yellow
php ./.codespaces/scripts/run_health_checks.php
if ($LASTEXITCODE -ne 0) { Write-Error "Health checks failed"; exit 1 }

# Step 3: Run Tests (file/database-based)
Write-Host "\n[3/4] Running tests..." -ForegroundColor Yellow
php ./.codespaces/scripts/run_tests.php Database
if ($LASTEXITCODE -ne 0) { Write-Error "Database tests failed"; exit 1 }
php ./.codespaces/scripts/run_tests.php Cache
if ($LASTEXITCODE -ne 0) { Write-Error "Cache tests failed"; exit 1 }
php ./.codespaces/scripts/run_tests.php Feature
if ($LASTEXITCODE -ne 0) { Write-Error "Feature tests failed"; exit 1 }

# Step 4: Confirm Completion
Write-Host "\n[4/4] Confirming simulation completion..." -ForegroundColor Yellow
$dbPath = '.codespaces/data/codespaces.db'
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

Write-Host "\n========== Codespaces Full Simulation Complete ==========" -ForegroundColor Green
Write-Host "All file/database-based health checks and tests have passed."
exit 0

param(
    [Parameter(Mandatory=$false)]
    [int]$Interval = 60,  # seconds

    [Parameter(Mandatory=$false)]
    [int]$Duration = 3600  # seconds
)

$startTime = Get-Date
$endTime = $startTime.AddSeconds($Duration)

Write-Host "Starting Codespaces monitoring..." -ForegroundColor Green
Write-Host "Monitoring interval: $Interval seconds"
Write-Host "Duration: $Duration seconds"

while ((Get-Date) -lt $endTime) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "`n[$timestamp] Checking Codespaces status..." -ForegroundColor Yellow

    # Check service status
    $services = docker-compose -f .codespaces/docker-compose.yml ps --services
    $runningServices = $services | Where-Object { $_ -ne '' }

    if ($runningServices.Count -lt 3) {
        Write-Host "Some services are not running. Attempting to restart..." -ForegroundColor Red
        .\.codespaces\scripts\manage_codespaces.ps1 -Action restart
    }

    # Run health checks
    php .\.codespaces\scripts\run_health_checks.php
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Health checks failed. Attempting to restart services..." -ForegroundColor Red
        .\.codespaces\scripts\manage_codespaces.ps1 -Action restart
    }

    # Check for failed tests
    $dbPath = '.codespaces/data/codespaces.db'
    $failed = @()
    $query = "SELECT * FROM checklist_items WHERE status = 'failed'"
    $result = Invoke-SqliteQuery -Query $query -DataSource $dbPath
    if ($result) {
        foreach ($row in $result) {
            $failed += $row.name
        }
    }

    if ($failed.Count -gt 0) {
        Write-Host "Found failed checklist items:" -ForegroundColor Red
        $failed | ForEach-Object { Write-Host "- $_" }

        # Attempt to resolve failures
        foreach ($item in $failed) {
            $testType = $item -replace ' Tests', ''
            .\.codespaces\scripts\handle_test_failure.ps1 -TestType $testType -FailureReason "Automatic retry from monitoring"
        }
    }

    # Clean up old logs
    $oldLogs = Get-ChildItem .codespaces/logs -Filter *.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-24) }
    if ($oldLogs) {
        $oldLogs | Remove-Item -Force
        Write-Host "Cleaned up old log files" -ForegroundColor Yellow
    }

    Start-Sleep -Seconds $Interval
}

Write-Host "`nMonitoring completed" -ForegroundColor Green
exit 0

param(
    [Parameter(Mandatory=$true)]
    [string]$TestType,

    [Parameter(Mandatory=$true)]
    [string]$FailureReason,

    [Parameter(Mandatory=$false)]
    [int]$MaxRetries = 3
)

# Log the failure
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = ".codespaces/logs/test_failure_{$TestType}_{$timestamp}.log"

$failureLog = @{
    timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    test_type = $TestType
    reason = $FailureReason
    retry_count = 0
} | ConvertTo-Json

Set-Content -Path $logFile -Value $failureLog

# Update checklist item
.\.codespaces\scripts\update_checklist.ps1 -ItemName "$TestType Tests" -Status "failed"

# Attempt retry if within limits
if ($MaxRetries -gt 0) {
    Write-Host "Attempting retry for $TestType tests..." -ForegroundColor Yellow

    # Run health checks first
    php .\.codespaces\scripts\run_health_checks.php
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Health checks failed during retry attempt"
        exit 1
    }

    # Run tests again
    php .\.codespaces\scripts\run_tests.php $TestType
    if ($LASTEXITCODE -eq 0) {
        # Update checklist on success
        .\.codespaces\scripts\update_checklist.ps1 -ItemName "$TestType Tests" -Status "complete"
        Remove-Item $logFile -Force
        Write-Host "Retry successful for $TestType tests" -ForegroundColor Green
        exit 0
    } else {
        # Recursive retry with decremented count
        .\.codespaces\scripts\handle_test_failure.ps1 -TestType $TestType -FailureReason $FailureReason -MaxRetries ($MaxRetries - 1)
    }
} else {
    Write-Error "Maximum retry attempts reached for $TestType tests"
    exit 1
}

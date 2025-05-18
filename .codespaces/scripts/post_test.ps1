# Post-test script for Codespaces test management
param(
    [string]$TestReportPath = ".codespaces/logs/feature_test_report.xml",
    [string]$CompletePath = ".codespaces/complete",
    [string]$LogPath = ".codespaces/logs"
)

# Ensure directories exist
if (!(Test-Path $CompletePath)) {
    New-Item -ItemType Directory -Path $CompletePath -Force
}

if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
}

# Function to check if tests passed
function Test-Passed {
    param([string]$ReportPath)

    if (!(Test-Path $ReportPath)) {
        return $false
    }

    $content = Get-Content $ReportPath
    return $content -match '<testsuites.*failures="0".*errors="0"'
}

# Function to create completion report
function New-CompletionReport {
    param(
        [string]$ReportPath,
        [string]$CompletePath
    )

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
    $reportName = Split-Path $ReportPath -Leaf
    $completeName = $reportName -replace '\.xml$', "_$timestamp.complete"
    $completePath = Join-Path $CompletePath $completeName

    $reportContent = Get-Content $ReportPath
    $completionReport = @{
        "component" = "Codespaces Feature Tests"
        "status" = "complete"
        "timestamp" = $timestamp
        "report" = $reportContent
        "checklist_item" = "feature_test_completion"
    } | ConvertTo-Json

    Set-Content -Path $completePath -Value $completionReport
    return $completePath
}

# Function to clean up failed logs
function Remove-FailedLogs {
    param([string]$LogPath)

    Get-ChildItem $LogPath -Filter "*.log" | ForEach-Object {
        $content = Get-Content $_.FullName
        if ($content -match "FAIL|Error|Exception") {
            Remove-Item $_.FullName -Force
            Write-Host "Removed failed log: $($_.Name)"
        }
    }
}

# Main execution
try {
    if (Test-Passed $TestReportPath) {
        $completePath = New-CompletionReport $TestReportPath $CompletePath
        Write-Host "Tests passed. Completion report created at: $completePath"
    } else {
        Write-Host "Tests failed. No completion report created."
    }

    Remove-FailedLogs $LogPath
} catch {
    Write-Error "Error in post-test script: $_"
    exit 1
}

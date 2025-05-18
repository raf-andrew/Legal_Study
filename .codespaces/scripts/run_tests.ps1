# Production Test Runner for Codespaces
# Tests against live environment without virtualization or WSL

# Configuration
$REPORT_DIR = ".codespaces/complete/testing"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG_FILE = "$REPORT_DIR/test_run_$TIMESTAMP.log"

# Create report directory
New-Item -ItemType Directory -Force -Path $REPORT_DIR | Out-Null

# Logging function
function Write-Log {
    param($Message)
    $logMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

# Test execution function
function Run-Test {
    param(
        [string]$TestName,
        [string]$TestScript,
        [string]$ReportFile
    )

    Write-Log "Starting test: $TestName"

    try {
        # Run the test and capture output
        $result = & $TestScript
        $result | ConvertTo-Json -Depth 10 | Set-Content $ReportFile

        if ($result.status -eq "passed") {
            Write-Log "Test passed: $TestName"
            return $true
        } else {
            Write-Log "Test failed: $TestName - $($result.error)"
            return $false
        }
    }
    catch {
        Write-Log "Test error: $TestName - $_"
        return $false
    }
}

# Verify Codespaces environment
Write-Log "Verifying Codespaces environment"
$codespaceInfo = gh codespace view --json name,state,gitStatus
if (-not $codespaceInfo) {
    Write-Log "Error: Not in a Codespaces environment"
    exit 1
}

# Run tests in sequence
$tests = @(
    @{
        Name = "Environment Setup"
        Script = ".codespaces/scripts/tests/env_setup.ps1"
        Report = "$REPORT_DIR/env_setup.json"
    },
    @{
        Name = "Frontend Service"
        Script = ".codespaces/scripts/tests/frontend.ps1"
        Report = "$REPORT_DIR/frontend.json"
    },
    @{
        Name = "Backend Service"
        Script = ".codespaces/scripts/tests/backend.ps1"
        Report = "$REPORT_DIR/backend.json"
    },
    @{
        Name = "Database Operations"
        Script = ".codespaces/scripts/tests/database.ps1"
        Report = "$REPORT_DIR/database.json"
    },
    @{
        Name = "Security Verification"
        Script = ".codespaces/scripts/tests/security.ps1"
        Report = "$REPORT_DIR/security.json"
    },
    @{
        Name = "Monitoring System"
        Script = ".codespaces/scripts/tests/monitoring.ps1"
        Report = "$REPORT_DIR/monitoring.json"
    },
    @{
        Name = "Integration Testing"
        Script = ".codespaces/scripts/tests/integration.ps1"
        Report = "$REPORT_DIR/integration.json"
    },
    @{
        Name = "Performance Testing"
        Script = ".codespaces/scripts/tests/performance.ps1"
        Report = "$REPORT_DIR/performance.json"
    },
    @{
        Name = "Deployment Verification"
        Script = ".codespaces/scripts/tests/deployment.ps1"
        Report = "$REPORT_DIR/deployment.json"
    }
)

# Track test results
$testResults = @{}
$allTestsPassed = $true

# Run each test
foreach ($test in $tests) {
    if (Test-Path $test.Script) {
        $testResults[$test.Name] = Run-Test -TestName $test.Name -TestScript $test.Script -ReportFile $test.Report
        if (-not $testResults[$test.Name]) {
            $allTestsPassed = $false
        }
    } else {
        Write-Log "Warning: Test script not found: $($test.Script)"
        $testResults[$test.Name] = $false
        $allTestsPassed = $false
    }
}

# Generate final report
$finalReport = @{
    timestamp = $TIMESTAMP
    environment = $codespaceInfo
    test_results = $testResults
    overall_status = if ($allTestsPassed) { "passed" } else { "failed" }
}

$finalReport | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/final_report_$TIMESTAMP.json"

# Update checklist
$checklistPath = ".codespaces/testing/production_testing.md"
if (Test-Path $checklistPath) {
    $content = Get-Content $checklistPath
    foreach ($test in $tests) {
        if ($testResults[$test.Name]) {
            $content = $content -replace "- \[ \] $($test.Name)", "- [x] $($test.Name)"
        }
    }
    $content | Set-Content $checklistPath

    # Move completed checklist to complete directory
    if ($allTestsPassed) {
        Copy-Item $checklistPath ".codespaces/complete/testing/production_testing.md"
    }
}

Write-Log "Test run completed. Final report generated at $REPORT_DIR/final_report_$TIMESTAMP.json"
exit $(if ($allTestsPassed) { 0 } else { 1 })

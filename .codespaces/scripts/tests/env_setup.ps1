# Environment Setup Test Script
# Tests the Codespaces environment initialization and configuration

# Configuration
$REPORT_FILE = ".codespaces/complete/testing/env_setup.json"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Environment Setup"
    status = "running"
    results = @{}
}

# Test Environment Variables
$envVars = @{
    status = "running"
    checks = @{}
}

try {
    # Check required environment variables
    $requiredVars = @(
        "CODESPACE_NAME",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "API_KEY"
    )

    foreach ($var in $requiredVars) {
        if ([System.Environment]::GetEnvironmentVariable($var)) {
            $envVars.checks[$var] = "present"
        } else {
            $envVars.checks[$var] = "missing"
            throw "Required environment variable $var is missing"
        }
    }

    $envVars.status = "passed"
}
catch {
    $envVars.status = "failed"
    $envVars.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Environment variables check failed: $($_.Exception.Message)"
    $report.results["environment_variables"] = $envVars
    $report | ConvertTo-Json -Depth 10 | Set-Content $REPORT_FILE
    exit 1
}

$report.results["environment_variables"] = $envVars

# Test Network Connectivity
$network = @{
    status = "running"
    checks = @{}
}

try {
    # Test required endpoints
    $endpoints = @(
        "http://localhost:3000/api/health",
        "http://localhost:3000/api/status",
        "http://localhost:3000/api/version"
    )

    foreach ($endpoint in $endpoints) {
        $response = Invoke-WebRequest -Uri $endpoint -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $network.checks[$endpoint] = "reachable"
        } else {
            $network.checks[$endpoint] = "unreachable"
            throw "Endpoint $endpoint is not reachable"
        }
    }

    $network.status = "passed"
}
catch {
    $network.status = "failed"
    $network.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Network connectivity check failed: $($_.Exception.Message)"
    $report.results["network"] = $network
    $report | ConvertTo-Json -Depth 10 | Set-Content $REPORT_FILE
    exit 1
}

$report.results["network"] = $network

# Test File System Access
$fileSystem = @{
    status = "running"
    checks = @{}
}

try {
    # Check required directories
    $requiredDirs = @(
        ".codespaces",
        ".codespaces/scripts",
        ".codespaces/testing",
        ".codespaces/logs"
    )

    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            $fileSystem.checks[$dir] = "accessible"
        } else {
            $fileSystem.checks[$dir] = "inaccessible"
            throw "Directory $dir is not accessible"
        }
    }

    $fileSystem.status = "passed"
}
catch {
    $fileSystem.status = "failed"
    $fileSystem.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "File system access check failed: $($_.Exception.Message)"
    $report.results["file_system"] = $fileSystem
    $report | ConvertTo-Json -Depth 10 | Set-Content $REPORT_FILE
    exit 1
}

$report.results["file_system"] = $fileSystem

# Complete report
$report.status = "passed"
$report.message = "Environment setup verification completed successfully"
$report | ConvertTo-Json -Depth 10 | Set-Content $REPORT_FILE

# Update checklist
$checklistPath = ".codespaces/testing/production_testing.md"
if (Test-Path $checklistPath) {
    $content = Get-Content $checklistPath
    $content = $content -replace "- \[ \] Codespaces environment initialization", "- [x] Codespaces environment initialization"
    $content | Set-Content $checklistPath

    # Copy to complete directory
    Copy-Item $checklistPath ".codespaces/complete/testing/production_testing.md"
}

exit 0

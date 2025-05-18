# Deployment Verification Test Script
# Tests deployment configuration and status in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Deployment Verification"
    status = "running"
    results = @{}
}

# Test Environment Configuration
$environment = @{
    status = "running"
    checks = @{}
}

try {
    # Check environment variables
    $requiredVars = @(
        "CODESPACE_NAME",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "API_KEY",
        "JWT_SECRET"
    )

    foreach ($var in $requiredVars) {
        if ($env:$var) {
            $environment.checks[$var] = "present"
        } else {
            $environment.checks[$var] = "missing"
            throw "Required environment variable $var is missing"
        }
    }

    # Check file structure
    $requiredDirs = @(
        ".codespaces",
        ".codespaces/scripts",
        ".codespaces/testing",
        ".codespaces/logs"
    )

    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            $environment.checks[$dir] = "present"
        } else {
            $environment.checks[$dir] = "missing"
            throw "Required directory $dir is missing"
        }
    }

    # Check file permissions
    foreach ($dir in $requiredDirs) {
        $acl = Get-Acl $dir
        $environment.checks["$dir`_permissions"] = $acl.Access | ForEach-Object {
            @{
                identity = $_.IdentityReference.Value
                rights = $_.FileSystemRights
                type = $_.AccessControlType
            }
        }
    }

    $environment.status = "passed"
}
catch {
    $environment.status = "failed"
    $environment.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Environment configuration check failed: $($_.Exception.Message)"
    $report.results["environment"] = $environment
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["environment"] = $environment

# Test Service Status
$services = @{
    status = "running"
    checks = @{}
}

try {
    # Check API service
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $services.checks["api"] = "running"
    } else {
        throw "API service is not running"
    }

    # Check database service
    Import-Module SqlServer
    $connectionString = $env:DATABASE_URL
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query "SELECT @@VERSION as version"
    if ($result) {
        $services.checks["database"] = "running"
    } else {
        throw "Database service is not running"
    }

    # Check cache service
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $services.checks["cache"] = "running"
    } else {
        throw "Cache service is not running"
    }

    $services.status = "passed"
}
catch {
    $services.status = "failed"
    $services.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Service status check failed: $($_.Exception.Message)"
    $report.results["services"] = $services
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["services"] = $services

# Test Deployment Configuration
$config = @{
    status = "running"
    checks = @{}
}

try {
    # Check API configuration
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/config" -UseBasicParsing
    $apiConfig = $response.Content | ConvertFrom-Json

    $requiredConfig = @(
        "version",
        "environment",
        "database",
        "cache",
        "security"
    )

    foreach ($item in $requiredConfig) {
        if ($apiConfig.$item) {
            $config.checks["api_$item"] = "present"
        } else {
            throw "Missing API configuration: $item"
        }
    }

    # Check database configuration
    $dbConfig = @{
        connection_string = $env:DATABASE_URL
        max_connections = 100
        timeout = 30
    }

    foreach ($item in $dbConfig.GetEnumerator()) {
        if ($item.Value) {
            $config.checks["database_$($item.Key)"] = "present"
        } else {
            throw "Missing database configuration: $($item.Key)"
        }
    }

    # Check security configuration
    $securityConfig = @{
        jwt_secret = $env:JWT_SECRET
        api_key = $env:API_KEY
        token_expiry = 3600
    }

    foreach ($item in $securityConfig.GetEnumerator()) {
        if ($item.Value) {
            $config.checks["security_$($item.Key)"] = "present"
        } else {
            throw "Missing security configuration: $($item.Key)"
        }
    }

    $config.status = "passed"
}
catch {
    $config.status = "failed"
    $config.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Deployment configuration check failed: $($_.Exception.Message)"
    $report.results["config"] = $config
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["config"] = $config

# Test Deployment Health
$health = @{
    status = "running"
    checks = @{}
}

try {
    # Check API health
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
    $healthData = $response.Content | ConvertFrom-Json

    $requiredHealth = @(
        "status",
        "version",
        "uptime",
        "database",
        "cache"
    )

    foreach ($item in $requiredHealth) {
        if ($healthData.$item) {
            $health.checks["api_$item"] = "healthy"
        } else {
            throw "API health check failed: $item"
        }
    }

    # Check database health
    $dbHealth = Invoke-Sqlcmd -ConnectionString $connectionString -Query @"
    SELECT
        @@VERSION as version,
        SERVERPROPERTY('IsClustered') as is_clustered,
        SERVERPROPERTY('IsHadrEnabled') as is_hadr_enabled
"@

    if ($dbHealth) {
        $health.checks["database"] = "healthy"
    } else {
        throw "Database health check failed"
    }

    # Check cache health
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/health" -UseBasicParsing
    $cacheHealth = $response.Content | ConvertFrom-Json

    if ($cacheHealth.status -eq "healthy") {
        $health.checks["cache"] = "healthy"
    } else {
        throw "Cache health check failed"
    }

    $health.status = "passed"
}
catch {
    $health.status = "failed"
    $health.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Deployment health check failed: $($_.Exception.Message)"
    $report.results["health"] = $health
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["health"] = $health

# Test Deployment Logs
$logs = @{
    status = "running"
    checks = @{}
}

try {
    # Check application logs
    $logDir = ".codespaces/logs"
    $logFiles = Get-ChildItem -Path $logDir -Filter "*.log"

    foreach ($file in $logFiles) {
        $logContent = Get-Content $file.FullName -Tail 100
        $errorCount = ($logContent | Select-String -Pattern "ERROR").Count
        $warningCount = ($logContent | Select-String -Pattern "WARNING").Count

        $logs.checks[$file.Name] = @{
            error_count = $errorCount
            warning_count = $warningCount
            last_modified = $file.LastWriteTime
        }

        if ($errorCount -gt 0) {
            throw "Found errors in $($file.Name)"
        }
    }

    # Check system logs
    $systemLogs = Get-EventLog -LogName System -Newest 100
    $errorCount = ($systemLogs | Where-Object { $_.EntryType -eq "Error" }).Count
    $warningCount = ($systemLogs | Where-Object { $_.EntryType -eq "Warning" }).Count

    $logs.checks["system"] = @{
        error_count = $errorCount
        warning_count = $warningCount
        last_checked = Get-Date
    }

    if ($errorCount -gt 0) {
        throw "Found system errors"
    }

    $logs.status = "passed"
}
catch {
    $logs.status = "failed"
    $logs.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Deployment logs check failed: $($_.Exception.Message)"
    $report.results["logs"] = $logs
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["logs"] = $logs

# Complete report
$report.status = "passed"
$report.message = "Deployment verification completed successfully"
$report | ConvertTo-Json -Depth 10

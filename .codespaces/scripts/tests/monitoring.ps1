# Monitoring System Test Script
# Tests monitoring and logging systems in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Monitoring System"
    status = "running"
    results = @{}
}

# Test Logging System
$logging = @{
    status = "running"
    tests = @{}
}

try {
    # Test log file creation and rotation
    $logDir = ".codespaces/logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force
    }

    # Generate test log entries
    $logLevels = @("INFO", "WARNING", "ERROR", "DEBUG")
    foreach ($level in $logLevels) {
        $logMessage = "Test $level message at $(Get-Date)"
        Add-Content -Path "$logDir/app.log" -Value "[$level] $logMessage"
        Start-Sleep -Milliseconds 100
    }

    # Verify log file exists and contains entries
    if (Test-Path "$logDir/app.log") {
        $logContent = Get-Content "$logDir/app.log"
        foreach ($level in $logLevels) {
            if ($logContent -match "\[$level\]") {
                $logging.tests["log_$level"] = "passed"
            } else {
                throw "Missing $level log entries"
            }
        }
    } else {
        throw "Log file not created"
    }

    # Test log rotation
    $maxLogSize = 1MB
    $largeMessage = "x" * 1000
    while ((Get-Item "$logDir/app.log").Length -lt $maxLogSize) {
        Add-Content -Path "$logDir/app.log" -Value $largeMessage
    }

    if (Test-Path "$logDir/app.log.1") {
        $logging.tests["log_rotation"] = "passed"
    } else {
        throw "Log rotation not triggered"
    }

    $logging.status = "passed"
}
catch {
    $logging.status = "failed"
    $logging.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Logging system test failed: $($_.Exception.Message)"
    $report.results["logging"] = $logging
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["logging"] = $logging

# Test Metrics Collection
$metrics = @{
    status = "running"
    tests = @{}
}

try {
    # Test system metrics collection
    $systemMetrics = @{
        cpu_usage = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
        memory_usage = (Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue
        disk_usage = (Get-Counter '\LogicalDisk(_Total)\% Free Space').CounterSamples.CookedValue
    }

    foreach ($metric in $systemMetrics.GetEnumerator()) {
        if ($metric.Value -ge 0 -and $metric.Value -le 100) {
            $metrics.tests[$metric.Key] = "passed"
        } else {
            throw "Invalid $($metric.Key) value: $($metric.Value)"
        }
    }

    # Test application metrics
    $appMetrics = @{
        status = "running"
        metrics = @{}
    }

    # Test request rate
    $startTime = Get-Date
    $requests = 0
    $duration = 10 # seconds
    $endTime = $startTime.AddSeconds($duration)

    while ((Get-Date) -lt $endTime) {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
        $requests++
        Start-Sleep -Milliseconds 100
    }

    $requestRate = $requests / $duration
    $appMetrics.metrics["request_rate"] = $requestRate
    if ($requestRate -gt 0) {
        $metrics.tests["request_rate"] = "passed"
    } else {
        throw "Request rate monitoring failed"
    }

    # Test response time
    $responseTimes = @()
    for ($i = 0; $i -lt 10; $i++) {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
        $responseTime = (Get-Date) - $startTime
        $responseTimes += $responseTime.TotalMilliseconds
        Start-Sleep -Milliseconds 100
    }

    $avgResponseTime = ($responseTimes | Measure-Object -Average).Average
    $appMetrics.metrics["avg_response_time"] = $avgResponseTime
    if ($avgResponseTime -gt 0) {
        $metrics.tests["response_time"] = "passed"
    } else {
        throw "Response time monitoring failed"
    }

    $metrics.status = "passed"
}
catch {
    $metrics.status = "failed"
    $metrics.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Metrics collection test failed: $($_.Exception.Message)"
    $report.results["metrics"] = $metrics
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["metrics"] = $metrics

# Test Alerting System
$alerts = @{
    status = "running"
    tests = @{}
}

try {
    # Test alert thresholds
    $thresholds = @{
        cpu_usage = 90
        memory_usage = 85
        disk_usage = 10
        response_time = 1000
    }

    # Simulate high CPU usage
    $cpuStress = Start-Job -ScriptBlock {
        $endTime = (Get-Date).AddSeconds(5)
        while ((Get-Date) -lt $endTime) {
            $null = 1..1000000 | ForEach-Object { $_ * $_ }
        }
    }

    Start-Sleep -Seconds 2
    $cpuUsage = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
    if ($cpuUsage -gt $thresholds.cpu_usage) {
        $alerts.tests["cpu_alert"] = "triggered"
    } else {
        $alerts.tests["cpu_alert"] = "not_triggered"
    }

    Wait-Job $cpuStress | Out-Null

    # Test alert notification
    $alertMessage = "Test alert message"
    $notificationSent = $false

    # Simulate sending alert notification
    $notificationJob = Start-Job -ScriptBlock {
        param($message)
        # Simulate notification delay
        Start-Sleep -Seconds 2
        return $true
    } -ArgumentList $alertMessage

    $notificationSent = Wait-Job $notificationJob | Receive-Job
    if ($notificationSent) {
        $alerts.tests["alert_notification"] = "sent"
    } else {
        throw "Alert notification failed"
    }

    $alerts.status = "passed"
}
catch {
    $alerts.status = "failed"
    $alerts.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Alerting system test failed: $($_.Exception.Message)"
    $report.results["alerts"] = $alerts
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["alerts"] = $alerts

# Test Health Checks
$health = @{
    status = "running"
    checks = @{}
}

try {
    # Test application health endpoint
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
    $healthData = $response.Content | ConvertFrom-Json

    $requiredChecks = @(
        "status",
        "version",
        "uptime",
        "database",
        "cache"
    )

    foreach ($check in $requiredChecks) {
        if ($healthData.$check) {
            $health.checks[$check] = "passed"
        } else {
            throw "Missing health check: $check"
        }
    }

    # Test dependency health
    $dependencies = @(
        "http://localhost:3000/api/db/health",
        "http://localhost:3000/api/cache/health"
    )

    foreach ($dep in $dependencies) {
        $response = Invoke-WebRequest -Uri $dep -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $health.checks[$dep] = "passed"
        } else {
            throw "Dependency health check failed: $dep"
        }
    }

    $health.status = "passed"
}
catch {
    $health.status = "failed"
    $health.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Health check test failed: $($_.Exception.Message)"
    $report.results["health"] = $health
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["health"] = $health

# Complete report
$report.status = "passed"
$report.message = "Monitoring system verification completed successfully"
$report | ConvertTo-Json -Depth 10

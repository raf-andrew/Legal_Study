# Performance Test Script
# Tests system performance in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Performance Testing"
    status = "running"
    results = @{}
}

# Test API Performance
$api = @{
    status = "running"
    metrics = @{}
}

try {
    # Test single request performance
    $endpoints = @(
        @{
            path = "/api/health"
            method = "GET"
            expected_time = 100
        },
        @{
            path = "/api/users"
            method = "GET"
            expected_time = 200
        },
        @{
            path = "/api/projects"
            method = "GET"
            expected_time = 200
        }
    )

    foreach ($endpoint in $endpoints) {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri "http://localhost:3000$($endpoint.path)" -Method $endpoint.method -UseBasicParsing
        $responseTime = (Get-Date) - $startTime

        $api.metrics[$endpoint.path] = @{
            response_time = $responseTime.TotalMilliseconds
            status_code = $response.StatusCode
            passed = $responseTime.TotalMilliseconds -le $endpoint.expected_time
        }

        if (-not $api.metrics[$endpoint.path].passed) {
            throw "Response time for $($endpoint.path) exceeds threshold"
        }
    }

    # Test concurrent requests
    $concurrentUsers = 10
    $requestsPerUser = 5
    $totalRequests = $concurrentUsers * $requestsPerUser
    $startTime = Get-Date
    $jobs = @()

    for ($i = 0; $i -lt $concurrentUsers; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($baseUrl, $requests)
            $results = @()
            for ($j = 0; $j -lt $requests; $j++) {
                $startTime = Get-Date
                $response = Invoke-WebRequest -Uri "$baseUrl/api/health" -UseBasicParsing
                $responseTime = (Get-Date) - $startTime
                $results += @{
                    response_time = $responseTime.TotalMilliseconds
                    status_code = $response.StatusCode
                }
                Start-Sleep -Milliseconds 100
            }
            return $results
        } -ArgumentList "http://localhost:3000", $requestsPerUser
    }

    $results = $jobs | Wait-Job | Receive-Job
    $totalTime = (Get-Date) - $startTime

    $api.metrics["concurrent_requests"] = @{
        total_requests = $totalRequests
        total_time = $totalTime.TotalMilliseconds
        requests_per_second = $totalRequests / $totalTime.TotalSeconds
        average_response_time = ($results | ForEach-Object { $_.response_time } | Measure-Object -Average).Average
        max_response_time = ($results | ForEach-Object { $_.response_time } | Measure-Object -Maximum).Maximum
        min_response_time = ($results | ForEach-Object { $_.response_time } | Measure-Object -Minimum).Minimum
    }

    if ($api.metrics["concurrent_requests"].average_response_time -gt 500) {
        throw "Average response time exceeds threshold"
    }

    $api.status = "passed"
}
catch {
    $api.status = "failed"
    $api.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "API performance test failed: $($_.Exception.Message)"
    $report.results["api"] = $api
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["api"] = $api

# Test Database Performance
$database = @{
    status = "running"
    metrics = @{}
}

try {
    # Test database connection performance
    Import-Module SqlServer
    $connectionString = $env:DATABASE_URL

    # Test query performance
    $queries = @(
        @{
            name = "simple_select"
            query = "SELECT TOP 1000 * FROM users"
            expected_time = 1000
        },
        @{
            name = "join_query"
            query = @"
                SELECT TOP 1000 u.*, p.name as project_name
                FROM users u
                LEFT JOIN projects p ON u.id = p.user_id
"@
            expected_time = 2000
        },
        @{
            name = "aggregate_query"
            query = @"
                SELECT
                    u.username,
                    COUNT(p.id) as project_count,
                    COUNT(t.id) as task_count
                FROM users u
                LEFT JOIN projects p ON u.id = p.user_id
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY u.username
"@
            expected_time = 3000
        }
    )

    foreach ($query in $queries) {
        $startTime = Get-Date
        $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $query.query
        $queryTime = (Get-Date) - $startTime

        $database.metrics[$query.name] = @{
            execution_time = $queryTime.TotalMilliseconds
            row_count = $result.Count
            passed = $queryTime.TotalMilliseconds -le $query.expected_time
        }

        if (-not $database.metrics[$query.name].passed) {
            throw "Query execution time for $($query.name) exceeds threshold"
        }
    }

    # Test concurrent database operations
    $concurrentOperations = 5
    $operationsPerThread = 10
    $startTime = Get-Date
    $jobs = @()

    for ($i = 0; $i -lt $concurrentOperations; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($connString, $operations)
            Import-Module SqlServer
            $results = @()
            for ($j = 0; $j -lt $operations; $j++) {
                $startTime = Get-Date
                $result = Invoke-Sqlcmd -ConnectionString $connString -Query "SELECT TOP 100 * FROM users"
                $queryTime = (Get-Date) - $startTime
                $results += @{
                    execution_time = $queryTime.TotalMilliseconds
                    row_count = $result.Count
                }
                Start-Sleep -Milliseconds 100
            }
            return $results
        } -ArgumentList $connectionString, $operationsPerThread
    }

    $results = $jobs | Wait-Job | Receive-Job
    $totalTime = (Get-Date) - $startTime

    $database.metrics["concurrent_operations"] = @{
        total_operations = $concurrentOperations * $operationsPerThread
        total_time = $totalTime.TotalMilliseconds
        operations_per_second = ($concurrentOperations * $operationsPerThread) / $totalTime.TotalSeconds
        average_execution_time = ($results | ForEach-Object { $_.execution_time } | Measure-Object -Average).Average
        max_execution_time = ($results | ForEach-Object { $_.execution_time } | Measure-Object -Maximum).Maximum
        min_execution_time = ($results | ForEach-Object { $_.execution_time } | Measure-Object -Minimum).Minimum
    }

    if ($database.metrics["concurrent_operations"].average_execution_time -gt 1000) {
        throw "Average database operation time exceeds threshold"
    }

    $database.status = "passed"
}
catch {
    $database.status = "failed"
    $database.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Database performance test failed: $($_.Exception.Message)"
    $report.results["database"] = $database
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["database"] = $database

# Test System Resource Usage
$resources = @{
    status = "running"
    metrics = @{}
}

try {
    # Test CPU usage
    $cpuTest = Start-Job -ScriptBlock {
        $endTime = (Get-Date).AddSeconds(10)
        $metrics = @()
        while ((Get-Date) -lt $endTime) {
            $cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
            $metrics += $cpu
            Start-Sleep -Seconds 1
        }
        return $metrics
    }

    $cpuMetrics = Wait-Job $cpuTest | Receive-Job
    $resources.metrics["cpu"] = @{
        average_usage = ($cpuMetrics | Measure-Object -Average).Average
        max_usage = ($cpuMetrics | Measure-Object -Maximum).Maximum
        min_usage = ($cpuMetrics | Measure-Object -Minimum).Minimum
    }

    if ($resources.metrics["cpu"].average_usage -gt 80) {
        throw "Average CPU usage exceeds threshold"
    }

    # Test memory usage
    $memoryTest = Start-Job -ScriptBlock {
        $endTime = (Get-Date).AddSeconds(10)
        $metrics = @()
        while ((Get-Date) -lt $endTime) {
            $memory = (Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue
            $metrics += $memory
            Start-Sleep -Seconds 1
        }
        return $metrics
    }

    $memoryMetrics = Wait-Job $memoryTest | Receive-Job
    $resources.metrics["memory"] = @{
        average_usage = ($memoryMetrics | Measure-Object -Average).Average
        max_usage = ($memoryMetrics | Measure-Object -Maximum).Maximum
        min_usage = ($memoryMetrics | Measure-Object -Minimum).Minimum
    }

    if ($resources.metrics["memory"].average_usage -gt 85) {
        throw "Average memory usage exceeds threshold"
    }

    # Test disk I/O
    $diskTest = Start-Job -ScriptBlock {
        $endTime = (Get-Date).AddSeconds(10)
        $metrics = @()
        while ((Get-Date) -lt $endTime) {
            $disk = (Get-Counter '\LogicalDisk(_Total)\% Disk Time').CounterSamples.CookedValue
            $metrics += $disk
            Start-Sleep -Seconds 1
        }
        return $metrics
    }

    $diskMetrics = Wait-Job $diskTest | Receive-Job
    $resources.metrics["disk"] = @{
        average_usage = ($diskMetrics | Measure-Object -Average).Average
        max_usage = ($diskMetrics | Measure-Object -Maximum).Maximum
        min_usage = ($diskMetrics | Measure-Object -Minimum).Minimum
    }

    if ($resources.metrics["disk"].average_usage -gt 70) {
        throw "Average disk usage exceeds threshold"
    }

    $resources.status = "passed"
}
catch {
    $resources.status = "failed"
    $resources.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "System resource usage test failed: $($_.Exception.Message)"
    $report.results["resources"] = $resources
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["resources"] = $resources

# Complete report
$report.status = "passed"
$report.message = "Performance testing completed successfully"
$report | ConvertTo-Json -Depth 10

# Backend Service Test Script
# Tests the backend service in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Backend Service"
    status = "running"
    results = @{}
}

# Test API Endpoints
$apiEndpoints = @{
    status = "running"
    endpoints = @{}
}

try {
    # Test health endpoint
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $apiEndpoints.endpoints["health"] = "responsive"
    } else {
        $apiEndpoints.endpoints["health"] = "failed"
        throw "Health endpoint failed"
    }

    # Test authentication endpoints
    $authEndpoints = @(
        @{
            path = "/api/auth/login"
            method = "POST"
            body = @{
                username = "testuser"
                password = "testpass"
            }
        },
        @{
            path = "/api/auth/refresh"
            method = "POST"
            body = @{
                refresh_token = "test_refresh_token"
            }
        }
    )

    foreach ($endpoint in $authEndpoints) {
        $response = Invoke-WebRequest -Uri "http://localhost:3000$($endpoint.path)" -Method $endpoint.method -Body ($endpoint.body | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $apiEndpoints.endpoints["auth_$($endpoint.path)"] = "responsive"
        } else {
            $apiEndpoints.endpoints["auth_$($endpoint.path)"] = "failed"
            throw "Auth endpoint $($endpoint.path) failed"
        }
    }

    # Test business logic endpoints
    $businessEndpoints = @(
        "/api/users",
        "/api/projects",
        "/api/tasks"
    )

    foreach ($endpoint in $businessEndpoints) {
        $response = Invoke-WebRequest -Uri "http://localhost:3000$endpoint" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $apiEndpoints.endpoints["business_$endpoint"] = "responsive"
        } else {
            $apiEndpoints.endpoints["business_$endpoint"] = "failed"
            throw "Business endpoint $endpoint failed"
        }
    }

    $apiEndpoints.status = "passed"
}
catch {
    $apiEndpoints.status = "failed"
    $apiEndpoints.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "API endpoint testing failed: $($_.Exception.Message)"
    $report.results["api_endpoints"] = $apiEndpoints
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["api_endpoints"] = $apiEndpoints

# Test Error Handling
$errorHandling = @{
    status = "running"
    scenarios = @{}
}

try {
    # Test invalid authentication
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/login" -Method Post -Body (@{
        username = "invalid"
        password = "invalid"
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 401) {
        $errorHandling.scenarios["invalid_auth"] = "handled"
    } else {
        $errorHandling.scenarios["invalid_auth"] = "failed"
        throw "Invalid authentication not handled correctly"
    }

    # Test invalid input
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/users" -Method Post -Body (@{
        invalid_field = "test"
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 400) {
        $errorHandling.scenarios["invalid_input"] = "handled"
    } else {
        $errorHandling.scenarios["invalid_input"] = "failed"
        throw "Invalid input not handled correctly"
    }

    # Test not found
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/nonexistent" -UseBasicParsing
    if ($response.StatusCode -eq 404) {
        $errorHandling.scenarios["not_found"] = "handled"
    } else {
        $errorHandling.scenarios["not_found"] = "failed"
        throw "Not found not handled correctly"
    }

    $errorHandling.status = "passed"
}
catch {
    $errorHandling.status = "failed"
    $errorHandling.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Error handling testing failed: $($_.Exception.Message)"
    $report.results["error_handling"] = $errorHandling
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["error_handling"] = $errorHandling

# Test Performance
$performance = @{
    status = "running"
    metrics = @{}
}

try {
    # Measure API response times
    $endpoints = @("/api/health", "/api/users", "/api/projects")
    foreach ($endpoint in $endpoints) {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri "http://localhost:3000$endpoint" -UseBasicParsing
        $responseTime = (Get-Date) - $startTime

        $performance.metrics["$endpoint"] = $responseTime.TotalMilliseconds
        if ($responseTime.TotalMilliseconds -gt 500) {
            throw "Response time for $endpoint exceeds threshold"
        }
    }

    # Test concurrent requests
    $startTime = Get-Date
    $jobs = @()
    for ($i = 0; $i -lt 10; $i++) {
        $jobs += Start-Job -ScriptBlock {
            $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
            return $response.StatusCode
        }
    }
    $results = $jobs | Wait-Job | Receive-Job
    $concurrentTime = (Get-Date) - $startTime

    $performance.metrics["concurrent_requests"] = $concurrentTime.TotalMilliseconds
    if ($concurrentTime.TotalMilliseconds -gt 2000) {
        throw "Concurrent request handling too slow"
    }

    $performance.status = "passed"
}
catch {
    $performance.status = "failed"
    $performance.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Performance testing failed: $($_.Exception.Message)"
    $report.results["performance"] = $performance
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["performance"] = $performance

# Complete report
$report.status = "passed"
$report.message = "Backend service testing completed successfully"
$report | ConvertTo-Json -Depth 10

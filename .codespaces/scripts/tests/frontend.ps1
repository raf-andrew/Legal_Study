# Frontend Service Test Script
# Tests the frontend service in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Frontend Service"
    status = "running"
    results = @{}
}

# Test UI Components
$uiComponents = @{
    status = "running"
    components = @{}
}

try {
    # Test main application page
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $uiComponents.components["main_page"] = "loaded"
    } else {
        $uiComponents.components["main_page"] = "failed"
        throw "Main page failed to load"
    }

    # Test API endpoints
    $endpoints = @(
        "/api/health",
        "/api/status",
        "/api/version"
    )

    foreach ($endpoint in $endpoints) {
        $response = Invoke-WebRequest -Uri "http://localhost:3000$endpoint" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $uiComponents.components["endpoint_$endpoint"] = "responsive"
        } else {
            $uiComponents.components["endpoint_$endpoint"] = "failed"
            throw "Endpoint $endpoint failed"
        }
    }

    $uiComponents.status = "passed"
}
catch {
    $uiComponents.status = "failed"
    $uiComponents.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "UI component testing failed: $($_.Exception.Message)"
    $report.results["ui_components"] = $uiComponents
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["ui_components"] = $uiComponents

# Test User Interactions
$userInteractions = @{
    status = "running"
    interactions = @{}
}

try {
    # Test form submissions
    $formData = @{
        username = "testuser"
        password = "testpass"
    }

    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/login" -Method Post -Body $formData -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $userInteractions.interactions["login_form"] = "working"
    } else {
        $userInteractions.interactions["login_form"] = "failed"
        throw "Login form submission failed"
    }

    # Test navigation
    $pages = @("/dashboard", "/profile", "/settings")
    foreach ($page in $pages) {
        $response = Invoke-WebRequest -Uri "http://localhost:3000$page" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $userInteractions.interactions["navigation_$page"] = "working"
        } else {
            $userInteractions.interactions["navigation_$page"] = "failed"
            throw "Navigation to $page failed"
        }
    }

    $userInteractions.status = "passed"
}
catch {
    $userInteractions.status = "failed"
    $userInteractions.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "User interaction testing failed: $($_.Exception.Message)"
    $report.results["user_interactions"] = $userInteractions
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["user_interactions"] = $userInteractions

# Test Performance
$performance = @{
    status = "running"
    metrics = @{}
}

try {
    # Measure page load time
    $startTime = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    $loadTime = (Get-Date) - $startTime

    $performance.metrics["page_load_time"] = $loadTime.TotalMilliseconds
    if ($loadTime.TotalMilliseconds -gt 2000) {
        throw "Page load time exceeds threshold"
    }

    # Measure API response time
    $startTime = Get-Date
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing
    $apiTime = (Get-Date) - $startTime

    $performance.metrics["api_response_time"] = $apiTime.TotalMilliseconds
    if ($apiTime.TotalMilliseconds -gt 500) {
        throw "API response time exceeds threshold"
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
$report.message = "Frontend service testing completed successfully"
$report | ConvertTo-Json -Depth 10

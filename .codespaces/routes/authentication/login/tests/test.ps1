# Login Route Test Script
# Tests the login endpoint functionality in live environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$REPORT_DIR = "reports"
$BASE_URL = "http://localhost:3000"

# Ensure report directory exists
if (-not (Test-Path $REPORT_DIR)) {
    New-Item -ItemType Directory -Path $REPORT_DIR | Out-Null
}

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Login Route Test"
    status = "running"
    results = @{}
}

# Test Basic Login
$basicLogin = @{
    status = "running"
    checks = @{}
}

try {
    # Test valid credentials
    $validCredentials = @{
        username = "testuser"
        password = "TestPass123!"
    }

    $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" `
        -Method Post `
        -Body ($validCredentials | ConvertTo-Json) `
        -ContentType "application/json" `
        -UseBasicParsing

    if ($response.StatusCode -eq 200) {
        $responseData = $response.Content | ConvertFrom-Json
        $basicLogin.checks["valid_credentials"] = @{
            status = "passed"
            token_received = [bool]$responseData.token
            refresh_token_received = [bool]$responseData.refresh_token
            user_info_received = [bool]$responseData.user
        }
    } else {
        throw "Valid credentials test failed with status $($response.StatusCode)"
    }

    # Test invalid credentials
    $invalidCredentials = @{
        username = "testuser"
        password = "WrongPass123!"
    }

    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" `
            -Method Post `
            -Body ($invalidCredentials | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401) {
            $basicLogin.checks["invalid_credentials"] = @{
                status = "passed"
                error_code = 401
                error_message = "Unauthorized"
            }
        } else {
            throw "Invalid credentials test failed with unexpected status"
        }
    }

    $basicLogin.status = "passed"
}
catch {
    $basicLogin.status = "failed"
    $basicLogin.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Basic login test failed: $($_.Exception.Message)"
    $report.results["basic_login"] = $basicLogin
    $report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/basic_login.json"
    exit 1
}

$report.results["basic_login"] = $basicLogin

# Test Rate Limiting
$rateLimit = @{
    status = "running"
    checks = @{}
}

try {
    # Test multiple failed attempts
    $failedAttempts = 0
    $rateLimited = $false

    for ($i = 0; $i -lt 5; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" `
                -Method Post `
                -Body (@{
                    username = "testuser"
                    password = "WrongPass123!"
                } | ConvertTo-Json) `
                -ContentType "application/json" `
                -UseBasicParsing
        } catch {
            if ($_.Exception.Response.StatusCode -eq 429) {
                $rateLimited = $true
                break
            }
            $failedAttempts++
        }
    }

    $rateLimit.checks["multiple_failed_attempts"] = @{
        status = if ($rateLimited) { "passed" } else { "failed" }
        failed_attempts = $failedAttempts
        rate_limited = $rateLimited
    }

    # Test success after rate limit
    if ($rateLimited) {
        Start-Sleep -Seconds 60  # Wait for rate limit to reset
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" `
            -Method Post `
            -Body ($validCredentials | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing

        if ($response.StatusCode -eq 200) {
            $rateLimit.checks["success_after_rate_limit"] = @{
                status = "passed"
                message = "Successfully logged in after rate limit reset"
            }
        } else {
            throw "Failed to login after rate limit reset"
        }
    }

    $rateLimit.status = "passed"
}
catch {
    $rateLimit.status = "failed"
    $rateLimit.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Rate limiting test failed: $($_.Exception.Message)"
    $report.results["rate_limiting"] = $rateLimit
    $report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/rate_limiting.json"
    exit 1
}

$report.results["rate_limiting"] = $rateLimit

# Test Session Management
$sessionManagement = @{
    status = "running"
    checks = @{}
}

try {
    # Test multiple active sessions
    $sessions = @()
    for ($i = 0; $i -lt 3; $i++) {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/auth/login" `
            -Method Post `
            -Body ($validCredentials | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing

        if ($response.StatusCode -eq 200) {
            $sessions += ($response.Content | ConvertFrom-Json).token
        }
    }

    $sessionManagement.checks["multiple_sessions"] = @{
        status = if ($sessions.Count -eq 3) { "passed" } else { "failed" }
        session_count = $sessions.Count
        sessions = $sessions
    }

    # Test session expiration
    $token = $sessions[0]
    Start-Sleep -Seconds 3600  # Wait for token to expire
    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/protected" `
            -Method Get `
            -Headers @{
                "Authorization" = "Bearer $token"
            } `
            -UseBasicParsing
    } catch {
        if ($_.Exception.Response.StatusCode -eq 401) {
            $sessionManagement.checks["session_expiration"] = @{
                status = "passed"
                message = "Session expired as expected"
            }
        } else {
            throw "Session expiration test failed with unexpected status"
        }
    }

    $sessionManagement.status = "passed"
}
catch {
    $sessionManagement.status = "failed"
    $sessionManagement.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Session management test failed: $($_.Exception.Message)"
    $report.results["session_management"] = $sessionManagement
    $report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/session_management.json"
    exit 1
}

$report.results["session_management"] = $sessionManagement

# Complete report
$report.status = "passed"
$report.message = "Login route testing completed successfully"
$report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/login_test.json"

# Update master routes list
$masterRoutes = Get-Content ".codespaces/routes/master_routes.json" | ConvertFrom-Json
$masterRoutes.routes.authentication.login.test_status = "completed"
$masterRoutes.routes.authentication.login.test_report = "$REPORT_DIR/login_test.json"
$masterRoutes | ConvertTo-Json -Depth 10 | Set-Content ".codespaces/routes/master_routes.json"

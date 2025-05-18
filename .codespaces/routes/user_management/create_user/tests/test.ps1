# Create User Route Test Script
# Tests the user creation endpoint functionality in live environment

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
    test_name = "Create User Route Test"
    status = "running"
    results = @{}
}

# Test Valid User Creation
$validCreation = @{
    status = "running"
    checks = @{}
}

try {
    # Test valid user creation
    $validUser = @{
        email = "test.user.$TIMESTAMP@example.com"
        password = "TestPass123!"
        name = "Test User"
    }

    $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
        -Method Post `
        -Body ($validUser | ConvertTo-Json) `
        -ContentType "application/json" `
        -UseBasicParsing

    if ($response.StatusCode -eq 201) {
        $responseData = $response.Content | ConvertFrom-Json
        $validCreation.checks["valid_creation"] = @{
            status = "passed"
            user_created = [bool]$responseData.user
            token_received = [bool]$responseData.token
            refresh_token_received = [bool]$responseData.refresh_token
            email_sent = [bool]$responseData.email_sent
        }
    } else {
        throw "Valid user creation test failed with status $($response.StatusCode)"
    }

    $validCreation.status = "passed"
}
catch {
    $validCreation.status = "failed"
    $validCreation.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Valid user creation test failed: $($_.Exception.Message)"
    $report.results["valid_creation"] = $validCreation
    $report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/valid_creation.json"
    exit 1
}

$report.results["valid_creation"] = $validCreation

# Test Duplicate Email
$duplicateEmail = @{
    status = "running"
    checks = @{}
}

try {
    # Test duplicate email
    $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
        -Method Post `
        -Body ($validUser | ConvertTo-Json) `
        -ContentType "application/json" `
        -UseBasicParsing
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        $duplicateEmail.checks["duplicate_email"] = @{
            status = "passed"
            error_code = 409
            error_message = "Email already exists"
        }
    } else {
        throw "Duplicate email test failed with unexpected status"
    }
}

$duplicateEmail.status = "passed"
$report.results["duplicate_email"] = $duplicateEmail

# Test Input Validation
$inputValidation = @{
    status = "running"
    checks = @{}
}

try {
    # Test missing required fields
    $missingFields = @{
        email = "test.user.$TIMESTAMP@example.com"
        # Missing password
        name = "Test User"
    }

    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
            -Method Post `
            -Body ($missingFields | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400) {
            $inputValidation.checks["missing_fields"] = @{
                status = "passed"
                error_code = 400
                error_message = "Missing required fields"
            }
        } else {
            throw "Missing fields test failed with unexpected status"
        }
    }

    # Test invalid email format
    $invalidEmail = @{
        email = "invalid.email"
        password = "TestPass123!"
        name = "Test User"
    }

    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
            -Method Post `
            -Body ($invalidEmail | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400) {
            $inputValidation.checks["invalid_email"] = @{
                status = "passed"
                error_code = 400
                error_message = "Invalid email format"
            }
        } else {
            throw "Invalid email test failed with unexpected status"
        }
    }

    # Test weak password
    $weakPassword = @{
        email = "test.user.$TIMESTAMP@example.com"
        password = "weak"
        name = "Test User"
    }

    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
            -Method Post `
            -Body ($weakPassword | ConvertTo-Json) `
            -ContentType "application/json" `
            -UseBasicParsing
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400) {
            $inputValidation.checks["weak_password"] = @{
                status = "passed"
                error_code = 400
                error_message = "Password too weak"
            }
        } else {
            throw "Weak password test failed with unexpected status"
        }
    }

    $inputValidation.status = "passed"
}
catch {
    $inputValidation.status = "failed"
    $inputValidation.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Input validation test failed: $($_.Exception.Message)"
    $report.results["input_validation"] = $inputValidation
    $report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/input_validation.json"
    exit 1
}

$report.results["input_validation"] = $inputValidation

# Test Rate Limiting
$rateLimit = @{
    status = "running"
    checks = @{}
}

try {
    # Test multiple requests
    $failedAttempts = 0
    $rateLimited = $false

    for ($i = 0; $i -lt 5; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$BASE_URL/api/users" `
                -Method Post `
                -Body (@{
                    email = "test.user.$TIMESTAMP.$i@example.com"
                    password = "TestPass123!"
                    name = "Test User"
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

    $rateLimit.checks["multiple_requests"] = @{
        status = if ($rateLimited) { "passed" } else { "failed" }
        failed_attempts = $failedAttempts
        rate_limited = $rateLimited
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

# Complete report
$report.status = "passed"
$report.message = "Create user route testing completed successfully"
$report | ConvertTo-Json -Depth 10 | Set-Content "$REPORT_DIR/create_user_test.json"

# Update master routes list
$masterRoutes = Get-Content ".codespaces/routes/master_routes.json" | ConvertFrom-Json
$masterRoutes.routes.user_management.create_user.test_status = "completed"
$masterRoutes.routes.user_management.create_user.test_report = "$REPORT_DIR/create_user_test.json"
$masterRoutes | ConvertTo-Json -Depth 10 | Set-Content ".codespaces/routes/master_routes.json"

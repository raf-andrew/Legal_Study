# Security Verification Test Script
# Tests security measures in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Security Verification"
    status = "running"
    results = @{}
}

# Test Environment Security
$environment = @{
    status = "running"
    checks = @{}
}

try {
    # Check for sensitive environment variables
    $sensitiveVars = @(
        "API_KEY",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "JWT_SECRET"
    )

    foreach ($var in $sensitiveVars) {
        if ($env:$var) {
            $environment.checks["$var"] = "present"
        } else {
            $environment.checks["$var"] = "missing"
            throw "Required security variable $var is missing"
        }
    }

    # Check file permissions
    $directories = @(
        ".codespaces",
        ".codespaces/scripts",
        ".codespaces/testing"
    )

    foreach ($dir in $directories) {
        $acl = Get-Acl $dir
        $environment.checks["$dir"] = $acl.Access | ForEach-Object {
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
    $report.error = "Environment security check failed: $($_.Exception.Message)"
    $report.results["environment"] = $environment
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["environment"] = $environment

# Test Authentication
$authentication = @{
    status = "running"
    tests = @{}
}

try {
    # Test JWT token validation
    $tokenResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/login" -Method Post -Body (@{
        username = "testuser"
        password = "testpass"
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    $token = ($tokenResponse.Content | ConvertFrom-Json).token

    if (-not $token) {
        throw "Failed to obtain JWT token"
    }

    # Test token validation
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/verify" -Headers $headers -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $authentication.tests["jwt_validation"] = "passed"
    } else {
        throw "JWT token validation failed"
    }

    # Test token expiration
    Start-Sleep -Seconds 2
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/refresh" -Method Post -Body (@{
        refresh_token = ($tokenResponse.Content | ConvertFrom-Json).refresh_token
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $authentication.tests["token_refresh"] = "passed"
    } else {
        throw "Token refresh failed"
    }

    $authentication.status = "passed"
}
catch {
    $authentication.status = "failed"
    $authentication.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Authentication testing failed: $($_.Exception.Message)"
    $report.results["authentication"] = $authentication
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["authentication"] = $authentication

# Test Authorization
$authorization = @{
    status = "running"
    tests = @{}
}

try {
    # Test role-based access control
    $roles = @("admin", "user", "guest")
    foreach ($role in $roles) {
        $roleResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/login" -Method Post -Body (@{
            username = "test_$role"
            password = "testpass"
        } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
        $roleToken = ($roleResponse.Content | ConvertFrom-Json).token

        $headers = @{
            "Authorization" = "Bearer $roleToken"
        }

        # Test access to protected resources
        $resources = @(
            @{
                path = "/api/admin"
                allowed_roles = @("admin")
            },
            @{
                path = "/api/users"
                allowed_roles = @("admin", "user")
            },
            @{
                path = "/api/public"
                allowed_roles = @("admin", "user", "guest")
            }
        )

        foreach ($resource in $resources) {
            $response = Invoke-WebRequest -Uri "http://localhost:3000$($resource.path)" -Headers $headers -UseBasicParsing
            if ($resource.allowed_roles -contains $role) {
                if ($response.StatusCode -eq 200) {
                    $authorization.tests["$role`_$($resource.path)"] = "passed"
                } else {
                    throw "Role $role should have access to $($resource.path)"
                }
            } else {
                if ($response.StatusCode -eq 403) {
                    $authorization.tests["$role`_$($resource.path)"] = "passed"
                } else {
                    throw "Role $role should not have access to $($resource.path)"
                }
            }
        }
    }

    $authorization.status = "passed"
}
catch {
    $authorization.status = "failed"
    $authorization.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Authorization testing failed: $($_.Exception.Message)"
    $report.results["authorization"] = $authorization
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["authorization"] = $authorization

# Test Security Headers
$headers = @{
    status = "running"
    tests = @{}
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    $requiredHeaders = @{
        "X-Content-Type-Options" = "nosniff"
        "X-Frame-Options" = "DENY"
        "X-XSS-Protection" = "1; mode=block"
        "Strict-Transport-Security" = "max-age=31536000; includeSubDomains"
        "Content-Security-Policy" = "default-src 'self'"
    }

    foreach ($header in $requiredHeaders.GetEnumerator()) {
        if ($response.Headers[$header.Key] -eq $header.Value) {
            $headers.tests[$header.Key] = "passed"
        } else {
            throw "Missing or incorrect security header: $($header.Key)"
        }
    }

    $headers.status = "passed"
}
catch {
    $headers.status = "failed"
    $headers.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Security headers testing failed: $($_.Exception.Message)"
    $report.results["headers"] = $headers
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["headers"] = $headers

# Complete report
$report.status = "passed"
$report.message = "Security verification completed successfully"
$report | ConvertTo-Json -Depth 10

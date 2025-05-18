# Integration Test Script
# Tests integration between components in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Integration Testing"
    status = "running"
    results = @{}
}

# Test API Integration
$api = @{
    status = "running"
    tests = @{}
}

try {
    # Test user creation and authentication flow
    $userData = @{
        username = "testuser_$TIMESTAMP"
        password = "TestPass123!"
        email = "test_$TIMESTAMP@example.com"
    }

    # Create user
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/users" -Method Post -Body ($userData | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 201) {
        $api.tests["user_creation"] = "passed"
        $userId = ($response.Content | ConvertFrom-Json).id
    } else {
        throw "User creation failed"
    }

    # Test login
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/auth/login" -Method Post -Body (@{
        username = $userData.username
        password = $userData.password
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($loginResponse.StatusCode -eq 200) {
        $api.tests["user_login"] = "passed"
        $token = ($loginResponse.Content | ConvertFrom-Json).token
    } else {
        throw "User login failed"
    }

    # Test authenticated requests
    $headers = @{
        "Authorization" = "Bearer $token"
    }

    # Test project creation
    $projectData = @{
        name = "Test Project"
        description = "Integration test project"
    }
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/projects" -Method Post -Headers $headers -Body ($projectData | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 201) {
        $api.tests["project_creation"] = "passed"
        $projectId = ($response.Content | ConvertFrom-Json).id
    } else {
        throw "Project creation failed"
    }

    # Test task creation
    $taskData = @{
        title = "Test Task"
        description = "Integration test task"
        project_id = $projectId
    }
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/tasks" -Method Post -Headers $headers -Body ($taskData | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 201) {
        $api.tests["task_creation"] = "passed"
        $taskId = ($response.Content | ConvertFrom-Json).id
    } else {
        throw "Task creation failed"
    }

    # Test data retrieval
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/projects/$projectId/tasks" -Headers $headers -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $tasks = $response.Content | ConvertFrom-Json
        if ($tasks.Count -gt 0) {
            $api.tests["data_retrieval"] = "passed"
        } else {
            throw "No tasks found in project"
        }
    } else {
        throw "Data retrieval failed"
    }

    # Clean up test data
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/users/$userId" -Method Delete -Headers $headers -UseBasicParsing
    if ($response.StatusCode -eq 204) {
        $api.tests["cleanup"] = "passed"
    } else {
        throw "Cleanup failed"
    }

    $api.status = "passed"
}
catch {
    $api.status = "failed"
    $api.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "API integration test failed: $($_.Exception.Message)"
    $report.results["api"] = $api
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["api"] = $api

# Test Database Integration
$database = @{
    status = "running"
    tests = @{}
}

try {
    # Test database connection
    Import-Module SqlServer
    $connectionString = $env:DATABASE_URL
    $query = "SELECT @@VERSION as version"
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $query
    $database.tests["connection"] = "passed"

    # Test transaction handling
    $transactionQuery = @"
    BEGIN TRANSACTION
    BEGIN TRY
        INSERT INTO users (username, email) VALUES ('test_transaction', 'test@example.com')
        INSERT INTO projects (name, user_id) VALUES ('Test Project', SCOPE_IDENTITY())
        COMMIT TRANSACTION
        SELECT 'Transaction successful' as result
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        SELECT ERROR_MESSAGE() as result
    END CATCH
"@
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $transactionQuery
    if ($result.result -eq "Transaction successful") {
        $database.tests["transactions"] = "passed"
    } else {
        throw "Transaction test failed"
    }

    # Test data consistency
    $consistencyQuery = @"
    SELECT
        u.username,
        COUNT(p.id) as project_count
    FROM users u
    LEFT JOIN projects p ON u.id = p.user_id
    GROUP BY u.username
    HAVING COUNT(p.id) > 0
"@
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $consistencyQuery
    if ($result) {
        $database.tests["data_consistency"] = "passed"
    } else {
        throw "Data consistency check failed"
    }

    $database.status = "passed"
}
catch {
    $database.status = "failed"
    $database.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Database integration test failed: $($_.Exception.Message)"
    $report.results["database"] = $database
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["database"] = $database

# Test Cache Integration
$cache = @{
    status = "running"
    tests = @{}
}

try {
    # Test cache connection
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $cache.tests["connection"] = "passed"
    } else {
        throw "Cache connection failed"
    }

    # Test cache operations
    $testKey = "test_key_$TIMESTAMP"
    $testValue = "test_value_$TIMESTAMP"

    # Set value
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/$testKey" -Method Put -Body (@{
        value = $testValue
    } | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $cache.tests["set_value"] = "passed"
    } else {
        throw "Cache set operation failed"
    }

    # Get value
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/$testKey" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $cachedValue = ($response.Content | ConvertFrom-Json).value
        if ($cachedValue -eq $testValue) {
            $cache.tests["get_value"] = "passed"
        } else {
            throw "Cache get operation returned incorrect value"
        }
    } else {
        throw "Cache get operation failed"
    }

    # Test cache expiration
    Start-Sleep -Seconds 2
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/cache/$testKey" -UseBasicParsing
    if ($response.StatusCode -eq 404) {
        $cache.tests["expiration"] = "passed"
    } else {
        throw "Cache expiration test failed"
    }

    $cache.status = "passed"
}
catch {
    $cache.status = "failed"
    $cache.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Cache integration test failed: $($_.Exception.Message)"
    $report.results["cache"] = $cache
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["cache"] = $cache

# Test External Service Integration
$external = @{
    status = "running"
    tests = @{}
}

try {
    # Test external API connections
    $externalApis = @(
        @{
            name = "GitHub"
            url = "https://api.github.com"
            expected_status = 200
        },
        @{
            name = "Database"
            url = "http://localhost:3000/api/db/health"
            expected_status = 200
        }
    )

    foreach ($api in $externalApis) {
        $response = Invoke-WebRequest -Uri $api.url -UseBasicParsing
        if ($response.StatusCode -eq $api.expected_status) {
            $external.tests[$api.name] = "passed"
        } else {
            throw "$($api.name) API connection failed"
        }
    }

    # Test webhook delivery
    $webhookData = @{
        event = "test_event"
        payload = @{
            test = "data"
        }
    }
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/webhooks/test" -Method Post -Body ($webhookData | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $external.tests["webhook_delivery"] = "passed"
    } else {
        throw "Webhook delivery failed"
    }

    $external.status = "passed"
}
catch {
    $external.status = "failed"
    $external.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "External service integration test failed: $($_.Exception.Message)"
    $report.results["external"] = $external
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["external"] = $external

# Complete report
$report.status = "passed"
$report.message = "Integration testing completed successfully"
$report | ConvertTo-Json -Depth 10

# Database Operations Test Script
# Tests database connectivity and operations in live Codespaces environment

# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Initialize report
$report = @{
    timestamp = $TIMESTAMP
    test_name = "Database Operations"
    status = "running"
    results = @{}
}

# Test Database Connection
$connection = @{
    status = "running"
    details = @{}
}

try {
    # Verify database connection string
    if (-not $env:DATABASE_URL) {
        throw "DATABASE_URL environment variable not set"
    }

    # Test connection using SQL Server module
    Import-Module SqlServer
    $connectionString = $env:DATABASE_URL
    $query = "SELECT @@VERSION as version"
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $query

    $connection.details["version"] = $result.version
    $connection.details["connection_string"] = $connectionString
    $connection.status = "passed"
}
catch {
    $connection.status = "failed"
    $connection.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Database connection failed: $($_.Exception.Message)"
    $report.results["connection"] = $connection
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["connection"] = $connection

# Test Database Operations
$operations = @{
    status = "running"
    tests = @{}
}

try {
    # Test table creation
    $createTableQuery = @"
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'test_table')
    BEGIN
        CREATE TABLE test_table (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(100),
            created_at DATETIME DEFAULT GETDATE()
        )
    END
"@
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $createTableQuery
    $operations.tests["table_creation"] = "passed"

    # Test data insertion
    $insertQuery = @"
    INSERT INTO test_table (name) VALUES ('test_record')
    SELECT SCOPE_IDENTITY() as id
"@
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $insertQuery
    $testId = $result.id
    $operations.tests["data_insertion"] = "passed"

    # Test data retrieval
    $selectQuery = "SELECT * FROM test_table WHERE id = $testId"
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $selectQuery
    if ($result.name -eq 'test_record') {
        $operations.tests["data_retrieval"] = "passed"
    } else {
        throw "Data retrieval test failed"
    }

    # Test data update
    $updateQuery = "UPDATE test_table SET name = 'updated_record' WHERE id = $testId"
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $updateQuery
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $selectQuery
    if ($result.name -eq 'updated_record') {
        $operations.tests["data_update"] = "passed"
    } else {
        throw "Data update test failed"
    }

    # Test data deletion
    $deleteQuery = "DELETE FROM test_table WHERE id = $testId"
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $deleteQuery
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $selectQuery
    if (-not $result) {
        $operations.tests["data_deletion"] = "passed"
    } else {
        throw "Data deletion test failed"
    }

    # Clean up test table
    $dropTableQuery = "DROP TABLE IF EXISTS test_table"
    Invoke-Sqlcmd -ConnectionString $connectionString -Query $dropTableQuery
    $operations.tests["cleanup"] = "passed"

    $operations.status = "passed"
}
catch {
    $operations.status = "failed"
    $operations.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Database operations testing failed: $($_.Exception.Message)"
    $report.results["operations"] = $operations
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["operations"] = $operations

# Test Database Performance
$performance = @{
    status = "running"
    metrics = @{}
}

try {
    # Test query performance
    $performanceQuery = @"
    DECLARE @StartTime DATETIME = GETDATE()
    SELECT TOP 1000 * FROM information_schema.tables
    DECLARE @EndTime DATETIME = GETDATE()
    SELECT DATEDIFF(MILLISECOND, @StartTime, @EndTime) as execution_time
"@
    $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $performanceQuery
    $performance.metrics["query_execution_time"] = $result.execution_time

    if ($result.execution_time -gt 1000) {
        throw "Query execution time exceeds threshold"
    }

    # Test concurrent connections
    $startTime = Get-Date
    $jobs = @()
    for ($i = 0; $i -lt 5; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($connString)
            Import-Module SqlServer
            $result = Invoke-Sqlcmd -ConnectionString $connString -Query "SELECT @@SPID as spid"
            return $result.spid
        } -ArgumentList $connectionString
    }
    $results = $jobs | Wait-Job | Receive-Job
    $concurrentTime = (Get-Date) - $startTime

    $performance.metrics["concurrent_connections"] = $concurrentTime.TotalMilliseconds
    if ($concurrentTime.TotalMilliseconds -gt 2000) {
        throw "Concurrent connection handling too slow"
    }

    $performance.status = "passed"
}
catch {
    $performance.status = "failed"
    $performance.error = $_.Exception.Message
    $report.status = "failed"
    $report.error = "Database performance testing failed: $($_.Exception.Message)"
    $report.results["performance"] = $performance
    $report | ConvertTo-Json -Depth 10
    exit 1
}

$report.results["performance"] = $performance

# Complete report
$report.status = "passed"
$report.message = "Database operations testing completed successfully"
$report | ConvertTo-Json -Depth 10

# Create necessary directories
$directories = @(
    ".codespaces/logs",
    ".codespaces/data",
    ".codespaces/complete",
    ".codespaces/services"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
    }
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

# Create SQLite database for Codespaces data
$dbPath = ".codespaces/data/codespaces.db"
if (-not (Test-Path $dbPath)) {
    $db = New-Object System.Data.SQLite.SQLiteConnection
    $db.ConnectionString = "Data Source=$dbPath;Version=3;"
    $db.Open()

    $command = $db.CreateCommand()
    $command.CommandText = @"
CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    service TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    issues TEXT
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    report_file TEXT
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    completion_file TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"@
    $command.ExecuteNonQuery()

    $db.Close()
}

# Create service configuration files
$services = @{
    "mysql" = @{
        "enabled" = $true
        "config" = @{
            "host" = "localhost"
            "port" = 3306
            "database" = "codespaces"
            "username" = "root"
            "password" = ""
        }
    }
    "redis" = @{
        "enabled" = $true
        "config" = @{
            "host" = "localhost"
            "port" = 6379
            "password" = $null
        }
    }
}

foreach ($service in $services.GetEnumerator()) {
    $servicePath = ".codespaces/services/$($service.Key).json"
    $service.Value | ConvertTo-Json | Set-Content $servicePath
}

# Create initial checklist items
$checklistItems = @(
    @{
        "name" = "Environment Setup"
        "description" = "Verify all required directories and configuration files are in place"
        "status" = "pending"
    },
    @{
        "name" = "Health Checks"
        "description" = "Verify all services are healthy and accessible"
        "status" = "pending"
    },
    @{
        "name" = "Database Tests"
        "description" = "Run all database-related tests"
        "status" = "pending"
    },
    @{
        "name" = "Cache Tests"
        "description" = "Run all cache-related tests"
        "status" = "pending"
    },
    @{
        "name" = "Feature Tests"
        "description" = "Run all feature tests"
        "status" = "pending"
    }
)

$db = New-Object System.Data.SQLite.SQLiteConnection
$db.ConnectionString = "Data Source=$dbPath;Version=3;"
$db.Open()

foreach ($item in $checklistItems) {
    $command = $db.CreateCommand()
    $command.CommandText = @"
    INSERT INTO checklist_items (name, description, status, created_at, updated_at)
    VALUES (@name, @description, @status, @created_at, @updated_at)
"@

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
    $command.Parameters.AddWithValue("@name", $item.name)
    $command.Parameters.AddWithValue("@description", $item.description)
    $command.Parameters.AddWithValue("@status", $item.status)
    $command.Parameters.AddWithValue("@created_at", $timestamp)
    $command.Parameters.AddWithValue("@updated_at", $timestamp)

    $command.ExecuteNonQuery()
}

$db.Close()

Write-Host "Codespaces environment setup completed successfully."

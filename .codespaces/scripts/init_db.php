<?php
$dbPath = __DIR__ . "/../data/codespaces.db";
if (file_exists($dbPath)) {
    unlink($dbPath);
}

$db = new SQLite3($dbPath);

// Create tables
$commands = [
    "CREATE TABLE health_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )",
    "CREATE TABLE test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_type TEXT NOT NULL,
        status TEXT NOT NULL,
        report_file TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )",
    "CREATE TABLE checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        completion_file TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )"
];

foreach ($commands as $cmd) {
    $db->exec($cmd);
}

// Initialize checklist items
$items = [
    "Environment Setup",
    "Health Checks",
    "Database Tests",
    "Cache Tests",
    "Feature Tests"
];

foreach ($items as $item) {
    $stmt = $db->prepare("INSERT INTO checklist_items (name, status) VALUES (:name, 'pending')");
    $stmt->bindValue(":name", $item, SQLITE3_TEXT);
    $stmt->execute();
}

// Mark Environment Setup as complete
$completionFile = __DIR__ . "/../complete/environment_setup_" . date('Y-m-d_His') . ".complete";
file_put_contents($completionFile, json_encode([
    'status' => 'complete',
    'timestamp' => date('c')
]));

$stmt = $db->prepare("UPDATE checklist_items SET status = 'complete', completion_file = :file, timestamp = CURRENT_TIMESTAMP WHERE name = 'Environment Setup'");
$stmt->bindValue(":file", $completionFile, SQLITE3_TEXT);
$stmt->execute();

$db->close();
echo "Database initialized successfully.\n";

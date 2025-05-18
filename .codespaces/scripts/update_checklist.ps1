param(
    [Parameter(Mandatory=$true)]
    [string]$ItemName,

    [Parameter(Mandatory=$true)]
    [ValidateSet('complete', 'failed', 'pending')]
    [string]$Status,

    [Parameter(Mandatory=$false)]
    [string]$CompletionFile
)

$dbPath = '.codespaces/data/codespaces.db'

# Update checklist item
$query = "UPDATE checklist_items SET status = '$Status', completion_file = '$CompletionFile', timestamp = CURRENT_TIMESTAMP WHERE name = '$ItemName'"
Invoke-SqliteQuery -Query $query -DataSource $dbPath

# Verify update
$verifyQuery = "SELECT * FROM checklist_items WHERE name = '$ItemName'"
$result = Invoke-SqliteQuery -Query $verifyQuery -DataSource $dbPath

Write-Host "Updated checklist item:"
Write-Host "Name: $($result.name)"
Write-Host "Status: $($result.status)"
Write-Host "Completion File: $($result.completion_file)"
Write-Host "Timestamp: $($result.timestamp)"

exit 0

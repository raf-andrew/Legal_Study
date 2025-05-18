param(
    [Parameter(Mandatory=$true)]
    [string]$ChecklistName,

    [Parameter(Mandatory=$false)]
    [string]$ReportPath
)

# Ensure testing and complete directories exist
$testingDir = ".codespaces/testing"
$completeDir = ".codespaces/complete"
$checklistsDir = "$completeDir/checklists"

if (-not (Test-Path $testingDir)) {
    New-Item -ItemType Directory -Force -Path $testingDir
}
if (-not (Test-Path $completeDir)) {
    New-Item -ItemType Directory -Force -Path $completeDir
}
if (-not (Test-Path $checklistsDir)) {
    New-Item -ItemType Directory -Force -Path $checklistsDir
}

# Verify checklist exists
$checklistPath = "$testingDir/$ChecklistName.md"
if (-not (Test-Path $checklistPath)) {
    Write-Error "Checklist not found: $checklistPath"
    exit 1
}

# Read checklist content
$checklist = Get-Content $checklistPath -Raw

# Check if all items are marked complete
$incompleteItems = $checklist | Select-String "- \[ \]" -AllMatches
if ($incompleteItems.Matches.Count -gt 0) {
    Write-Error "Not all items are marked complete in the checklist. Please complete all items first."
    exit 1
}

# Verify report exists if provided
if ($ReportPath -and -not (Test-Path $ReportPath)) {
    Write-Error "Report file not found: $ReportPath"
    exit 1
}

# Create completion timestamp
$timestamp = Get-Date -Format "yyyy-MM-ddTHHmmss"
$completionFile = "$checklistsDir/${ChecklistName}_${timestamp}.complete"

# Move checklist to complete directory
Move-Item $checklistPath $completionFile

# Update database
$dbPath = '.codespaces/data/codespaces.db'
$checklistItem = $ChecklistName -replace '_', ' ' -replace '\.md$', ''
$reportPath = if ($ReportPath) { $ReportPath } else { $completionFile }

$query = @"
UPDATE checklist_items
SET status = 'complete',
    completion_file = '$reportPath',
    timestamp = CURRENT_TIMESTAMP
WHERE name = '$checklistItem'
"@

Invoke-SqliteQuery -Query $query -DataSource $dbPath

Write-Host "Checklist '$ChecklistName' has been verified and moved to complete directory."
Write-Host "Database updated with completion status and report path."
exit 0

# Setup environment variables for Codespaces testing

# Set required environment variables
$env:CODESPACE_NAME = "legal-study-codespace"
$env:GITHUB_TOKEN = "ghp_placeholder_token"  # Replace with actual token
$env:DATABASE_URL = "postgresql://localhost:5432/legal_study"
$env:API_KEY = "test_api_key_placeholder"    # Replace with actual key

# Verify environment variables are set
Write-Host "Environment variables set:"
Write-Host "CODESPACE_NAME: $env:CODESPACE_NAME"
Write-Host "GITHUB_TOKEN: $env:GITHUB_TOKEN"
Write-Host "DATABASE_URL: $env:DATABASE_URL"
Write-Host "API_KEY: $env:API_KEY"

# Create required directories if they don't exist
$directories = @(
    ".codespaces",
    ".codespaces/scripts",
    ".codespaces/testing",
    ".codespaces/complete",
    ".codespaces/complete/testing"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir"
    }
}

Write-Host "Environment setup completed"

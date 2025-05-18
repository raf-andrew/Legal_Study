# Create .env file
$envContent = @"
APP_NAME="Legal Study"
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost

LOG_CHANNEL=stack
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=debug

DB_CONNECTION=mysql
DB_HOST=codespaces-mysql
DB_PORT=3306
DB_DATABASE=legal_study
DB_USERNAME=root
DB_PASSWORD=root

BROADCAST_DRIVER=pusher
CACHE_DRIVER=redis
FILESYSTEM_DISK=local
QUEUE_CONNECTION=redis
SESSION_DRIVER=redis
SESSION_LIFETIME=120

REDIS_HOST=codespaces-redis
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER=smtp
MAIL_HOST=mailpit
MAIL_PORT=1025
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="`${APP_NAME}"

CODESPACES_ENABLED=true
"@

Set-Content -Path .env -Value $envContent

# Create necessary directories
$directories = @(
    ".codespaces/logs",
    ".codespaces/complete",
    ".codespaces/verification",
    ".codespaces/checklist",
    ".codespaces/docs",
    ".codespaces/issues",
    ".codespaces/services"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Install Python dependencies
pip install mysql-connector-python redis requests

Write-Host "Environment setup completed!"

# Function to log messages
function Write-Log {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# Create necessary directories
Write-Log "Creating necessary directories..."
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

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Log "Creating .env file..."
    @"
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
DB_PASSWORD=

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

PUSHER_APP_ID=
PUSHER_APP_KEY=
PUSHER_APP_SECRET=
PUSHER_HOST=
PUSHER_PORT=443
PUSHER_SCHEME=https
PUSHER_APP_CLUSTER=mt1

CODESPACES_ENABLED=true
"@ | Out-File -FilePath .env -Encoding UTF8
}

# Install Python dependencies
Write-Log "Installing Python dependencies..."
pip install mysql-connector-python redis requests

# Install Composer dependencies
Write-Log "Installing Composer dependencies..."
composer install

# Generate Laravel application key
Write-Log "Generating Laravel application key..."
php artisan key:generate

# Run database migrations
Write-Log "Running database migrations..."
php artisan migrate:fresh --seed

Write-Log "Setup completed successfully!"

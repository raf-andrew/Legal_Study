#!/bin/bash

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create necessary directories
log "Creating necessary directories..."
mkdir -p .codespaces/{logs,complete,verification,checklist,docs,issues,services}

# Install Python and pip
log "Installing Python and pip..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Install Python dependencies
log "Installing Python dependencies..."
pip3 install mysql-connector-python redis requests

# Install PHP and extensions
log "Installing PHP and extensions..."
sudo add-apt-repository ppa:ondrej/php -y
sudo apt-get update
sudo apt-get install -y php8.2 php8.2-cli php8.2-common php8.2-curl php8.2-mbstring php8.2-mysql php8.2-xml php8.2-zip php8.2-gd php8.2-redis

# Install Composer
log "Installing Composer..."
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer

# Install Laravel dependencies
log "Installing Laravel dependencies..."
composer install

# Setup Laravel environment
log "Setting up Laravel environment..."
cp .env.example .env
php artisan key:generate

# Setup database
log "Setting up database..."
php artisan migrate:fresh --seed

# Clear Redis
log "Clearing Redis..."
redis-cli FLUSHALL

# Enable Codespaces configuration
log "Enabling Codespaces configuration..."
sed -i 's/CODESPACES_ENABLED=false/CODESPACES_ENABLED=true/' .env

log "Setup completed successfully!"

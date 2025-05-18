#!/bin/bash

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Install system dependencies
log "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    software-properties-common \
    curl \
    git \
    unzip \
    zip

# Install PHP and extensions
log "Installing PHP and extensions..."
sudo add-apt-repository -y ppa:ondrej/php
sudo apt-get update
sudo apt-get install -y \
    php8.2 \
    php8.2-cli \
    php8.2-common \
    php8.2-curl \
    php8.2-mbstring \
    php8.2-mysql \
    php8.2-xml \
    php8.2-zip \
    php8.2-gd \
    php8.2-redis

# Install Composer
log "Installing Composer..."
curl -sS https://getcomposer.org/installer | sudo php -- --install-dir=/usr/local/bin --filename=composer

# Install Node.js and npm
log "Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python dependencies
log "Installing Python dependencies..."
pip install mysql-connector-python redis requests

# Create necessary directories
log "Creating necessary directories..."
mkdir -p .codespaces/{logs,complete,verification,docs,issues,services}

# Set up Laravel environment
log "Setting up Laravel environment..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Generate application key
log "Generating application key..."
php artisan key:generate

# Install Laravel dependencies
log "Installing Laravel dependencies..."
composer install

# Install Node.js dependencies
log "Installing Node.js dependencies..."
npm install

# Set up database
log "Setting up database..."
php artisan migrate:fresh --seed

# Set up Redis
log "Setting up Redis..."
php artisan redis:clear

log "Environment setup completed successfully!"

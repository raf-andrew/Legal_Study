FROM php:8.3-cli

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    unzip \
    libzip-dev \
    && docker-php-ext-install zip

# Install Xdebug for coverage reporting
RUN pecl install xdebug \
    && docker-php-ext-enable xdebug

# Configure Xdebug
RUN echo "xdebug.mode=coverage" >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini \
    && echo "xdebug.start_with_request=yes" >> /usr/local/etc/php/conf.d/docker-php-ext-xdebug.ini

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files
COPY composer.json composer.lock ./

# Install dependencies
RUN composer install --no-scripts --no-autoloader

# Copy application files
COPY . .

# Generate autoloader
RUN composer dump-autoload --optimize

# Create directories for test reports
RUN mkdir -p reports/coverage \
    && mkdir -p reports/verification \
    && mkdir -p reports/certification

# Set environment variables
ENV XDEBUG_MODE=coverage

# Default command
CMD ["php", "vendor/bin/phpunit", "--coverage-html", "reports/coverage"]

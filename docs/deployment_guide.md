# Deployment Guide

## Environment Setup

### System Requirements

1. PHP 8.1 or higher
2. Required PHP extensions:
   - pdo
   - pdo_mysql
   - redis
   - json
   - mbstring
   - openssl
3. Operating System:
   - Linux (recommended)
   - Windows
   - macOS
4. Memory:
   - Minimum: 512MB
   - Recommended: 1GB
5. Storage:
   - Minimum: 100MB
   - Recommended: 1GB

### Dependencies

1. Cache:
   - Redis 6.0 or higher
   - Memcached 1.6 or higher
2. Database:
   - MySQL 8.0 or higher
   - PostgreSQL 13 or higher
3. Filesystem:
   - Write permissions
   - Minimum 1GB free space

### Configuration

1. Environment Variables:
   ```bash
   export APP_ENV=production
   export APP_DEBUG=false
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_NAME=app_db
   export DB_USER=app_user
   export DB_PASS=secret
   export CACHE_HOST=localhost
   export CACHE_PORT=6379
   ```

2. Configuration Files:
   ```yaml
   # config/production.yaml
   debug: false
   error_reporting: E_ALL & ~E_DEPRECATED & ~E_NOTICE
   
   cache:
     driver: redis
     host: ${CACHE_HOST}
     port: ${CACHE_PORT}
   
   database:
     driver: mysql
     host: ${DB_HOST}
     port: ${DB_PORT}
     database: ${DB_NAME}
     username: ${DB_USER}
     password: ${DB_PASS}
   ```

### Security Setup

1. File Permissions:
   ```bash
   # Set directory permissions
   chmod 755 /var/www/app
   chmod 755 /var/www/app/cache
   chmod 755 /var/www/app/logs
   
   # Set file permissions
   chmod 644 /var/www/app/config/*.yaml
   chmod 600 /var/www/app/config/secrets.yaml
   ```

2. Database Security:
   ```sql
   -- Create application user
   CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'secret';
   GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'app_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. Cache Security:
   ```bash
   # Redis configuration
   requirepass secret
   bind 127.0.0.1
   protected-mode yes
   ```

## Deployment Process

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/app.git /var/www/app
   cd /var/www/app
   ```

2. Install dependencies:
   ```bash
   composer install --no-dev --optimize-autoloader
   ```

3. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

4. Initialize application:
   ```bash
   php bin/console app:init
   ```

### Configuration Steps

1. Configure web server:
   ```nginx
   # nginx configuration
   server {
       listen 80;
       server_name app.example.com;
       root /var/www/app/public;
       
       location / {
           try_files $uri /index.php$is_args$args;
       }
       
       location ~ ^/index\.php(/|$) {
           fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
           fastcgi_split_path_info ^(.+\.php)(/.*)$;
           include fastcgi_params;
           fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
           fastcgi_param DOCUMENT_ROOT $realpath_root;
           internal;
       }
   }
   ```

2. Configure PHP:
   ```ini
   ; php.ini
   memory_limit = 256M
   max_execution_time = 30
   error_reporting = E_ALL & ~E_DEPRECATED & ~E_NOTICE
   display_errors = Off
   log_errors = On
   error_log = /var/log/php/error.log
   ```

### Verification Steps

1. Check system requirements:
   ```bash
   php bin/console app:check
   ```

2. Verify configuration:
   ```bash
   php bin/console app:verify
   ```

3. Test connections:
   ```bash
   php bin/console app:test
   ```

4. Run health checks:
   ```bash
   php bin/console app:health
   ```

### Rollback Procedures

1. Backup current version:
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz /var/www/app
   ```

2. Restore previous version:
   ```bash
   # Stop application
   systemctl stop app.service
   
   # Restore backup
   tar -xzf backup-20230101.tar.gz -C /
   
   # Start application
   systemctl start app.service
   ```

## Maintenance

### Monitoring Setup

1. Configure metrics collection:
   ```yaml
   # config/monitoring.yaml
   metrics:
     interval: 60
     retention: 30d
     aggregation: 1h
   ```

2. Set up logging:
   ```yaml
   # config/logging.yaml
   handlers:
     file:
       path: /var/log/app/app.log
       level: info
       max_files: 7
   ```

3. Configure alerts:
   ```yaml
   # config/alerts.yaml
   thresholds:
     cpu: 80
     memory: 85
     disk: 90
   channels:
     - email
     - slack
   ```

### Logging Configuration

1. Application logs:
   ```yaml
   # config/logging.yaml
   app:
     path: /var/log/app/app.log
     level: info
     max_files: 7
     max_size: 10M
   ```

2. Error logs:
   ```yaml
   # config/logging.yaml
   error:
     path: /var/log/app/error.log
     level: error
     max_files: 30
     max_size: 10M
   ```

3. Access logs:
   ```yaml
   # config/logging.yaml
   access:
     path: /var/log/app/access.log
     level: info
     max_files: 7
     max_size: 10M
   ```

### Backup Procedures

1. Database backup:
   ```bash
   # Daily backup
   0 0 * * * mysqldump -u root -p app_db | gzip > /backup/db/app_db_$(date +\%Y\%m\%d).sql.gz
   
   # Weekly backup
   0 0 * * 0 mysqldump -u root -p app_db | gzip > /backup/db/app_db_week_$(date +\%Y\%W).sql.gz
   ```

2. Filesystem backup:
   ```bash
   # Daily backup
   0 2 * * * tar -czf /backup/fs/app_$(date +\%Y\%m\%d).tar.gz /var/www/app
   
   # Weekly backup
   0 2 * * 0 tar -czf /backup/fs/app_week_$(date +\%Y\%W).tar.gz /var/www/app
   ```

3. Configuration backup:
   ```bash
   # Daily backup
   0 1 * * * tar -czf /backup/config/app_config_$(date +\%Y\%m\%d).tar.gz /var/www/app/config
   ```

### Update Procedures

1. Prepare update:
   ```bash
   # Backup current version
   tar -czf backup-$(date +%Y%m%d).tar.gz /var/www/app
   
   # Pull latest changes
   cd /var/www/app
   git fetch origin
   git checkout v1.2.3
   ```

2. Apply update:
   ```bash
   # Install dependencies
   composer install --no-dev --optimize-autoloader
   
   # Run migrations
   php bin/console doctrine:migrations:migrate
   
   # Clear cache
   php bin/console cache:clear
   ```

3. Verify update:
   ```bash
   # Run health checks
   php bin/console app:health
   
   # Test functionality
   php bin/console app:test
   ```

4. Rollback if needed:
   ```bash
   # Stop application
   systemctl stop app.service
   
   # Restore backup
   tar -xzf backup-20230101.tar.gz -C /
   
   # Start application
   systemctl start app.service
   ``` 
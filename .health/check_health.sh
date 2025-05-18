#!/bin/bash

# Health Check Script

# Configuration
CONFIG_FILE=".health/health_config.json"
LOG_FILE=".health/health_check.log"
REPORT_FILE=".health/health_report.md"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check system requirements
check_system_requirements() {
    log_message "Checking system requirements..."
    
    # Check OS
    OS=$(uname -s)
    if [[ "$OS" == "Linux" || "$OS" == "Darwin" || "$OS" == "MINGW"* ]]; then
        log_message "✓ OS check passed: $OS"
    else
        log_message "✗ Unsupported OS: $OS"
    fi

    # Check Node.js version
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        log_message "✓ Node.js version: $NODE_VERSION"
    else
        log_message "✗ Node.js not installed"
    fi

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -V)
        log_message "✓ Python version: $PYTHON_VERSION"
    else
        log_message "✗ Python not installed"
    fi

    # Check memory
    MEMORY=$(free -h | grep Mem | awk '{print $2}')
    log_message "✓ Available memory: $MEMORY"

    # Check disk space
    DISK_SPACE=$(df -h / | awk 'NR==2 {print $4}')
    log_message "✓ Available disk space: $DISK_SPACE"
}

# Function to check dependencies
check_dependencies() {
    log_message "Checking dependencies..."
    
    # Check npm packages
    for package in $(jq -r '.health_checks.system_requirements.dependencies.required_packages[]' "$CONFIG_FILE"); do
        if npm list -g "$package" &> /dev/null; then
            log_message "✓ Package installed: $package"
        else
            log_message "✗ Package missing: $package"
        fi
    done

    # Check services
    for service in $(jq -r '.health_checks.system_requirements.dependencies.required_services[]' "$CONFIG_FILE"); do
        case $service in
            "mongodb")
                if command -v mongod &> /dev/null; then
                    log_message "✓ MongoDB service available"
                else
                    log_message "✗ MongoDB service not available"
                fi
                ;;
            "redis")
                if command -v redis-cli &> /dev/null; then
                    log_message "✓ Redis service available"
                else
                    log_message "✗ Redis service not available"
                fi
                ;;
        esac
    done
}

# Function to check connections
check_connections() {
    log_message "Checking service connections..."
    
    # Check MongoDB connection
    MONGODB_HOST=$(jq -r '.health_checks.connection_checks.database.mongodb.host' "$CONFIG_FILE")
    if mongosh "$MONGODB_HOST" --eval "db.version()" &> /dev/null; then
        log_message "✓ MongoDB connection successful"
    else
        log_message "✗ MongoDB connection failed"
    fi

    # Check Redis connection
    REDIS_HOST=$(jq -r '.health_checks.connection_checks.database.redis.host' "$CONFIG_FILE")
    REDIS_PORT=$(jq -r '.health_checks.connection_checks.database.redis.port' "$CONFIG_FILE")
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
        log_message "✓ Redis connection successful"
    else
        log_message "✗ Redis connection failed"
    fi
}

# Function to check API endpoints
check_api_endpoints() {
    log_message "Checking API endpoints..."
    
    # Get API endpoints from config
    jq -r '.health_checks.service_checks.api.endpoints[]' "$CONFIG_FILE" | while read -r endpoint; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$endpoint" | grep -q "200"; then
            log_message "✓ API endpoint available: $endpoint"
        else
            log_message "✗ API endpoint unavailable: $endpoint"
        fi
    done
}

# Function to generate report
generate_report() {
    log_message "Generating health report..."
    
    echo "# System Health Report" > "$REPORT_FILE"
    echo "Generated: $(date)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## System Requirements" >> "$REPORT_FILE"
    grep "✓\|✗" "$LOG_FILE" | grep "system requirements" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## Dependencies" >> "$REPORT_FILE"
    grep "✓\|✗" "$LOG_FILE" | grep "dependencies" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## Connections" >> "$REPORT_FILE"
    grep "✓\|✗" "$LOG_FILE" | grep "connection" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## API Endpoints" >> "$REPORT_FILE"
    grep "✓\|✗" "$LOG_FILE" | grep "API endpoint" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Main execution
main() {
    echo "Starting health check..."
    echo "=== Health Check Started $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"
    
    check_system_requirements
    check_dependencies
    check_connections
    check_api_endpoints
    generate_report
    
    echo "Health check completed. See $REPORT_FILE for details."
}

# Run main function
main 
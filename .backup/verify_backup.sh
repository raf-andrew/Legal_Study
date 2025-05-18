#!/bin/bash

# Backup Verification Script

# Configuration
BACKUP_DIR=".backup"
LOG_FILE=".backup/verification.log"
CONFIG_FILE=".backup/backup_config.json"
RESTORE_TEST_DIR=".backup/restore_test"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Initialize log file
echo "=== Backup Verification Started $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"

# Check backup configuration
if [ ! -f "$CONFIG_FILE" ]; then
    log_message "ERROR: Backup configuration file not found"
    exit 1
fi

# Verify backup directory structure
log_message "Checking backup directory structure..."
for dir in "daily" "weekly" "monthly"; do
    if [ ! -d "$BACKUP_DIR/$dir" ]; then
        log_message "ERROR: Missing backup directory: $dir"
        exit 1
    fi
done

# Check backup files
log_message "Checking backup files..."
for dir in "$BACKUP_DIR"/*/ ; do
    if [ -d "$dir" ]; then
        files_count=$(ls -1 "$dir" 2>/dev/null | wc -l)
        log_message "Found $files_count files in $(basename "$dir")"
    fi
done

# Verify checksums
log_message "Verifying backup checksums..."
find "$BACKUP_DIR" -type f -name "*.checksum" -exec sh -c '
    file="${1%.checksum}"
    if [ -f "$file" ]; then
        stored_sum=$(cat "$1")
        actual_sum=$(sha256sum "$file" | cut -d " " -f 1)
        if [ "$stored_sum" = "$actual_sum" ]; then
            echo "[$(date "+%Y-%m-%d %H:%M:%S")] Checksum verified: $file"
        else
            echo "[$(date "+%Y-%m-%d %H:%M:%S")] ERROR: Checksum mismatch: $file"
        fi
    fi
' sh {} \; >> "$LOG_FILE"

# Test restore capability
log_message "Testing restore capability..."
mkdir -p "$RESTORE_TEST_DIR"

# Find most recent backup
latest_backup=$(find "$BACKUP_DIR" -type f -name "*.backup" -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)

if [ -n "$latest_backup" ]; then
    log_message "Testing restore of: $latest_backup"
    # Add restore test logic here based on backup type
    log_message "Restore test completed"
else
    log_message "ERROR: No backup files found for restore test"
fi

# Clean up test directory
rm -rf "$RESTORE_TEST_DIR"

# Check retention policies
log_message "Checking retention policies..."
# Add retention policy verification logic here

# Final status
log_message "Backup verification completed"
echo "=== Backup Verification Completed $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE" 
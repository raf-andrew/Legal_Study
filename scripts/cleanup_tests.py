#!/usr/bin/env python3

import os
import sys
import logging
import shutil
from pathlib import Path
import yaml
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/cleanup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestCleanup:
    def __init__(self):
        self.config = None
        self.cleanup_stats = {
            'files_removed': 0,
            'directories_removed': 0,
            'bytes_freed': 0
        }
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load cleanup configuration."""
        try:
            config_file = Path('.config/test_config.yaml')
            if not config_file.exists():
                logger.error("Configuration file not found")
                sys.exit(1)
            
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            
            logger.info("Loaded cleanup configuration")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def cleanup_test_db(self):
        """Cleanup test database."""
        try:
            if self.config['cleanup']['remove_test_db']:
                db_path = Path(self.config['database']['name'])
                if db_path.exists():
                    db_path.unlink()
                    self.cleanup_stats['files_removed'] += 1
                    self.cleanup_stats['bytes_freed'] += db_path.stat().st_size
                    logger.info(f"Removed test database: {db_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning up test database: {e}")
    
    def cleanup_logs(self):
        """Cleanup log files."""
        try:
            if self.config['cleanup']['remove_logs']:
                log_dir = Path('.logs')
                if log_dir.exists():
                    for log_file in log_dir.glob('*.log'):
                        log_file.unlink()
                        self.cleanup_stats['files_removed'] += 1
                        self.cleanup_stats['bytes_freed'] += log_file.stat().st_size
                        logger.info(f"Removed log file: {log_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
    
    def cleanup_reports(self):
        """Cleanup test reports."""
        try:
            if self.config['cleanup']['remove_reports']:
                # Remove HTML reports
                for report_file in Path('.').glob('*.html'):
                    if report_file.name.startswith('test_report'):
                        report_file.unlink()
                        self.cleanup_stats['files_removed'] += 1
                        self.cleanup_stats['bytes_freed'] += report_file.stat().st_size
                        logger.info(f"Removed report file: {report_file}")
                
                # Remove coverage reports
                coverage_dir = Path('htmlcov')
                if coverage_dir.exists():
                    shutil.rmtree(coverage_dir)
                    self.cleanup_stats['directories_removed'] += 1
                    logger.info(f"Removed coverage directory: {coverage_dir}")
            
        except Exception as e:
            logger.error(f"Error cleaning up reports: {e}")
    
    def cleanup_cache(self):
        """Cleanup cache files."""
        try:
            if self.config['cleanup']['remove_cache']:
                # Remove pytest cache
                cache_dir = Path('.pytest_cache')
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    self.cleanup_stats['directories_removed'] += 1
                    logger.info(f"Removed pytest cache: {cache_dir}")
                
                # Remove Python cache
                for cache_file in Path('.').rglob('__pycache__'):
                    shutil.rmtree(cache_file)
                    self.cleanup_stats['directories_removed'] += 1
                    logger.info(f"Removed Python cache: {cache_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def cleanup_old_files(self):
        """Cleanup old test files."""
        try:
            # Get retention period from config or default to 7 days
            retention_days = self.config.get('cleanup', {}).get('retention_days', 7)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Cleanup old test data
            test_data_dir = Path('test_data')
            if test_data_dir.exists():
                for data_file in test_data_dir.glob('*.json'):
                    file_date = datetime.fromtimestamp(data_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        data_file.unlink()
                        self.cleanup_stats['files_removed'] += 1
                        self.cleanup_stats['bytes_freed'] += data_file.stat().st_size
                        logger.info(f"Removed old test data: {data_file}")
            
            # Cleanup old error logs
            error_dir = Path('.errors')
            if error_dir.exists():
                for error_file in error_dir.glob('*.log'):
                    file_date = datetime.fromtimestamp(error_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        error_file.unlink()
                        self.cleanup_stats['files_removed'] += 1
                        self.cleanup_stats['bytes_freed'] += error_file.stat().st_size
                        logger.info(f"Removed old error log: {error_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
    
    def print_stats(self):
        """Print cleanup statistics."""
        logger.info("Cleanup Statistics:")
        logger.info(f"Files removed: {self.cleanup_stats['files_removed']}")
        logger.info(f"Directories removed: {self.cleanup_stats['directories_removed']}")
        logger.info(f"Bytes freed: {self.cleanup_stats['bytes_freed'] / 1024 / 1024:.2f} MB")
    
    def cleanup(self):
        """Main cleanup process."""
        try:
            logger.info("Starting test cleanup")
            
            # Cleanup test database
            self.cleanup_test_db()
            
            # Cleanup logs
            self.cleanup_logs()
            
            # Cleanup reports
            self.cleanup_reports()
            
            # Cleanup cache
            self.cleanup_cache()
            
            # Cleanup old files
            self.cleanup_old_files()
            
            # Print statistics
            self.print_stats()
            
            logger.info("Test cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup process: {e}")
            sys.exit(1)

if __name__ == "__main__":
    cleanup = TestCleanup()
    cleanup.cleanup() 
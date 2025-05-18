#!/usr/bin/env python3
import pytest
import os
import sys
import logging
from datetime import datetime
import json
import psutil
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/test_suite.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        '.logs',
        '.errors',
        '.complete',
        '.benchmarks',
        '.health'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def record_system_info():
    """Record system information before running tests."""
    system_info = {
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'python_version': sys.version,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('.health/system_info.json', 'w') as f:
        json.dump(system_info, f, indent=2)

def run_test_suite():
    """Run the complete test suite."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Record test start
    logger.info(f"Starting test suite at {timestamp}")
    
    try:
        # Run smoke tests
        logger.info("Running smoke tests...")
        result = pytest.main(["-v", "-m", "smoke", "--html=.complete/smoke_test_report.html"])
        if result != 0:
            logger.error("Smoke tests failed")
            with open(f'.errors/smoke_test_failure_{timestamp}.txt', 'w') as f:
                f.write(f"Smoke tests failed at {datetime.now()}\n")
            return False
        
        # Run ACID tests
        logger.info("Running ACID tests...")
        result = pytest.main(["-v", "-m", "acid", "--html=.complete/acid_test_report.html"])
        if result != 0:
            logger.error("ACID tests failed")
            with open(f'.errors/acid_test_failure_{timestamp}.txt', 'w') as f:
                f.write(f"ACID tests failed at {datetime.now()}\n")
            return False
        
        # Run chaos tests
        logger.info("Running chaos tests...")
        result = pytest.main(["-v", "-m", "chaos", "--html=.complete/chaos_test_report.html"])
        if result != 0:
            logger.error("Chaos tests failed")
            with open(f'.errors/chaos_test_failure_{timestamp}.txt', 'w') as f:
                f.write(f"Chaos tests failed at {datetime.now()}\n")
            return False
        
        # Run security tests
        logger.info("Running security tests...")
        result = pytest.main(["-v", "-m", "security", "--html=.complete/security_test_report.html"])
        if result != 0:
            logger.error("Security tests failed")
            with open(f'.errors/security_test_failure_{timestamp}.txt', 'w') as f:
                f.write(f"Security tests failed at {datetime.now()}\n")
            return False
        
        # All tests passed
        logger.info("All tests passed successfully")
        with open(f'.complete/test_suite_success_{timestamp}.txt', 'w') as f:
            f.write(f"Test suite completed successfully at {datetime.now()}\n")
        return True
        
    except Exception as e:
        logger.error(f"Error running test suite: {e}")
        with open(f'.errors/test_suite_error_{timestamp}.txt', 'w') as f:
            f.write(f"Test suite error at {datetime.now()}: {str(e)}\n")
        return False

def cleanup_old_reports():
    """Clean up old test reports and logs."""
    # Keep only last 5 reports
    for directory in ['.complete', '.errors']:
        files = sorted(os.listdir(directory))
        if len(files) > 5:
            for old_file in files[:-5]:
                os.remove(os.path.join(directory, old_file))

def main():
    """Main function to run the test suite."""
    setup_directories()
    record_system_info()
    success = run_test_suite()
    cleanup_old_reports()
    
    if success:
        logger.info("Test suite completed successfully")
        sys.exit(0)
    else:
        logger.error("Test suite failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 
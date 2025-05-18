#!/usr/bin/env python3
import subprocess
import sys
import logging
from datetime import datetime
from monitor import SystemMonitor
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/monitored_tests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_monitored_tests():
    """Run tests with system monitoring."""
    try:
        # Start system monitoring
        monitor = SystemMonitor(interval=1)
        monitor.start()
        logger.info("System monitoring started")
        
        # Run tests
        logger.info("Starting test execution")
        result = subprocess.run([sys.executable, 'run_tests.py'], capture_output=True, text=True)
        
        # Stop monitoring
        monitor.stop()
        logger.info("System monitoring stopped")
        
        # Save test output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('.logs/test_output')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / f'test_output_{timestamp}.log', 'w') as f:
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
        
        # Check test results
        if result.returncode != 0:
            logger.error("Tests failed")
            with open('.errors/test_execution_error.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Tests failed with return code {result.returncode}")
            sys.exit(1)
        
        logger.info("Tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running monitored tests: {e}")
        with open('.errors/monitored_tests_error.log', 'a') as f:
            f.write(f"\n{datetime.now()} - Error running monitored tests: {str(e)}")
        return False

def main():
    """Main function."""
    try:
        success = run_monitored_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Monitored tests failed: {e}")
        with open('.errors/monitored_tests_error.log', 'a') as f:
            f.write(f"\n{datetime.now()} - Monitored tests failed: {str(e)}")
        sys.exit(2)

if __name__ == '__main__':
    main() 
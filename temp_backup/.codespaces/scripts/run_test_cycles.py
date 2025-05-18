#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/test_cycles.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestCycleRunner:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.verification_dir = Path('.codespaces/verification')
        self.complete_dir = Path('.codespaces/complete')
        self.checklist_dir = Path('.codespaces/checklist')

        # Create necessary directories
        for directory in [self.log_dir, self.verification_dir, self.complete_dir, self.checklist_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def run_health_check(self):
        """Run health check before tests"""
        logging.info("Running health check...")
        result = subprocess.run(['python', '.codespaces/scripts/health_check.py'],
                              capture_output=True, text=True)
        return result.returncode == 0

    def run_tests(self):
        """Run Laravel feature tests"""
        logging.info("Running feature tests...")
        result = subprocess.run(['php', 'artisan', 'test', '--testsuite=Feature'],
                              capture_output=True, text=True)
        return result

    def save_test_results(self, test_output, cycle_number):
        """Save test results and link to checklist"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f"feature_tests_cycle{cycle_number}_{timestamp}.log"

        # Save test output
        with open(log_file, 'w') as f:
            f.write(test_output.stdout)
            if test_output.stderr:
                f.write("\nErrors:\n")
                f.write(test_output.stderr)

        # If tests passed, move to complete and link to checklist
        if test_output.returncode == 0:
            complete_file = self.complete_dir / f"feature_tests_cycle{cycle_number}_{timestamp}.log"
            shutil.move(log_file, complete_file)

            # Update checklist
            checklist_file = self.checklist_dir / "feature_tests.md"
            with open(checklist_file, 'a') as f:
                f.write(f"\n- [x] Cycle {cycle_number} completed at {timestamp}\n")
                f.write(f"  - Report: {complete_file}\n")

            logging.info(f"Tests passed, results saved to {complete_file}")
            return True
        else:
            logging.error(f"Tests failed, results saved to {log_file}")
            # Delete failed log after review
            os.remove(log_file)
            return False

    def run_cycle(self, cycle_number):
        """Run a single test cycle"""
        logging.info(f"Starting test cycle {cycle_number}...")

        # Run health check
        if not self.run_health_check():
            logging.error("Health check failed, skipping test cycle")
            return False

        # Run tests
        test_result = self.run_tests()
        return self.save_test_results(test_result, cycle_number)

    def run_cycles(self, num_cycles=10):
        """Run multiple test cycles"""
        successful_cycles = 0
        failed_cycles = 0

        for cycle in range(1, num_cycles + 1):
            if self.run_cycle(cycle):
                successful_cycles += 1
            else:
                failed_cycles += 1

        logging.info(f"Test cycles completed: {successful_cycles} successful, {failed_cycles} failed")
        return successful_cycles == num_cycles

def main():
    runner = TestCycleRunner()
    success = runner.run_cycles()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

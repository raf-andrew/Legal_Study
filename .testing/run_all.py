#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/run_all.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestRunner:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.testing_dir = self.workspace_root / '.testing'
        
        # Scripts to run in order
        self.scripts = [
            'verify_env.py',
            'verify_database.py', 
            'verify_security.py',
            'run_verification.py',
            'update_checklist.py'
        ]
        
    def run_script(self, script: str) -> bool:
        """Run a verification script and return success status"""
        script_path = self.testing_dir / script
        
        if not script_path.exists():
            logging.error(f"Script not found: {script}")
            return False
            
        try:
            logging.info(f"Running {script}...")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=True,
                text=True
            )
            logging.info(f"{script} output:\n{result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running {script}:\n{e.stderr}")
            return False
            
    def run_all(self) -> bool:
        """Run all verification scripts"""
        start_time = datetime.now()
        logging.info("Starting verification process...")
        
        success = True
        for script in self.scripts:
            if not self.run_script(script):
                success = False
                break
                
        end_time = datetime.now()
        duration = end_time - start_time
        
        if success:
            logging.info(f"All verifications completed successfully in {duration}")
        else:
            logging.error(f"Verification process failed after {duration}")
            
        return success

if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1) 
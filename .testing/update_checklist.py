#!/usr/bin/env python3

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/checklist_update.log'),
        logging.StreamHandler()
    ]
)

class ChecklistUpdater:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.checklist_path = self.workspace_root / '.testing' / 'checklist.md'
        self.verification_report_path = self.workspace_root / '.testing' / 'verification_report.json'
        self.results = {}

    def load_verification_results(self):
        """Load the verification results from the JSON report."""
        try:
            with open(self.verification_report_path, 'r') as f:
                self.results = json.load(f)
            logging.info(f"Loaded verification results from {self.verification_report_path}")
        except FileNotFoundError:
            logging.error(f"Verification report not found at {self.verification_report_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in verification report at {self.verification_report_path}")
            sys.exit(1)

    def update_checklist(self):
        """Update the checklist based on verification results."""
        try:
            with open(self.checklist_path, 'r') as f:
                checklist_content = f.read()

            # Update environment checks
            if self.results.get('environment', {}).get('status') == 'pass':
                checklist_content = checklist_content.replace(
                    "[ ] Environment setup verified",
                    "[x] Environment setup verified"
                )

            # Update database checks
            if self.results.get('database', {}).get('status') == 'pass':
                checklist_content = checklist_content.replace(
                    "[ ] Database setup verified",
                    "[x] Database setup verified"
                )

            # Update security checks
            if self.results.get('security', {}).get('status') == 'pass':
                checklist_content = checklist_content.replace(
                    "[ ] Security setup verified",
                    "[x] Security setup verified"
                )

            # Add timestamp of last verification
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            checklist_content = checklist_content.replace(
                "Last verified: Never",
                f"Last verified: {timestamp}"
            )

            with open(self.checklist_path, 'w') as f:
                f.write(checklist_content)

            logging.info(f"Successfully updated checklist at {self.checklist_path}")

        except FileNotFoundError:
            logging.error(f"Checklist file not found at {self.checklist_path}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error updating checklist: {str(e)}")
            sys.exit(1)

    def run(self):
        """Run the checklist update process."""
        self.load_verification_results()
        self.update_checklist()

if __name__ == '__main__':
    updater = ChecklistUpdater()
    updater.run() 
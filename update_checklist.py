#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import re
from typing import Dict, Any, List

class ChecklistUpdater:
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.checklist_file = self.workspace_root / '.testing' / 'checklist.md'
        self.results_file = self.workspace_root / '.testing' / 'verification_report.json'
        
    def load_checklist(self) -> str:
        """Load the checklist content"""
        with open(self.checklist_file) as f:
            return f.read()
    
    def load_results(self) -> Dict[str, Any]:
        """Load verification results"""
        with open(self.results_file) as f:
            return json.load(f)
    
    def update_checklist(self, checklist: str, results: Dict[str, Any]) -> str:
        """Update checklist based on verification results"""
        # Update environment setup
        if all(check['status'] == 'pass' for checks in results['details'].values() for check in checks.values()):
            checklist = re.sub(
                r'(\[ \]) Environment Setup',
                r'[x] Environment Setup',
                checklist
            )
        
        # Update database setup
        if all(check['status'] == 'pass' for check in results['details'].get('verify_database.py', {}).values()):
            checklist = re.sub(
                r'(\[ \]) Database Setup',
                r'[x] Database Setup',
                checklist
            )
        
        # Update security setup
        if all(check['status'] == 'pass' for check in results['details'].get('verify_security.py', {}).values()):
            checklist = re.sub(
                r'(\[ \]) Security Setup',
                r'[x] Security Setup',
                checklist
            )
        
        return checklist
    
    def save_checklist(self, checklist: str) -> None:
        """Save updated checklist"""
        with open(self.checklist_file, 'w') as f:
            f.write(checklist)
    
    def run(self) -> None:
        """Run checklist update"""
        try:
            # Load current checklist
            checklist = self.load_checklist()
            
            # Load verification results
            results = self.load_results()
            
            # Update checklist
            updated_checklist = self.update_checklist(checklist, results)
            
            # Save updated checklist
            self.save_checklist(updated_checklist)
            
            print("Checklist updated successfully")
            
        except Exception as e:
            print(f"Error updating checklist: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    updater = ChecklistUpdater()
    updater.run() 
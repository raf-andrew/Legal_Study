#!/usr/bin/env python3
"""
Checklist validation script.
Validates checklist format and content.
"""
import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChecklistValidator:
    def __init__(self):
        self.checklist_dir = Path("checklists")
        self.required_sections = [
            "Test Framework",
            "Test Cases",
            "Test Data",
            "Documentation",
            "Quality Assurance",
            "Testing",
            "Monitoring",
            "Deployment",
            "Maintenance"
        ]

    def validate_checklist_format(self, content: str) -> bool:
        """Validate the format of a checklist file."""
        lines = content.split("\n")
        has_title = False
        has_sections = False

        for line in lines:
            if line.startswith("# "):
                has_title = True
            elif line.startswith("## "):
                has_sections = True

        return has_title and has_sections

    def validate_checklist_content(self, content: str) -> List[str]:
        """Validate the content of a checklist file."""
        errors = []

        # Check for required sections
        for section in self.required_sections:
            if f"## {section}" not in content:
                errors.append(f"Missing required section: {section}")

        # Check for proper checkbox format
        checkbox_pattern = r"- \[[ x]\]"
        if not re.search(checkbox_pattern, content):
            errors.append("No checkboxes found in checklist")

        return errors

    def validate_all_checklists(self) -> Dict[str, List[str]]:
        """Validate all checklist files in the checklists directory."""
        results = {}

        if not self.checklist_dir.exists():
            logger.error(f"Checklist directory not found: {self.checklist_dir}")
            return results

        for checklist_file in self.checklist_dir.glob("**/*.md"):
            try:
                with open(checklist_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if not self.validate_checklist_format(content):
                    results[str(checklist_file)] = ["Invalid checklist format"]
                    continue

                errors = self.validate_checklist_content(content)
                if errors:
                    results[str(checklist_file)] = errors

            except Exception as e:
                results[str(checklist_file)] = [f"Error processing file: {str(e)}"]

        return results

def main():
    validator = ChecklistValidator()
    results = validator.validate_all_checklists()

    if results:
        logger.error("Checklist validation failed:")
        for file, errors in results.items():
            logger.error(f"\n{file}:")
            for error in errors:
                logger.error(f"  - {error}")
        exit(1)
    else:
        logger.info("All checklists validated successfully!")

if __name__ == "__main__":
    main()

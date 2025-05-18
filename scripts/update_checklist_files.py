#!/usr/bin/env python3
"""
Update checklist files based on test results.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from scripts.test_tracker import TestTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChecklistUpdater:
    def __init__(self, checklist_dir: str = "checklists"):
        self.checklist_dir = Path(checklist_dir)
        self.tracker = TestTracker()

    def update_checklist_files(self) -> bool:
        """Update all checklist files based on test results."""
        try:
            if not self.checklist_dir.exists():
                logger.error(f"Checklist directory not found: {self.checklist_dir}")
                return False

            items = self.tracker._load_checklist_items()
            if not items:
                logger.error("No checklist items found")
                return False

            # Group items by checklist file
            checklist_items = self._group_items_by_checklist(items)

            # Update each checklist file
            for file_path, file_items in checklist_items.items():
                self._update_checklist_file(file_path, file_items)

            logger.info("Successfully updated checklist files")
            return True

        except Exception as e:
            logger.error(f"Error updating checklist files: {str(e)}")
            return False

    def _group_items_by_checklist(self, items: Dict) -> Dict[Path, List[Dict]]:
        """Group checklist items by their source file."""
        checklist_items = {}

        for item in items.values():
            # Extract checklist name from item ID
            checklist_name = item["id"].split("-")[0]

            # Find matching checklist file
            for file_path in self.checklist_dir.glob("**/*.md"):
                if self._get_checklist_name(file_path) == checklist_name:
                    if file_path not in checklist_items:
                        checklist_items[file_path] = []
                    checklist_items[file_path].append(item)
                    break

        return checklist_items

    def _get_checklist_name(self, file_path: Path) -> str:
        """Get the checklist name from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract checklist name from title
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            if title_match:
                name = title_match.group(1)
                return re.sub(r"[^A-Z0-9]", "", name.upper())

        except Exception as e:
            logger.error(f"Error reading checklist file {file_path}: {str(e)}")

        return file_path.stem.upper()

    def _update_checklist_file(self, file_path: Path, items: List[Dict]) -> None:
        """Update a checklist file with test results."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Update each item in the file
            for item in items:
                content = self._update_item_in_content(content, item)

            # Write updated content back to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Error updating checklist file {file_path}: {str(e)}")

    def _update_item_in_content(self, content: str, item: Dict) -> str:
        """Update a checklist item in the file content."""
        # Find the item in the content
        item_pattern = rf"- \[[ x]\] {re.escape(item['description'])}$"
        match = re.search(item_pattern, content, re.MULTILINE)

        if match:
            # Determine checkbox state based on test coverage
            checkbox = "[x]" if item["test_coverage"] >= 100.0 else "[ ]"

            # Create updated item line
            updated_line = f"- {checkbox} {item['description']}"

            # Replace the old line with the updated one
            content = content[:match.start()] + updated_line + content[match.end():]

        return content

def main():
    """Main function for updating checklist files."""
    updater = ChecklistUpdater()
    success = updater.update_checklist_files()

    if success:
        logger.info("Successfully updated checklist files")
    else:
        logger.error("Failed to update checklist files")
        exit(1)

if __name__ == "__main__":
    main()

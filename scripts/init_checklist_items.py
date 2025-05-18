#!/usr/bin/env python3
"""
Initialize checklist items from existing checklists.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from scripts.test_tracker import TestTracker, ChecklistItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChecklistInitializer:
    def __init__(self, checklist_dir: str = "checklists"):
        self.checklist_dir = Path(checklist_dir)
        self.tracker = TestTracker()

    def initialize_checklist_items(self) -> bool:
        """Initialize checklist items from all checklist files."""
        try:
            if not self.checklist_dir.exists():
                logger.error(f"Checklist directory not found: {self.checklist_dir}")
                return False

            checklist_items = {}

            for checklist_file in self.checklist_dir.glob("**/*.md"):
                items = self._parse_checklist_file(checklist_file)
                checklist_items.update(items)

            # Save checklist items
            self.tracker._save_checklist_items(checklist_items)
            logger.info(f"Initialized {len(checklist_items)} checklist items")
            return True

        except Exception as e:
            logger.error(f"Error initializing checklist items: {str(e)}")
            return False

    def _parse_checklist_file(self, file_path: Path) -> Dict[str, Dict]:
        """Parse a checklist file and extract items."""
        items = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract checklist name from title
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            checklist_name = title_match.group(1) if title_match else file_path.stem

            # Find all checklist items
            item_pattern = r"- \[[ x]\] (.+)$"
            for match in re.finditer(item_pattern, content, re.MULTILINE):
                item_text = match.group(1)
                item_id = self._generate_item_id(checklist_name, item_text)

                items[item_id] = {
                    "id": item_id,
                    "description": item_text,
                    "status": "in_progress",
                    "test_coverage": 0.0,
                    "last_updated": "",
                    "test_results": [],
                    "dependencies": []
                }

        except Exception as e:
            logger.error(f"Error parsing checklist file {file_path}: {str(e)}")

        return items

    def _generate_item_id(self, checklist_name: str, item_text: str) -> str:
        """Generate a unique ID for a checklist item."""
        # Create a base ID from the checklist name
        base = re.sub(r"[^A-Z0-9]", "", checklist_name.upper())
        if not base:
            base = "CLI"

        # Create a unique suffix from the item text
        suffix = re.sub(r"[^A-Z0-9]", "", item_text.upper())[:8]
        if not suffix:
            suffix = "ITEM"

        return f"{base}-{suffix}"

def main():
    """Main function for initializing checklist items."""
    initializer = ChecklistInitializer()
    success = initializer.initialize_checklist_items()

    if success:
        logger.info("Successfully initialized checklist items")
    else:
        logger.error("Failed to initialize checklist items")
        exit(1)

if __name__ == "__main__":
    main()

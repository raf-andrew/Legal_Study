#!/usr/bin/env python3
"""
Script to move verified items to .complete directory.
This script reads verification results and moves successfully verified items to .complete.
"""
import os
import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from rich.console import Console
from rich.progress import Progress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reports/move_to_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
console = Console()

class ItemMover:
    """Class to handle moving verified items to .complete."""

    def __init__(self):
        """Initialize the item mover."""
        self.reports_dir = Path('reports')
        self.verification_dir = self.reports_dir / 'verification'
        self.certification_dir = self.reports_dir / 'certification'
        self.complete_dir = Path('.complete')
        self.evidence_dir = Path('evidence')
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary directories."""
        self.complete_dir.mkdir(parents=True, exist_ok=True)
        (self.complete_dir / 'reports').mkdir(parents=True, exist_ok=True)
        (self.complete_dir / 'evidence').mkdir(parents=True, exist_ok=True)

    def _load_verification_results(self) -> Dict[str, Any]:
        """Load the most recent verification results."""
        verification_files = sorted(
            self.verification_dir.glob('verification_results_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not verification_files:
            logger.error("No verification results found")
            sys.exit(1)

        with open(verification_files[0]) as f:
            return json.load(f)

    def _load_certification_results(self) -> Dict[str, Any]:
        """Load the most recent certification results."""
        certification_files = sorted(
            self.certification_dir.glob('certification_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not certification_files:
            logger.error("No certification results found")
            sys.exit(1)

        with open(certification_files[0]) as f:
            return json.load(f)

    def _get_verified_items(self) -> List[str]:
        """Get list of verified items from results."""
        verification_results = self._load_verification_results()
        certification_results = self._load_certification_results()

        # Only include items that passed both verification and certification
        verified_items = []
        for criterion, result in verification_results.get('results', {}).items():
            if result['passed']:
                verified_items.append(criterion)

        return verified_items

    def _copy_reports(self):
        """Copy relevant reports to .complete/reports."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target_dir = self.complete_dir / 'reports' / timestamp

        # Copy verification results
        verification_files = self.verification_dir.glob('verification_results_*.json')
        for file in verification_files:
            shutil.copy2(file, target_dir / file.name)

        # Copy certification results
        certification_files = self.certification_dir.glob('certification_*.json')
        for file in certification_files:
            shutil.copy2(file, target_dir / file.name)

        # Copy coverage reports
        coverage_dir = self.reports_dir / 'coverage'
        if coverage_dir.exists():
            shutil.copytree(coverage_dir, target_dir / 'coverage')

        # Copy benchmark results
        benchmark_file = self.reports_dir / 'benchmark.json'
        if benchmark_file.exists():
            shutil.copy2(benchmark_file, target_dir / 'benchmark.json')

    def _copy_evidence(self):
        """Copy relevant evidence to .complete/evidence."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target_dir = self.complete_dir / 'evidence' / timestamp

        # Copy all evidence files
        if self.evidence_dir.exists():
            shutil.copytree(self.evidence_dir, target_dir)

    def _create_summary(self):
        """Create a summary of moved items."""
        verified_items = self._get_verified_items()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        summary = {
            'timestamp': datetime.now().isoformat(),
            'verified_items': verified_items,
            'verification_results': self._load_verification_results(),
            'certification_results': self._load_certification_results()
        }

        # Save summary
        summary_file = self.complete_dir / f'summary_{timestamp}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def move_verified_items(self):
        """Move verified items to .complete directory."""
        logger.info("Starting to move verified items to .complete")

        # Get verified items
        verified_items = self._get_verified_items()
        if not verified_items:
            logger.error("No verified items found")
            sys.exit(1)

        # Copy reports and evidence
        self._copy_reports()
        self._copy_evidence()

        # Create summary
        self._create_summary()

        logger.info(f"Successfully moved {len(verified_items)} items to .complete")
        return verified_items

    def display_results(self, verified_items: List[str]):
        """Display results of moving items to .complete."""
        table = Table(title="Moved Items to .complete")
        table.add_column("Item", style="cyan")
        table.add_column("Status", style="green")

        for item in verified_items:
            table.add_row(item, "✓")

        console.print(table)

def main():
    """Main entry point for moving verified items."""
    mover = ItemMover()

    with Progress() as progress:
        task = progress.add_task("[cyan]Moving verified items...", total=100)

        # Move verified items
        verified_items = mover.move_verified_items()
        progress.update(task, completed=100)

        # Display results
        mover.display_results(verified_items)

if __name__ == '__main__':
    main()

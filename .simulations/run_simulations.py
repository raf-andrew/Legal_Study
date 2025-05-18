#!/usr/bin/env python3

"""
Master simulation runner for coordinating all platform simulations.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simulation_runner")

class SimulationRunner:
    """Coordinates and runs platform simulations."""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.reports_dir = self.base_dir / "reports"
        self.categories = ["data_processing", "ui_ux", "integration"]
        self.simulation_types = {
            "data_processing": [
                "load_testing",
                "data_validation",
                "error_handling",
                "state_management",
                "data_flow"
            ],
            "ui_ux": [
                "user_flows",
                "accessibility",
                "performance",
                "responsive",
                "interaction"
            ],
            "integration": [
                "end_to_end",
                "api_integration",
                "service_orchestration",
                "system_integration",
                "cross_platform"
            ]
        }

    def setup_environment(self) -> None:
        """Setup simulation environment."""
        logger.info("Setting up simulation environment")
        os.makedirs(self.reports_dir, exist_ok=True)

        for category in self.categories:
            category_dir = self.reports_dir / category
            os.makedirs(category_dir, exist_ok=True)

            for sim_type in self.simulation_types[category]:
                sim_dir = category_dir / sim_type
                os.makedirs(sim_dir, exist_ok=True)

    def run_simulation(self, category: str, sim_type: str) -> Dict[str, Any]:
        """Run a specific simulation."""
        logger.info(f"Running {category}/{sim_type} simulation")

        try:
            # Import the simulation module dynamically
            module_path = f"{category}.{sim_type}.{sim_type}_test"
            simulation = __import__(module_path, fromlist=["*"])

            # Run simulation steps
            config = simulation.setup_simulation()
            results = simulation.execute_simulation(config)
            analysis = simulation.analyze_results(results)

            return {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "type": sim_type,
                "config": config,
                "results": results,
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error running simulation: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "type": sim_type,
                "error": str(e)
            }

    def save_report(self, report: Dict[str, Any]) -> None:
        """Save simulation report."""
        try:
            category = report["category"]
            sim_type = report["type"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            report_path = self.reports_dir / category / sim_type / f"report_{timestamp}.json"

            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"Report saved: {report_path}")
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")

    def cleanup_old_reports(self, days: int = 90) -> None:
        """Clean up reports older than specified days."""
        logger.info(f"Cleaning up reports older than {days} days")

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for category in self.categories:
            category_dir = self.reports_dir / category
            for sim_type in self.simulation_types[category]:
                sim_dir = category_dir / sim_type

                if not sim_dir.exists():
                    continue

                for report_file in sim_dir.glob("report_*.json"):
                    if report_file.stat().st_mtime < cutoff:
                        report_file.unlink()
                        logger.info(f"Deleted old report: {report_file}")

    def run_all_simulations(self) -> List[Dict[str, Any]]:
        """Run all simulations."""
        reports = []

        for category in self.categories:
            for sim_type in self.simulation_types[category]:
                report = self.run_simulation(category, sim_type)
                self.save_report(report)
                reports.append(report)

        return reports

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Platform Simulation Runner")
    parser.add_argument("--category", choices=["data_processing", "ui_ux", "integration"],
                      help="Simulation category to run")
    parser.add_argument("--type", help="Specific simulation type to run")
    parser.add_argument("--cleanup", type=int, help="Clean up reports older than N days")

    args = parser.parse_args()

    runner = SimulationRunner()
    runner.setup_environment()

    if args.cleanup:
        runner.cleanup_old_reports(args.cleanup)
        return

    if args.category and args.type:
        if args.type not in runner.simulation_types[args.category]:
            logger.error(f"Invalid simulation type for category {args.category}")
            return

        report = runner.run_simulation(args.category, args.type)
        runner.save_report(report)
    else:
        reports = runner.run_all_simulations()
        logger.info(f"Completed {len(reports)} simulations")

if __name__ == "__main__":
    main()

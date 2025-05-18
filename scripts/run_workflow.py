"""
Script to run complete sniffing workflow.
"""
import argparse
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("run_workflow")

class WorkflowRunner:
    """Class for running complete sniffing workflow."""

    def __init__(self):
        """Initialize runner."""
        self.root_dir = Path.cwd()
        self.scripts_dir = self.root_dir / "scripts"

    async def run(
        self,
        steps: Optional[List[str]] = None,
        watch: bool = False,
        report_format: str = "html"
    ) -> None:
        """Run workflow.

        Args:
            steps: Optional list of steps to run
            watch: Whether to watch for changes
            report_format: Report format
        """
        try:
            # Get steps
            all_steps = [
                "setup",
                "monitoring",
                "sniffing",
                "report"
            ]
            steps = steps or all_steps

            # Run steps
            for step in steps:
                if step == "setup":
                    await self._run_setup()
                elif step == "monitoring":
                    await self._run_monitoring()
                elif step == "sniffing":
                    await self._run_sniffing(watch)
                elif step == "report":
                    await self._run_report(report_format)
                else:
                    logger.warning(f"Unknown step: {step}")

        except Exception as e:
            logger.error(f"Error running workflow: {e}")
            raise

    async def _run_setup(self) -> None:
        """Run setup step."""
        try:
            logger.info("Running setup...")

            # Install Git hooks
            script = self.scripts_dir / "install_hooks.py"
            result = subprocess.run([sys.executable, str(script)])
            if result.returncode != 0:
                raise Exception("Failed to install Git hooks")

            logger.info("Setup completed")

        except Exception as e:
            logger.error(f"Error in setup: {e}")
            raise

    async def _run_monitoring(self) -> None:
        """Run monitoring step."""
        try:
            logger.info("Setting up monitoring...")

            # Install monitoring
            script = self.scripts_dir / "install_monitoring.py"
            result = subprocess.run([sys.executable, str(script)])
            if result.returncode != 0:
                raise Exception("Failed to install monitoring")

            # Start monitoring services
            monitoring_dir = self.root_dir / "monitoring"
            if not monitoring_dir.exists():
                raise Exception("Monitoring directory not found")

            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=monitoring_dir
            )
            if result.returncode != 0:
                raise Exception("Failed to start monitoring services")

            logger.info("Monitoring started")

        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            raise

    async def _run_sniffing(self, watch: bool = False) -> None:
        """Run sniffing step.

        Args:
            watch: Whether to watch for changes
        """
        try:
            logger.info("Running sniffing...")

            # Run initial sniffing
            script = self.scripts_dir / "initial_sniffing.py"
            result = subprocess.run([sys.executable, str(script)])
            if result.returncode != 0:
                raise Exception("Initial sniffing failed")

            # Start development mode if watching
            if watch:
                script = self.scripts_dir / "run_dev.py"
                process = subprocess.Popen([sys.executable, str(script)])
                try:
                    process.wait()
                except KeyboardInterrupt:
                    process.terminate()
                    process.wait()

            logger.info("Sniffing completed")

        except Exception as e:
            logger.error(f"Error in sniffing: {e}")
            raise

    async def _run_report(self, format: str = "html") -> None:
        """Run report step.

        Args:
            format: Report format
        """
        try:
            logger.info("Generating report...")

            # Generate report
            script = self.scripts_dir / "generate_report.py"
            result = subprocess.run([
                sys.executable,
                str(script),
                "--format",
                format
            ])
            if result.returncode != 0:
                raise Exception("Failed to generate report")

            logger.info("Report generated")

        except Exception as e:
            logger.error(f"Error in report: {e}")
            raise

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run complete sniffing workflow"
        )
        parser.add_argument(
            "--steps",
            type=str,
            help="Comma-separated list of steps to run"
        )
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Watch for changes"
        )
        parser.add_argument(
            "--report-format",
            type=str,
            choices=["html", "markdown", "json"],
            default="html",
            help="Report format"
        )
        args = parser.parse_args()

        # Get steps
        steps = args.steps.split(",") if args.steps else None

        # Run workflow
        runner = WorkflowRunner()
        asyncio.run(runner.run(
            steps=steps,
            watch=args.watch,
            report_format=args.report_format
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

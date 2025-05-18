"""
Script to run sniffing infrastructure in production mode.
"""
import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from prometheus_client import start_http_server

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_production")

class ProductionRunner:
    """Class for running sniffing infrastructure in production mode."""

    def __init__(self):
        """Initialize runner."""
        self.root_dir = Path.cwd()
        self.config_path = self.root_dir / "sniffing/config/sniffing_config.yaml"
        self.server: Optional[MCPServer] = None
        self.running = True

    async def run(
        self,
        domains: Optional[List[str]] = None,
        interval: int = 3600,
        report_format: str = "html"
    ) -> None:
        """Run production mode.

        Args:
            domains: Optional list of domains to run
            interval: Interval between runs in seconds
            report_format: Report format
        """
        try:
            # Load config
            if not self.config_path.exists():
                logger.error("Config file not found")
                return

            # Create MCP server
            self.server = MCPServer(str(self.config_path))

            # Start server
            server_task = asyncio.create_task(self.server.start())

            try:
                # Start metrics server
                metrics_port = self.server.config["mcp"]["monitoring"]["prometheus_port"]
                start_http_server(metrics_port)
                logger.info(f"Metrics server started on port {metrics_port}")

                # Run continuous sniffing
                while self.running:
                    # Run sniffing
                    await self._run_sniffing(domains)

                    # Generate report
                    await self._generate_report(report_format)

                    # Wait for next run
                    logger.info(f"Waiting {interval} seconds until next run")
                    await asyncio.sleep(interval)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running production mode: {e}")
            raise

    async def _run_sniffing(self, domains: Optional[List[str]] = None) -> None:
        """Run sniffing.

        Args:
            domains: Optional list of domains to run
        """
        try:
            if not self.server:
                return

            logger.info("Running sniffing...")

            # Get all files
            files = []
            ignore_dirs = {".git", "venv", "__pycache__", "node_modules"}
            ignore_exts = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib"}

            for root, dirs, filenames in os.walk("."):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_dirs]

                for filename in filenames:
                    # Skip ignored extensions
                    if Path(filename).suffix in ignore_exts:
                        continue

                    # Add file
                    file_path = os.path.join(root, filename)
                    files.append(file_path)

            # Run sniffing
            result = await self.server.sniff({
                "files": files,
                "domains": domains,
                "fix": True,
                "priority": 1
            })

            # Check result
            if result.get("status") != "completed":
                logger.error("Sniffing failed")
                return

            # Log issues
            results = result.get("results", {})
            for file_path, file_results in results.items():
                for domain, domain_result in file_results.items():
                    issues = domain_result.get("issues", [])
                    if issues:
                        logger.info(
                            f"{file_path} ({domain}): "
                            f"{len(issues)} issues found"
                        )

            logger.info("Sniffing completed")

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            raise

    async def _generate_report(self, format: str = "html") -> None:
        """Generate report.

        Args:
            format: Report format
        """
        try:
            logger.info("Generating report...")

            # Generate report
            script = self.root_dir / "scripts/generate_report.py"
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
            logger.error(f"Error generating report: {e}")
            raise

    def stop(self) -> None:
        """Stop production mode."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping production mode...")
    if runner:
        runner.stop()

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("production.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in production mode"
        )
        parser.add_argument(
            "--domains",
            type=str,
            help="Comma-separated list of domains to run"
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=3600,
            help="Interval between runs in seconds"
        )
        parser.add_argument(
            "--report-format",
            type=str,
            choices=["html", "markdown", "json"],
            default="html",
            help="Report format"
        )
        args = parser.parse_args()

        # Get domains
        domains = args.domains.split(",") if args.domains else None

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run production mode
        global runner
        runner = ProductionRunner()
        asyncio.run(runner.run(
            domains=domains,
            interval=args.interval,
            report_format=args.report_format
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()

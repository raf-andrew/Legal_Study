"""
Script to run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files.
"""
import argparse
import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_domains_files")

class DomainFileRunner:
    """Class for running sniffing infrastructure in a specific mode with a specific configuration and specific domains and files."""

    def __init__(self, mode: str, config_path: str, domains: List[str], files: List[str]):
        """Initialize runner.

        Args:
            mode: Mode to run in
            config_path: Path to configuration file
            domains: List of domains to run
            files: List of files to run
        """
        self.mode = mode
        self.config_path = Path(config_path)
        self.domains = domains
        self.files = files
        self.server: Optional[MCPServer] = None
        self.running = True

    async def run(
        self,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run in specific mode with specific configuration and specific domains and files.

        Args:
            verbose: Whether to enable verbose logging
            trace: Whether to enable trace logging
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
                # Run sniffing
                await self._run_sniffing(verbose, trace)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running in {self.mode} mode with config {self.config_path}, domains {self.domains}, and files {self.files}: {e}")
            raise

    async def _run_sniffing(
        self,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run sniffing.

        Args:
            verbose: Whether to enable verbose logging
            trace: Whether to enable trace logging
        """
        try:
            if not self.server:
                return

            logger.info(f"Running sniffing in {self.mode} mode with config {self.config_path}, domains {self.domains}, and files {self.files}...")

            # Get priority based on mode
            priority = {
                "debug": 5,
                "profile": 6,
                "test": 7,
                "prod": 8,
                "ci": 9,
                "all": 10
            }.get(self.mode, 0)

            # Run sniffing
            result = await self.server.sniff({
                "files": self.files,
                "domains": self.domains,
                "verbose": verbose,
                "trace": trace,
                "priority": priority
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

                        # Log issue details
                        for issue in issues:
                            logger.info(
                                f"  - {issue.get('title')} "
                                f"({issue.get('severity')}): "
                                f"{issue.get('description')}"
                            )

                            if issue.get("fix"):
                                logger.info(f"    Fix: {issue.get('fix')}")

                            if issue.get("trace"):
                                logger.info("    Trace:")
                                for line in issue.get("trace", []):
                                    logger.info(f"      {line}")

            logger.info("Sniffing completed")

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            raise

    def stop(self) -> None:
        """Stop runner."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping runner...")
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
                logging.FileHandler("run_domains_files.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files"
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["debug", "profile", "test", "prod", "ci", "all"],
            required=True,
            help="Mode to run in"
        )
        parser.add_argument(
            "--config",
            type=str,
            required=True,
            help="Path to configuration file"
        )
        parser.add_argument(
            "--domains",
            type=str,
            required=True,
            help="Comma-separated list of domains to run"
        )
        parser.add_argument(
            "--files",
            type=str,
            required=True,
            help="Comma-separated list of files to run"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging"
        )
        parser.add_argument(
            "--trace",
            action="store_true",
            help="Enable trace logging"
        )
        args = parser.parse_args()

        # Get domains and files
        domains = args.domains.split(",")
        files = args.files.split(",")

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run in specific mode with specific configuration and specific domains and files
        global runner
        runner = DomainFileRunner(args.mode, args.config, domains, files)
        asyncio.run(runner.run(
            verbose=args.verbose,
            trace=args.trace
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()

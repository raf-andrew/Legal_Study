"""
Script to run sniffing infrastructure in CI mode.
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

logger = logging.getLogger("run_ci")

class CIRunner:
    """Class for running sniffing infrastructure in CI mode."""

    def __init__(self):
        """Initialize runner."""
        self.root_dir = Path.cwd()
        self.config_path = self.root_dir / "sniffing/config/sniffing_config.yaml"
        self.server: Optional[MCPServer] = None
        self.running = True

    async def run(
        self,
        domains: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run CI mode.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
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
                await self._run_sniffing(domains, files, verbose, trace)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running CI mode: {e}")
            raise

    async def _run_sniffing(
        self,
        domains: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run sniffing.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
            verbose: Whether to enable verbose logging
            trace: Whether to enable trace logging
        """
        try:
            if not self.server:
                return

            logger.info("Running sniffing...")

            # Get files to run
            if not files:
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
                "verbose": verbose,
                "trace": trace,
                "priority": 9
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
        """Stop CI mode."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping CI mode...")
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
                logging.FileHandler("ci.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in CI mode"
        )
        parser.add_argument(
            "--domains",
            type=str,
            help="Comma-separated list of domains to run"
        )
        parser.add_argument(
            "--files",
            type=str,
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
        domains = args.domains.split(",") if args.domains else None
        files = args.files.split(",") if args.files else None

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run CI mode
        global runner
        runner = CIRunner()
        asyncio.run(runner.run(
            domains=domains,
            files=files,
            verbose=args.verbose,
            trace=args.trace
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()

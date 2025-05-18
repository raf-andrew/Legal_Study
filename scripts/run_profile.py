"""
Script to run sniffing infrastructure in profile mode.
"""
import argparse
import asyncio
import cProfile
import logging
import os
import pstats
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_profile")

class ProfileRunner:
    """Class for running sniffing infrastructure in profile mode."""

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
        sort_by: str = "cumulative",
        limit: int = 20
    ) -> None:
        """Run profile mode.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
            sort_by: Sort key for profile results
            limit: Number of results to show
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
                await self._run_sniffing(domains, files, sort_by, limit)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running profile mode: {e}")
            raise

    async def _run_sniffing(
        self,
        domains: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        sort_by: str = "cumulative",
        limit: int = 20
    ) -> None:
        """Run sniffing.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
            sort_by: Sort key for profile results
            limit: Number of results to show
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

            # Create profiler
            profiler = cProfile.Profile()

            # Run sniffing with profiler
            profiler.enable()
            result = await self.server.sniff({
                "files": files,
                "domains": domains,
                "priority": 6
            })
            profiler.disable()

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

            # Print profile results
            stats = pstats.Stats(profiler)
            stats.sort_stats(sort_by)
            stats.print_stats(limit)

            # Save profile results
            profile_file = f"profile_{datetime.now():%Y%m%d_%H%M%S}.prof"
            stats.dump_stats(profile_file)
            logger.info(f"Profile results saved to: {profile_file}")

            logger.info("Sniffing completed")

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            raise

    def stop(self) -> None:
        """Stop profile mode."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping profile mode...")
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
                logging.FileHandler("profile.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in profile mode"
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
            "--sort-by",
            type=str,
            choices=["calls", "cumulative", "file", "line", "module", "name", "nfl", "pcalls", "stdname", "time"],
            default="cumulative",
            help="Sort key for profile results"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Number of results to show"
        )
        args = parser.parse_args()

        # Get domains and files
        domains = args.domains.split(",") if args.domains else None
        files = args.files.split(",") if args.files else None

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run profile mode
        global runner
        runner = ProfileRunner()
        asyncio.run(runner.run(
            domains=domains,
            files=files,
            sort_by=args.sort_by,
            limit=args.limit
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()

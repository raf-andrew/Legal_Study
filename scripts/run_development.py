"""
Script to run sniffing infrastructure in development mode.
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

logger = logging.getLogger("run_development")

class DevelopmentRunner:
    """Class for running sniffing infrastructure in development mode."""

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
        watch: bool = False,
        fix: bool = False
    ) -> None:
        """Run development mode.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
            watch: Whether to watch for file changes
            fix: Whether to automatically fix issues
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
                await self._run_sniffing(domains, files, fix)

                # Watch for changes
                if watch:
                    await self._watch_files(domains, fix)

            finally:
                # Stop server
                await self.server.shutdown()
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error running development mode: {e}")
            raise

    async def _run_sniffing(
        self,
        domains: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        fix: bool = False
    ) -> None:
        """Run sniffing.

        Args:
            domains: Optional list of domains to run
            files: Optional list of files to run
            fix: Whether to automatically fix issues
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
                "fix": fix,
                "priority": 2
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

    async def _watch_files(
        self,
        domains: Optional[List[str]] = None,
        fix: bool = False
    ) -> None:
        """Watch files for changes.

        Args:
            domains: Optional list of domains to run
            fix: Whether to automatically fix issues
        """
        try:
            logger.info("Watching files for changes...")

            # Get files to watch
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

            # Watch files
            while self.running:
                # Check for changes
                changed_files = []
                for file_path in files:
                    try:
                        stat = os.stat(file_path)
                        mtime = stat.st_mtime
                        if mtime > getattr(self, "_last_mtime", {}).get(file_path, 0):
                            changed_files.append(file_path)
                            self._last_mtime = getattr(self, "_last_mtime", {})
                            self._last_mtime[file_path] = mtime
                    except OSError:
                        continue

                # Run sniffing on changed files
                if changed_files:
                    logger.info(f"Files changed: {', '.join(changed_files)}")
                    await self._run_sniffing(domains, changed_files, fix)

                # Wait for next check
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error watching files: {e}")
            raise

    def stop(self) -> None:
        """Stop development mode."""
        self.running = False

def handle_signal(signum, frame):
    """Handle signal.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Stopping development mode...")
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
                logging.FileHandler("development.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in development mode"
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
            "--watch",
            action="store_true",
            help="Watch for file changes"
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Automatically fix issues"
        )
        args = parser.parse_args()

        # Get domains and files
        domains = args.domains.split(",") if args.domains else None
        files = args.files.split(",") if args.files else None

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run development mode
        global runner
        runner = DevelopmentRunner()
        asyncio.run(runner.run(
            domains=domains,
            files=files,
            watch=args.watch,
            fix=args.fix
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    runner = None
    main()

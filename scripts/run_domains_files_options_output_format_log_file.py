"""
Script to run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file.
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import signal
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_domains_files_options_output_format_log_file")

class DomainFileOptionOutputFormatLogFileRunner:
    """Class for running sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file."""

    def __init__(
        self,
        mode: str,
        config_path: str,
        domains: List[str],
        files: List[str],
        options: Dict[str, any],
        output_path: str,
        output_format: str,
        log_level: str,
        log_file: str
    ):
        """Initialize runner.

        Args:
            mode: Mode to run in
            config_path: Path to configuration file
            domains: List of domains to run
            files: List of files to run
            options: Dictionary of options to use
            output_path: Path to output file
            output_format: Format of output file
            log_level: Level of logging
            log_file: Path to log file
        """
        self.mode = mode
        self.config_path = Path(config_path)
        self.domains = domains
        self.files = files
        self.options = options
        self.output_path = Path(output_path)
        self.output_format = output_format
        self.log_level = log_level
        self.log_file = Path(log_file)
        self.server: Optional[MCPServer] = None
        self.running = True

    async def run(
        self,
        verbose: bool = False,
        trace: bool = False
    ) -> None:
        """Run in specific mode with specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file.

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
            logger.error(f"Error running in {self.mode} mode with config {self.config_path}, domains {self.domains}, files {self.files}, options {self.options}, output {self.output_path}, format {self.output_format}, log level {self.log_level}, and log file {self.log_file}: {e}")
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

            logger.info(f"Running sniffing in {self.mode} mode with config {self.config_path}, domains {self.domains}, files {self.files}, options {self.options}, output {self.output_path}, format {self.output_format}, log level {self.log_level}, and log file {self.log_file}...")

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
                "priority": priority,
                **self.options
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

            # Write output
            if self.output_format == "json":
                with open(self.output_path, "w") as f:
                    json.dump(result, f, indent=2)
            elif self.output_format == "yaml":
                with open(self.output_path, "w") as f:
                    yaml.dump(result, f, indent=2)
            elif self.output_format == "csv":
                with open(self.output_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["file", "domain", "title", "severity", "description", "fix", "trace"])
                    for file_path, file_results in results.items():
                        for domain, domain_result in file_results.items():
                            for issue in domain_result.get("issues", []):
                                writer.writerow([
                                    file_path,
                                    domain,
                                    issue.get("title"),
                                    issue.get("severity"),
                                    issue.get("description"),
                                    issue.get("fix"),
                                    "\n".join(issue.get("trace", []))
                                ])
            else:
                logger.error(f"Unsupported output format: {self.output_format}")
                return

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
        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Run sniffing infrastructure in a specific mode with a specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file"
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
            "--options",
            type=str,
            required=True,
            help="Comma-separated list of options to use in key=value format"
        )
        parser.add_argument(
            "--output",
            type=str,
            required=True,
            help="Path to output file"
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["json", "yaml", "csv"],
            required=True,
            help="Format of output file"
        )
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["debug", "info", "warning", "error", "critical"],
            required=True,
            help="Level of logging"
        )
        parser.add_argument(
            "--log-file",
            type=str,
            required=True,
            help="Path to log file"
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

        # Set up logging
        logging.basicConfig(
            level=getattr(logging, args.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(args.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Get domains and files
        domains = args.domains.split(",")
        files = args.files.split(",")

        # Get options
        options = {}
        for option in args.options.split(","):
            key, value = option.split("=")
            options[key] = value

        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Run in specific mode with specific configuration and specific domains and files and specific options and specific output and specific format and specific log level and specific log file
        global runner
        runner = DomainFileOptionOutputFormatLogFileRunner(args.mode, args.config, domains, files, options, args.output, args.format, args.log_level, args.log_file)
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

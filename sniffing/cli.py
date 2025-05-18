"""
Command-line interface for sniffing infrastructure.
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .core.base import SniffingLoop
from .core.git import GitWorkflow
from .core.utils.logging import setup_logger

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Sniffing infrastructure CLI"
    )

    # Add commands
    subparsers = parser.add_subparsers(dest="command")

    # Sniff command
    sniff_parser = subparsers.add_parser(
        "sniff",
        help="Run sniffing"
    )
    sniff_parser.add_argument(
        "--files",
        help="Files to sniff (comma-separated)",
        type=str
    )
    sniff_parser.add_argument(
        "--domains",
        help="Domains to check (comma-separated)",
        type=str
    )
    sniff_parser.add_argument(
        "--config",
        help="Configuration file",
        type=str,
        default="sniffing/config/sniffing_config.yaml"
    )
    sniff_parser.add_argument(
        "--report-dir",
        help="Report directory",
        type=str,
        default="reports"
    )

    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Install Git hooks"
    )
    install_parser.add_argument(
        "--config",
        help="Configuration file",
        type=str,
        default="sniffing/config/sniffing_config.yaml"
    )

    # Fix command
    fix_parser = subparsers.add_parser(
        "fix",
        help="Fix issues"
    )
    fix_parser.add_argument(
        "--files",
        help="Files to fix (comma-separated)",
        type=str
    )
    fix_parser.add_argument(
        "--domains",
        help="Domains to fix (comma-separated)",
        type=str
    )
    fix_parser.add_argument(
        "--config",
        help="Configuration file",
        type=str,
        default="sniffing/config/sniffing_config.yaml"
    )

    return parser.parse_args()

async def run_sniffing(args: argparse.Namespace) -> None:
    """Run sniffing command.

    Args:
        args: Command-line arguments
    """
    try:
        # Load configuration
        with open(args.config) as f:
            config = yaml.safe_load(f)

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "sniffing_cli"
        )

        # Create sniffing loop
        loop = SniffingLoop(config)

        # Get files
        files = []
        if args.files:
            files = args.files.split(",")
        else:
            # Get all files
            for root, _, filenames in os.walk("."):
                for filename in filenames:
                    if filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                        files.append(os.path.join(root, filename))

        # Get domains
        domains = []
        if args.domains:
            domains = args.domains.split(",")
        else:
            # Get all enabled domains
            domains = [
                domain
                for domain, settings in config["domains"].items()
                if settings["enabled"]
            ]

        # Run sniffing
        results = {}
        for file in files:
            result = await loop.sniff_file(file, domains)
            results[file] = result

            # Generate report
            report_dir = Path(args.report_dir)
            report_dir.mkdir(parents=True, exist_ok=True)

            report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            with open(report_file, "w") as f:
                yaml.safe_dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "files": files,
                        "domains": domains,
                        "results": results
                    },
                    f
                )

        # Check results
        if any(
            result["status"] == "failed"
            for result in results.values()
        ):
            logger.error("Sniffing failed")
            sys.exit(1)

        logger.info("Sniffing completed successfully")

    except Exception as e:
        logger.error(f"Error running sniffing: {e}")
        sys.exit(1)

async def install_hooks(args: argparse.Namespace) -> None:
    """Install Git hooks command.

    Args:
        args: Command-line arguments
    """
    try:
        # Load configuration
        with open(args.config) as f:
            config = yaml.safe_load(f)

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "sniffing_cli"
        )

        # Create workflow
        workflow = GitWorkflow(config)

        # Install hooks
        await workflow.install_hooks()

        logger.info("Git hooks installed successfully")

    except Exception as e:
        logger.error(f"Error installing Git hooks: {e}")
        sys.exit(1)

async def fix_issues(args: argparse.Namespace) -> None:
    """Fix issues command.

    Args:
        args: Command-line arguments
    """
    try:
        # Load configuration
        with open(args.config) as f:
            config = yaml.safe_load(f)

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "sniffing_cli"
        )

        # Create sniffing loop
        loop = SniffingLoop(config)

        # Get files
        files = []
        if args.files:
            files = args.files.split(",")
        else:
            # Get all files
            for root, _, filenames in os.walk("."):
                for filename in filenames:
                    if filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                        files.append(os.path.join(root, filename))

        # Get domains
        domains = []
        if args.domains:
            domains = args.domains.split(",")
        else:
            # Get all enabled domains
            domains = [
                domain
                for domain, settings in config["domains"].items()
                if settings["enabled"]
            ]

        # Run sniffing
        results = {}
        for file in files:
            result = await loop.sniff_file(file, domains)
            results[file] = result

        # Fix issues
        fixes = {}
        for file, result in results.items():
            if result["status"] == "failed":
                fixes[file] = await loop.fix_issues(
                    file,
                    result["issues"]
                )

        # Generate report
        report_dir = Path("reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = report_dir / f"fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        with open(report_file, "w") as f:
            yaml.safe_dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "files": files,
                    "domains": domains,
                    "fixes": fixes
                },
                f
            )

        # Check fixes
        if any(
            fix["status"] == "failed"
            for fix in fixes.values()
        ):
            logger.error("Fix failed")
            sys.exit(1)

        logger.info("Fix completed successfully")

    except Exception as e:
        logger.error(f"Error fixing issues: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_args()

        # Run command
        if args.command == "sniff":
            asyncio.run(run_sniffing(args))
        elif args.command == "install":
            asyncio.run(install_hooks(args))
        elif args.command == "fix":
            asyncio.run(fix_issues(args))
        else:
            logger.error("Invalid command")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error running command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

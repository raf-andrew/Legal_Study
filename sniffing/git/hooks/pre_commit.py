"""
Pre-commit hook implementation for sniffing validation.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from ...core.utils.result import SniffingResult
from ...mcp.server.mcp_server import MCPServer

logger = logging.getLogger("pre_commit")

async def validate_files(files: List[str]) -> bool:
    """Validate files using sniffing.

    Args:
        files: List of files to validate

    Returns:
        True if validation passed, False otherwise
    """
    try:
        # Load config
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error("Config file not found")
            return False

        # Create MCP server
        server = MCPServer(str(config_path))

        # Run sniffing
        result = await server.sniff({
            "files": files,
            "fix": True,
            "priority": 1
        })

        # Check result
        if not result.get("status") == "completed":
            logger.error("Sniffing failed")
            return False

        # Check for critical issues
        results = result.get("results", {})
        for file_result in results.values():
            for domain_result in file_result.values():
                if domain_result.get("has_critical_issues", False):
                    logger.error(f"Critical issues found in {file_result}")
                    return False

        return True

    except Exception as e:
        logger.error(f"Error validating files: {e}")
        return False

def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Parse arguments
        parser = argparse.ArgumentParser(description="Pre-commit sniffing validation")
        parser.add_argument(
            "--files",
            type=str,
            required=True,
            help="Space-separated list of files to validate"
        )
        args = parser.parse_args()

        # Get files
        files = args.files.split()
        if not files:
            logger.info("No files to validate")
            return 0

        # Run validation
        success = asyncio.run(validate_files(files))
        return 0 if success else 1

    except Exception as e:
        logger.error(f"Error in pre-commit hook: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

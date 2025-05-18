"""
Pre-push hook implementation for sniffing validation.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from ...core.utils.result import SniffingResult
from ...mcp.server.mcp_server import MCPServer

logger = logging.getLogger("pre_push")

async def validate_branch(branch: str, files: List[str]) -> bool:
    """Validate branch using sniffing.

    Args:
        branch: Branch name
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

        # Get branch protection rules
        protection = server.config["git"]["branch_protection"]
        if not protection.get("enabled", True):
            logger.info("Branch protection disabled")
            return True

        # Check if branch requires protection
        required_checks = protection.get("required_checks", [])
        if not required_checks:
            logger.info("No required checks for branch")
            return True

        # Run sniffing with required checks
        result = await server.sniff({
            "files": files,
            "domains": required_checks,
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

        # Check required approvals
        required_approvals = protection.get("required_approvals", 0)
        if required_approvals > 0:
            approvals = await server.get_branch_approvals(branch)
            if approvals < required_approvals:
                logger.error(
                    f"Branch requires {required_approvals} approvals, "
                    f"but only has {approvals}"
                )
                return False

        return True

    except Exception as e:
        logger.error(f"Error validating branch: {e}")
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
        parser = argparse.ArgumentParser(description="Pre-push sniffing validation")
        parser.add_argument(
            "--branch",
            type=str,
            required=True,
            help="Branch name"
        )
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
        success = asyncio.run(validate_branch(args.branch, files))
        return 0 if success else 1

    except Exception as e:
        logger.error(f"Error in pre-push hook: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

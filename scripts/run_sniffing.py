"""
Script to run sniffing infrastructure.
"""
import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("run_sniffing")

async def run_sniffing(
    files: Optional[List[str]] = None,
    domains: Optional[List[str]] = None,
    fix: bool = True,
    watch: bool = False
) -> None:
    """Run sniffing infrastructure.

    Args:
        files: Optional list of files to sniff
        domains: Optional list of domains to sniff
        fix: Whether to fix issues
        watch: Whether to watch for changes
    """
    try:
        # Load config
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error("Config file not found")
            return

        # Create MCP server
        server = MCPServer(str(config_path))

        # Start server
        server_task = asyncio.create_task(server.start())

        try:
            # Run initial sniffing
            result = await server.sniff({
                "files": files,
                "domains": domains,
                "fix": fix,
                "priority": 1
            })

            # Check result
            if result.get("status") != "completed":
                logger.error("Initial sniffing failed")
                return

            # Watch for changes if requested
            if watch:
                while True:
                    # Wait for file changes
                    changes = await server.wait_for_changes()

                    # Run sniffing on changed files
                    result = await server.sniff({
                        "files": changes,
                        "domains": domains,
                        "fix": fix,
                        "priority": 1
                    })

                    # Check result
                    if result.get("status") != "completed":
                        logger.error("Change sniffing failed")

        finally:
            # Stop server
            await server.shutdown()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Error running sniffing: {e}")

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Parse arguments
        parser = argparse.ArgumentParser(description="Run sniffing infrastructure")
        parser.add_argument(
            "--files",
            type=str,
            help="Comma-separated list of files to sniff"
        )
        parser.add_argument(
            "--domains",
            type=str,
            help="Comma-separated list of domains to sniff"
        )
        parser.add_argument(
            "--no-fix",
            action="store_true",
            help="Don't fix issues"
        )
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Watch for changes"
        )
        args = parser.parse_args()

        # Get files and domains
        files = args.files.split(",") if args.files else None
        domains = args.domains.split(",") if args.domains else None

        # Run sniffing
        asyncio.run(run_sniffing(
            files=files,
            domains=domains,
            fix=not args.no_fix,
            watch=args.watch
        ))

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()

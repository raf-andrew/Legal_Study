"""
Script to run initial sniffing and fix issues.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional, Set

from sniffing.mcp.server.mcp_server import MCPServer

logger = logging.getLogger("initial_sniffing")

async def get_all_files() -> List[str]:
    """Get all files in workspace.

    Returns:
        List of file paths
    """
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

    return files

async def run_initial_sniffing() -> None:
    """Run initial sniffing and fix issues."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

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
            # Get all files
            files = await get_all_files()
            logger.info(f"Found {len(files)} files to sniff")

            # Run sniffing in batches
            batch_size = server.config["mcp"]["orchestration"]["batch_size"]
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} files)")

                # Run sniffing
                result = await server.sniff({
                    "files": batch,
                    "fix": True,
                    "priority": 1
                })

                # Check result
                if result.get("status") != "completed":
                    logger.error(f"Batch {i//batch_size + 1} failed")
                    continue

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

            logger.info("Initial sniffing completed")

        finally:
            # Stop server
            await server.shutdown()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(f"Error running initial sniffing: {e}")

def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_initial_sniffing())

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()

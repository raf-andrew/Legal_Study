"""
Script to start the MCP server.
"""
import asyncio
import logging
from pathlib import Path

from sniffing.mcp.server import Server
from sniffing.mcp.server.config import ServerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("server_script")

async def main():
    """Start the MCP server."""
    try:
        # Get config path
        config_path = Path("mcp/config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load config
        config = ServerConfig(str(config_path))

        # Create server
        server = Server(config)

        # Start server
        await server.start()

        # Keep server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop()
        logger.info("Server stopped")

    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

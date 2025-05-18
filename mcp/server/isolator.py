"""
MCP file isolator for test isolation.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import MCPConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("mcp_isolator")

class MCPIsolator:
    """Isolator for test isolation."""

    def __init__(self, config: MCPConfig):
        """Initialize isolator.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.active_isolations: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for isolator."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                "mcp_isolator"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the isolator."""
        try:
            logger.info("Starting MCP isolator...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info("MCP isolator started successfully")

        except Exception as e:
            logger.error(f"Error starting isolator: {e}")
            raise

    async def stop(self) -> None:
        """Stop the isolator."""
        try:
            logger.info("Stopping MCP isolator...")
            await self._cleanup()
            self.active_isolations.clear()
            self.metrics.clear()
            logger.info("MCP isolator stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping isolator: {e}")
            raise

    async def isolate_files(
        self,
        files: List[str],
        domains: List[str]
    ) -> str:
        """Isolate files for testing.

        Args:
            files: Files to isolate
            domains: Domains to use

        Returns:
            Isolation identifier
        """
        try:
            # Create isolation
            isolation_id = f"isolation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_isolations.add(isolation_id)

            try:
                # Create isolation directory
                isolation_dir = await self._create_isolation_dir(isolation_id)

                # Copy files
                await self._copy_files(files, isolation_dir)

                # Create domain configs
                await self._create_domain_configs(domains, isolation_dir)

                # Create metadata
                await self._create_metadata(
                    isolation_id,
                    files,
                    domains,
                    isolation_dir
                )

                logger.info(f"Created isolation: {isolation_id}")
                return isolation_id

            except Exception as e:
                await self._cleanup_isolation(isolation_id)
                raise

            finally:
                self.active_isolations.remove(isolation_id)

        except Exception as e:
            logger.error(f"Error isolating files: {e}")
            raise

    async def get_isolation_path(self, isolation_id: str) -> Optional[str]:
        """Get isolation directory path.

        Args:
            isolation_id: Isolation identifier

        Returns:
            Isolation directory path or None
        """
        try:
            isolation_dir = Path(self.config.isolation_path) / isolation_id
            return str(isolation_dir) if isolation_dir.exists() else None

        except Exception as e:
            logger.error(f"Error getting isolation path: {e}")
            return None

    async def cleanup_isolation(self, isolation_id: str) -> bool:
        """Clean up isolation.

        Args:
            isolation_id: Isolation identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            return await self._cleanup_isolation(isolation_id)

        except Exception as e:
            logger.error(f"Error cleaning up isolation: {e}")
            return False

    async def _initialize(self) -> None:
        """Initialize isolator resources."""
        try:
            # Create isolation directory
            isolation_dir = Path(self.config.isolation_path)
            isolation_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error initializing isolator: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up isolator resources."""
        try:
            # Clean up active isolations
            for isolation_id in list(self.active_isolations):
                await self._cleanup_isolation(isolation_id)

        except Exception as e:
            logger.error(f"Error cleaning up isolator: {e}")
            raise

    async def _create_isolation_dir(self, isolation_id: str) -> Path:
        """Create isolation directory.

        Args:
            isolation_id: Isolation identifier

        Returns:
            Isolation directory path
        """
        try:
            # Create directory
            isolation_dir = Path(self.config.isolation_path) / isolation_id
            isolation_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (isolation_dir / "files").mkdir(exist_ok=True)
            (isolation_dir / "configs").mkdir(exist_ok=True)
            (isolation_dir / "results").mkdir(exist_ok=True)

            return isolation_dir

        except Exception as e:
            logger.error(f"Error creating isolation directory: {e}")
            raise

    async def _copy_files(self, files: List[str], isolation_dir: Path) -> None:
        """Copy files to isolation directory.

        Args:
            files: Files to copy
            isolation_dir: Isolation directory path
        """
        try:
            import shutil
            files_dir = isolation_dir / "files"

            for file in files:
                src = Path(file)
                dst = files_dir / src.name

                # Create parent directories
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(src, dst)

        except Exception as e:
            logger.error(f"Error copying files: {e}")
            raise

    async def _create_domain_configs(
        self,
        domains: List[str],
        isolation_dir: Path
    ) -> None:
        """Create domain configurations.

        Args:
            domains: Domains to configure
            isolation_dir: Isolation directory path
        """
        try:
            configs_dir = isolation_dir / "configs"

            for domain in domains:
                # Get domain config
                domain_config = self.config.get_domain_config(domain)

                # Update paths
                domain_config["workspace_path"] = str(isolation_dir / "files")
                domain_config["report_path"] = str(isolation_dir / "results" / domain)

                # Save config
                config_file = configs_dir / f"{domain}.yaml"
                import yaml
                with open(config_file, "w") as f:
                    yaml.safe_dump(domain_config, f)

        except Exception as e:
            logger.error(f"Error creating domain configs: {e}")
            raise

    async def _create_metadata(
        self,
        isolation_id: str,
        files: List[str],
        domains: List[str],
        isolation_dir: Path
    ) -> None:
        """Create isolation metadata.

        Args:
            isolation_id: Isolation identifier
            files: Isolated files
            domains: Configured domains
            isolation_dir: Isolation directory path
        """
        try:
            metadata = {
                "id": isolation_id,
                "timestamp": datetime.now(),
                "files": files,
                "domains": domains,
                "path": str(isolation_dir)
            }

            # Save metadata
            metadata_file = isolation_dir / "metadata.json"
            import json
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            raise

    async def _cleanup_isolation(self, isolation_id: str) -> bool:
        """Clean up isolation.

        Args:
            isolation_id: Isolation identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            # Get isolation directory
            isolation_dir = Path(self.config.isolation_path) / isolation_id
            if not isolation_dir.exists():
                return False

            # Remove directory
            import shutil
            shutil.rmtree(isolation_dir)

            logger.info(f"Cleaned up isolation: {isolation_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up isolation: {e}")
            return False

    async def _start_metrics_collection(self) -> None:
        """Start collecting metrics."""
        try:
            while True:
                # Update metrics
                self.metrics = {
                    "active_isolations": len(self.active_isolations),
                    "total_isolations": len(list(Path(self.config.isolation_path).iterdir())),
                    "timestamp": datetime.now()
                }

                # Wait for next collection
                await asyncio.sleep(
                    self.config.monitoring_config["collection_interval"]
                )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            if not self.active_isolations:
                # Restart metrics collection
                asyncio.create_task(self._start_metrics_collection())

    async def get_health(self) -> Dict[str, Any]:
        """Get isolator health.

        Returns:
            Health status dictionary
        """
        try:
            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Calculate overall health
            healthy = all([
                metrics_health == "healthy",
                not self.active_isolations  # No stuck isolations
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "metrics": metrics_health,
                    "active_isolations": len(self.active_isolations)
                },
                "metrics": self.metrics
            }

        except Exception as e:
            logger.error(f"Error getting health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get isolator metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "component": "isolator",
                    "version": "1.0.0"
                },
                "help": {
                    "active_isolations": "Number of active isolations",
                    "total_isolations": "Total number of isolations"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

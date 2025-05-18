"""
Script to clean up sniffing infrastructure.
"""
import argparse
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("cleanup")

class Cleaner:
    """Class for cleaning up sniffing infrastructure."""

    def __init__(self):
        """Initialize cleaner."""
        self.root_dir = Path.cwd()
        self.monitoring_dir = self.root_dir / "monitoring"
        self.reports_dir = self.root_dir / "reports"
        self.git_hooks_dir = self.root_dir / ".git" / "hooks"

    def cleanup(
        self,
        components: Optional[List[str]] = None,
        force: bool = False
    ) -> None:
        """Clean up infrastructure.

        Args:
            components: Optional list of components to clean
            force: Whether to force cleanup
        """
        try:
            # Get components
            all_components = [
                "monitoring",
                "reports",
                "hooks",
                "cache"
            ]
            components = components or all_components

            # Clean components
            for component in components:
                if component == "monitoring":
                    self._cleanup_monitoring(force)
                elif component == "reports":
                    self._cleanup_reports(force)
                elif component == "hooks":
                    self._cleanup_hooks(force)
                elif component == "cache":
                    self._cleanup_cache(force)
                else:
                    logger.warning(f"Unknown component: {component}")

            logger.info("Cleanup completed")

        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            raise

    def _cleanup_monitoring(self, force: bool) -> None:
        """Clean up monitoring.

        Args:
            force: Whether to force cleanup
        """
        try:
            logger.info("Cleaning up monitoring...")

            # Stop monitoring services
            if self.monitoring_dir.exists():
                result = subprocess.run(
                    ["docker-compose", "down"],
                    cwd=self.monitoring_dir
                )
                if result.returncode != 0 and not force:
                    raise Exception("Failed to stop monitoring services")

            # Remove monitoring directory
            if self.monitoring_dir.exists():
                shutil.rmtree(self.monitoring_dir)

            logger.info("Monitoring cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up monitoring: {e}")
            if not force:
                raise

    def _cleanup_reports(self, force: bool) -> None:
        """Clean up reports.

        Args:
            force: Whether to force cleanup
        """
        try:
            logger.info("Cleaning up reports...")

            # Remove reports directory
            if self.reports_dir.exists():
                shutil.rmtree(self.reports_dir)

            logger.info("Reports cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up reports: {e}")
            if not force:
                raise

    def _cleanup_hooks(self, force: bool) -> None:
        """Clean up Git hooks.

        Args:
            force: Whether to force cleanup
        """
        try:
            logger.info("Cleaning up Git hooks...")

            # Remove hooks
            hooks = ["pre-commit", "pre-push"]
            for hook in hooks:
                hook_file = self.git_hooks_dir / hook
                if hook_file.exists():
                    hook_file.unlink()

            logger.info("Git hooks cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up Git hooks: {e}")
            if not force:
                raise

    def _cleanup_cache(self, force: bool) -> None:
        """Clean up cache.

        Args:
            force: Whether to force cleanup
        """
        try:
            logger.info("Cleaning up cache...")

            # Remove cache directories
            cache_dirs = [
                "__pycache__",
                ".pytest_cache",
                ".coverage",
                ".mypy_cache"
            ]
            for cache_dir in cache_dirs:
                for path in self.root_dir.rglob(cache_dir):
                    if path.is_dir():
                        shutil.rmtree(path)

            logger.info("Cache cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            if not force:
                raise

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Clean up sniffing infrastructure"
        )
        parser.add_argument(
            "--components",
            type=str,
            help="Comma-separated list of components to clean"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force cleanup"
        )
        args = parser.parse_args()

        # Get components
        components = args.components.split(",") if args.components else None

        # Run cleanup
        cleaner = Cleaner()
        cleaner.cleanup(components=components, force=args.force)

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()

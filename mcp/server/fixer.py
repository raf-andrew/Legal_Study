"""
MCP fixer for automated fixes.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import MCPConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("mcp_fixer")

class MCPFixer:
    """Fixer for automated fixes."""

    def __init__(self, config: MCPConfig):
        """Initialize fixer.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.active_fixes: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for fixer."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                "mcp_fixer"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the fixer."""
        try:
            logger.info("Starting MCP fixer...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info("MCP fixer started successfully")

        except Exception as e:
            logger.error(f"Error starting fixer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the fixer."""
        try:
            logger.info("Stopping MCP fixer...")
            await self._cleanup()
            self.active_fixes.clear()
            self.metrics.clear()
            logger.info("MCP fixer stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping fixer: {e}")
            raise

    async def generate_fixes(
        self,
        analysis_id: str,
        domains: List[str]
    ) -> str:
        """Generate fixes from analysis.

        Args:
            analysis_id: Analysis identifier
            domains: Domains to fix

        Returns:
            Fix identifier
        """
        try:
            # Create fix
            fix_id = f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_fixes.add(fix_id)

            try:
                # Create fix directory
                fix_dir = await self._create_fix_dir(fix_id)

                # Load analysis results
                analysis = await self._load_analysis_results(analysis_id)

                # Generate fixes
                fixes = await self._generate_fixes(
                    analysis,
                    domains,
                    fix_dir
                )

                # Create metadata
                await self._create_metadata(
                    fix_id,
                    analysis_id,
                    domains,
                    fix_dir
                )

                logger.info(f"Created fixes: {fix_id}")
                return fix_id

            except Exception as e:
                await self._cleanup_fixes(fix_id)
                raise

            finally:
                self.active_fixes.remove(fix_id)

        except Exception as e:
            logger.error(f"Error generating fixes: {e}")
            raise

    async def apply_fixes(
        self,
        fix_id: str,
        domains: List[str]
    ) -> bool:
        """Apply generated fixes.

        Args:
            fix_id: Fix identifier
            domains: Domains to apply

        Returns:
            Whether fixes were applied successfully
        """
        try:
            # Get fix directory
            fix_dir = Path(self.config.fix_path) / fix_id
            if not fix_dir.exists():
                raise ValueError(f"Fix not found: {fix_id}")

            # Load fixes
            fixes = await self._load_fixes(fix_id)

            # Apply fixes
            success = await self._apply_fixes(fixes, domains)

            return success

        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False

    async def get_fix_path(self, fix_id: str) -> Optional[str]:
        """Get fix directory path.

        Args:
            fix_id: Fix identifier

        Returns:
            Fix directory path or None
        """
        try:
            fix_dir = Path(self.config.fix_path) / fix_id
            return str(fix_dir) if fix_dir.exists() else None

        except Exception as e:
            logger.error(f"Error getting fix path: {e}")
            return None

    async def cleanup_fixes(self, fix_id: str) -> bool:
        """Clean up fixes.

        Args:
            fix_id: Fix identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            return await self._cleanup_fixes(fix_id)

        except Exception as e:
            logger.error(f"Error cleaning up fixes: {e}")
            return False

    async def _initialize(self) -> None:
        """Initialize fixer resources."""
        try:
            # Create fix directory
            fix_dir = Path(self.config.fix_path)
            fix_dir.mkdir(parents=True, exist_ok=True)

            # Initialize AI model
            await self._init_model()

        except Exception as e:
            logger.error(f"Error initializing fixer: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up fixer resources."""
        try:
            # Clean up active fixes
            for fix_id in list(self.active_fixes):
                await self._cleanup_fixes(fix_id)

            # Clean up model
            await self._cleanup_model()

        except Exception as e:
            logger.error(f"Error cleaning up fixer: {e}")
            raise

    async def _create_fix_dir(self, fix_id: str) -> Path:
        """Create fix directory.

        Args:
            fix_id: Fix identifier

        Returns:
            Fix directory path
        """
        try:
            # Create directory
            fix_dir = Path(self.config.fix_path) / fix_id
            fix_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (fix_dir / "fixes").mkdir(exist_ok=True)
            (fix_dir / "backups").mkdir(exist_ok=True)

            return fix_dir

        except Exception as e:
            logger.error(f"Error creating fix directory: {e}")
            raise

    async def _load_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Load analysis results.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Analysis results
        """
        try:
            # Get analysis directory
            analysis_dir = Path(self.config.analysis_path) / analysis_id
            if not analysis_dir.exists():
                raise ValueError(f"Analysis not found: {analysis_id}")

            # Load analysis
            analysis_file = analysis_dir / "analysis.json"
            if not analysis_file.exists():
                raise ValueError(f"Analysis file not found: {analysis_id}")

            # Load results
            import json
            with open(analysis_file) as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading analysis results: {e}")
            raise

    async def _generate_fixes(
        self,
        analysis: Dict[str, Any],
        domains: List[str],
        fix_dir: Path
    ) -> Dict[str, Any]:
        """Generate fixes.

        Args:
            analysis: Analysis results
            domains: Domains to fix
            fix_dir: Fix directory path

        Returns:
            Generated fixes
        """
        try:
            fixes = {
                "status": "running",
                "timestamp": datetime.now(),
                "domains": {}
            }

            # Generate fixes for each domain
            for domain in domains:
                domain_analysis = analysis.get("domains", {}).get(domain, {})
                if domain_analysis:
                    domain_fixes = await self._generate_domain_fixes(
                        domain,
                        domain_analysis,
                        fix_dir
                    )
                    fixes["domains"][domain] = domain_fixes

            # Update status
            fixes["status"] = "completed"

            # Save fixes
            await self._save_fixes(fixes, fix_dir)

            return fixes

        except Exception as e:
            logger.error(f"Error generating fixes: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _generate_domain_fixes(
        self,
        domain: str,
        analysis: Dict[str, Any],
        fix_dir: Path
    ) -> Dict[str, Any]:
        """Generate domain fixes.

        Args:
            domain: Domain name
            analysis: Domain analysis
            fix_dir: Fix directory path

        Returns:
            Domain fixes
        """
        try:
            # Import domain fixer
            from sniffing.core.domains import get_fixer
            fixer = get_fixer(domain, self.config)

            # Generate fixes
            fixes = await fixer.generate_fixes(analysis)

            # Save domain fixes
            domain_dir = fix_dir / "fixes" / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            fixes_file = domain_dir / "fixes.json"
            import json
            with open(fixes_file, "w") as f:
                json.dump(fixes, f, indent=2, default=str)

            return fixes

        except Exception as e:
            logger.error(f"Error generating domain fixes: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _save_fixes(
        self,
        fixes: Dict[str, Any],
        fix_dir: Path
    ) -> None:
        """Save fixes.

        Args:
            fixes: Generated fixes
            fix_dir: Fix directory path
        """
        try:
            # Save fixes
            fixes_file = fix_dir / "fixes.json"
            import json
            with open(fixes_file, "w") as f:
                json.dump(fixes, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving fixes: {e}")
            raise

    async def _load_fixes(self, fix_id: str) -> Dict[str, Any]:
        """Load fixes.

        Args:
            fix_id: Fix identifier

        Returns:
            Loaded fixes
        """
        try:
            # Get fix directory
            fix_dir = Path(self.config.fix_path) / fix_id
            if not fix_dir.exists():
                raise ValueError(f"Fix not found: {fix_id}")

            # Load fixes
            fixes_file = fix_dir / "fixes.json"
            if not fixes_file.exists():
                raise ValueError(f"Fixes file not found: {fix_id}")

            # Load results
            import json
            with open(fixes_file) as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading fixes: {e}")
            raise

    async def _apply_fixes(
        self,
        fixes: Dict[str, Any],
        domains: List[str]
    ) -> bool:
        """Apply fixes.

        Args:
            fixes: Fixes to apply
            domains: Domains to apply

        Returns:
            Whether fixes were applied successfully
        """
        try:
            success = True

            # Apply fixes for each domain
            for domain in domains:
                domain_fixes = fixes.get("domains", {}).get(domain, {})
                if domain_fixes:
                    domain_success = await self._apply_domain_fixes(
                        domain,
                        domain_fixes
                    )
                    success = success and domain_success

            return success

        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False

    async def _apply_domain_fixes(
        self,
        domain: str,
        fixes: Dict[str, Any]
    ) -> bool:
        """Apply domain fixes.

        Args:
            domain: Domain name
            fixes: Domain fixes

        Returns:
            Whether fixes were applied successfully
        """
        try:
            # Import domain fixer
            from sniffing.core.domains import get_fixer
            fixer = get_fixer(domain, self.config)

            # Apply fixes
            return await fixer.apply_fixes(fixes)

        except Exception as e:
            logger.error(f"Error applying domain fixes: {e}")
            return False

    async def _create_metadata(
        self,
        fix_id: str,
        analysis_id: str,
        domains: List[str],
        fix_dir: Path
    ) -> None:
        """Create fix metadata.

        Args:
            fix_id: Fix identifier
            analysis_id: Analysis identifier
            domains: Fixed domains
            fix_dir: Fix directory path
        """
        try:
            metadata = {
                "id": fix_id,
                "analysis_id": analysis_id,
                "timestamp": datetime.now(),
                "domains": domains,
                "path": str(fix_dir)
            }

            # Save metadata
            metadata_file = fix_dir / "metadata.json"
            import json
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            raise

    async def _cleanup_fixes(self, fix_id: str) -> bool:
        """Clean up fixes.

        Args:
            fix_id: Fix identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            # Get fix directory
            fix_dir = Path(self.config.fix_path) / fix_id
            if not fix_dir.exists():
                return False

            # Remove directory
            import shutil
            shutil.rmtree(fix_dir)

            logger.info(f"Cleaned up fixes: {fix_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up fixes: {e}")
            return False

    async def _init_model(self) -> None:
        """Initialize AI model."""
        try:
            # Import here to avoid circular imports
            from transformers import AutoModel, AutoTokenizer

            # Load model and tokenizer
            model_name = self.config.model_config.get(
                "name",
                "microsoft/codebert-base"
            )
            self.model = AutoModel.from_pretrained(model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    async def _cleanup_model(self) -> None:
        """Clean up AI model."""
        try:
            if hasattr(self, "model"):
                del self.model
            if hasattr(self, "tokenizer"):
                del self.tokenizer

        except Exception as e:
            logger.error(f"Error cleaning up model: {e}")
            raise

    async def _start_metrics_collection(self) -> None:
        """Start collecting metrics."""
        try:
            while True:
                # Update metrics
                self.metrics = {
                    "active_fixes": len(self.active_fixes),
                    "total_fixes": len(list(Path(self.config.fix_path).iterdir())),
                    "timestamp": datetime.now()
                }

                # Wait for next collection
                await asyncio.sleep(
                    self.config.monitoring_config["collection_interval"]
                )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            if not self.active_fixes:
                # Restart metrics collection
                asyncio.create_task(self._start_metrics_collection())

    async def get_health(self) -> Dict[str, Any]:
        """Get fixer health.

        Returns:
            Health status dictionary
        """
        try:
            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Check model
            model_health = "healthy" if hasattr(self, "model") else "not_initialized"

            # Calculate overall health
            healthy = all([
                metrics_health == "healthy",
                model_health == "healthy",
                not self.active_fixes  # No stuck fixes
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "metrics": metrics_health,
                    "model": model_health,
                    "active_fixes": len(self.active_fixes)
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
        """Get fixer metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "component": "fixer",
                    "version": "1.0.0"
                },
                "help": {
                    "active_fixes": "Number of active fixes",
                    "total_fixes": "Total number of fixes"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

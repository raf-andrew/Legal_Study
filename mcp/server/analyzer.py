"""
MCP analyzer for result analysis.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import MCPConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("mcp_analyzer")

class MCPAnalyzer:
    """Analyzer for result analysis."""

    def __init__(self, config: MCPConfig):
        """Initialize analyzer.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.active_analyses: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for analyzer."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                "mcp_analyzer"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the analyzer."""
        try:
            logger.info("Starting MCP analyzer...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info("MCP analyzer started successfully")

        except Exception as e:
            logger.error(f"Error starting analyzer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the analyzer."""
        try:
            logger.info("Stopping MCP analyzer...")
            await self._cleanup()
            self.active_analyses.clear()
            self.metrics.clear()
            logger.info("MCP analyzer stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping analyzer: {e}")
            raise

    async def analyze_results(
        self,
        job_id: str,
        domains: List[str]
    ) -> str:
        """Analyze job results.

        Args:
            job_id: Job identifier
            domains: Domains to analyze

        Returns:
            Analysis identifier
        """
        try:
            # Create analysis
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_analyses.add(analysis_id)

            try:
                # Create analysis directory
                analysis_dir = await self._create_analysis_dir(analysis_id)

                # Load job results
                results = await self._load_job_results(job_id)

                # Analyze results
                analysis = await self._analyze_results(
                    results,
                    domains,
                    analysis_dir
                )

                # Create metadata
                await self._create_metadata(
                    analysis_id,
                    job_id,
                    domains,
                    analysis_dir
                )

                logger.info(f"Created analysis: {analysis_id}")
                return analysis_id

            except Exception as e:
                await self._cleanup_analysis(analysis_id)
                raise

            finally:
                self.active_analyses.remove(analysis_id)

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            raise

    async def get_analysis_path(self, analysis_id: str) -> Optional[str]:
        """Get analysis directory path.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Analysis directory path or None
        """
        try:
            analysis_dir = Path(self.config.analysis_path) / analysis_id
            return str(analysis_dir) if analysis_dir.exists() else None

        except Exception as e:
            logger.error(f"Error getting analysis path: {e}")
            return None

    async def cleanup_analysis(self, analysis_id: str) -> bool:
        """Clean up analysis.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            return await self._cleanup_analysis(analysis_id)

        except Exception as e:
            logger.error(f"Error cleaning up analysis: {e}")
            return False

    async def _initialize(self) -> None:
        """Initialize analyzer resources."""
        try:
            # Create analysis directory
            analysis_dir = Path(self.config.analysis_path)
            analysis_dir.mkdir(parents=True, exist_ok=True)

            # Initialize AI model
            await self._init_model()

        except Exception as e:
            logger.error(f"Error initializing analyzer: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up analyzer resources."""
        try:
            # Clean up active analyses
            for analysis_id in list(self.active_analyses):
                await self._cleanup_analysis(analysis_id)

            # Clean up model
            await self._cleanup_model()

        except Exception as e:
            logger.error(f"Error cleaning up analyzer: {e}")
            raise

    async def _create_analysis_dir(self, analysis_id: str) -> Path:
        """Create analysis directory.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Analysis directory path
        """
        try:
            # Create directory
            analysis_dir = Path(self.config.analysis_path) / analysis_id
            analysis_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (analysis_dir / "results").mkdir(exist_ok=True)
            (analysis_dir / "reports").mkdir(exist_ok=True)

            return analysis_dir

        except Exception as e:
            logger.error(f"Error creating analysis directory: {e}")
            raise

    async def _load_job_results(self, job_id: str) -> Dict[str, Any]:
        """Load job results.

        Args:
            job_id: Job identifier

        Returns:
            Job results
        """
        try:
            # Get job directory
            job_dir = Path(self.config.job_path) / job_id
            if not job_dir.exists():
                raise ValueError(f"Job not found: {job_id}")

            # Load status
            status_file = job_dir / "status.json"
            if not status_file.exists():
                raise ValueError(f"Job status not found: {job_id}")

            # Load results
            import json
            with open(status_file) as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading job results: {e}")
            raise

    async def _analyze_results(
        self,
        results: Dict[str, Any],
        domains: List[str],
        analysis_dir: Path
    ) -> Dict[str, Any]:
        """Analyze results.

        Args:
            results: Results to analyze
            domains: Domains to analyze
            analysis_dir: Analysis directory path

        Returns:
            Analysis results
        """
        try:
            analysis = {
                "status": "running",
                "timestamp": datetime.now(),
                "domains": {}
            }

            # Analyze each domain
            for domain in domains:
                domain_results = results.get("domains", {}).get(domain, {})
                if domain_results:
                    domain_analysis = await self._analyze_domain_results(
                        domain,
                        domain_results,
                        analysis_dir
                    )
                    analysis["domains"][domain] = domain_analysis

            # Update status
            analysis["status"] = "completed"

            # Save analysis
            await self._save_analysis(analysis, analysis_dir)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _analyze_domain_results(
        self,
        domain: str,
        results: Dict[str, Any],
        analysis_dir: Path
    ) -> Dict[str, Any]:
        """Analyze domain results.

        Args:
            domain: Domain name
            results: Domain results
            analysis_dir: Analysis directory path

        Returns:
            Domain analysis
        """
        try:
            # Import domain analyzer
            from sniffing.core.domains import get_analyzer
            analyzer = get_analyzer(domain, self.config)

            # Run analysis
            analysis = await analyzer.analyze(results)

            # Save domain analysis
            domain_dir = analysis_dir / "results" / domain
            domain_dir.mkdir(parents=True, exist_ok=True)
            analysis_file = domain_dir / "analysis.json"
            import json
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing domain results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _save_analysis(
        self,
        analysis: Dict[str, Any],
        analysis_dir: Path
    ) -> None:
        """Save analysis results.

        Args:
            analysis: Analysis results
            analysis_dir: Analysis directory path
        """
        try:
            # Save analysis
            analysis_file = analysis_dir / "analysis.json"
            import json
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2, default=str)

            # Generate reports
            await self._generate_reports(analysis, analysis_dir)

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise

    async def _generate_reports(
        self,
        analysis: Dict[str, Any],
        analysis_dir: Path
    ) -> None:
        """Generate analysis reports.

        Args:
            analysis: Analysis results
            analysis_dir: Analysis directory path
        """
        try:
            reports_dir = analysis_dir / "reports"

            # Generate domain reports
            for domain, domain_analysis in analysis.get("domains", {}).items():
                # Import domain reporter
                from sniffing.core.domains import get_reporter
                reporter = get_reporter(domain, self.config)

                # Generate report
                report = await reporter.generate_report(domain_analysis)

                # Save report
                domain_dir = reports_dir / domain
                domain_dir.mkdir(parents=True, exist_ok=True)
                report_file = domain_dir / "report.json"
                import json
                with open(report_file, "w") as f:
                    json.dump(report, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            raise

    async def _create_metadata(
        self,
        analysis_id: str,
        job_id: str,
        domains: List[str],
        analysis_dir: Path
    ) -> None:
        """Create analysis metadata.

        Args:
            analysis_id: Analysis identifier
            job_id: Job identifier
            domains: Analyzed domains
            analysis_dir: Analysis directory path
        """
        try:
            metadata = {
                "id": analysis_id,
                "job_id": job_id,
                "timestamp": datetime.now(),
                "domains": domains,
                "path": str(analysis_dir)
            }

            # Save metadata
            metadata_file = analysis_dir / "metadata.json"
            import json
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            raise

    async def _cleanup_analysis(self, analysis_id: str) -> bool:
        """Clean up analysis.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Whether cleanup was successful
        """
        try:
            # Get analysis directory
            analysis_dir = Path(self.config.analysis_path) / analysis_id
            if not analysis_dir.exists():
                return False

            # Remove directory
            import shutil
            shutil.rmtree(analysis_dir)

            logger.info(f"Cleaned up analysis: {analysis_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up analysis: {e}")
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
                    "active_analyses": len(self.active_analyses),
                    "total_analyses": len(list(Path(self.config.analysis_path).iterdir())),
                    "timestamp": datetime.now()
                }

                # Wait for next collection
                await asyncio.sleep(
                    self.config.monitoring_config["collection_interval"]
                )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            if not self.active_analyses:
                # Restart metrics collection
                asyncio.create_task(self._start_metrics_collection())

    async def get_health(self) -> Dict[str, Any]:
        """Get analyzer health.

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
                not self.active_analyses  # No stuck analyses
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "metrics": metrics_health,
                    "model": model_health,
                    "active_analyses": len(self.active_analyses)
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
        """Get analyzer metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "component": "analyzer",
                    "version": "1.0.0"
                },
                "help": {
                    "active_analyses": "Number of active analyses",
                    "total_analyses": "Total number of analyses"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

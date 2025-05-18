"""
Base analyzer class providing core analysis functionality.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import SnifferConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("base_analyzer")

class BaseAnalyzer(ABC):
    """Base class for all analyzers."""

    def __init__(self, domain: str, config: SnifferConfig):
        """Initialize base analyzer.

        Args:
            domain: Domain name
            config: Analyzer configuration
        """
        self.domain = domain
        self.config = config
        self.active_jobs: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for analyzer."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                f"{self.domain}_analyzer"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the analyzer."""
        try:
            logger.info(f"Starting {self.domain} analyzer...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info(f"{self.domain} analyzer started successfully")

        except Exception as e:
            logger.error(f"Error starting {self.domain} analyzer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the analyzer."""
        try:
            logger.info(f"Stopping {self.domain} analyzer...")
            await self._cleanup()
            self.active_jobs.clear()
            self.metrics.clear()
            logger.info(f"{self.domain} analyzer stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} analyzer: {e}")
            raise

    async def analyze(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results.

        Args:
            results: Results to analyze

        Returns:
            Analysis results
        """
        try:
            logger.info(f"Analyzing {len(results)} results...")
            job_id = f"{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Run analysis
                start_time = datetime.now()
                analysis = await self._analyze_results(results)
                end_time = datetime.now()

                # Calculate metrics
                duration = (end_time - start_time).total_seconds()
                confidence = await self._calculate_confidence(analysis)

                # Add metrics
                analysis["metrics"] = {
                    "duration": duration,
                    "confidence": confidence,
                    "results": len(results),
                    "findings": len(analysis.get("findings", []))
                }

                # Generate report
                await self._generate_report(job_id, analysis)

                return analysis

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    @abstractmethod
    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run domain-specific analysis.

        Args:
            results: Results to analyze

        Returns:
            Analysis results
        """
        pass

    async def _initialize(self) -> None:
        """Initialize analyzer resources."""
        try:
            # Create report directory
            report_dir = Path(self.config.report_path) / self.domain / "analysis"
            report_dir.mkdir(parents=True, exist_ok=True)

            # Initialize AI model
            await self._init_model()

        except Exception as e:
            logger.error(f"Error initializing analyzer: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up analyzer resources."""
        try:
            # Clean up model
            await self._cleanup_model()

        except Exception as e:
            logger.error(f"Error cleaning up analyzer: {e}")
            raise

    async def _init_model(self) -> None:
        """Initialize AI model."""
        try:
            # Import here to avoid circular imports
            from transformers import AutoModel, AutoTokenizer

            # Load model and tokenizer
            model_name = self.config.get_analyzer_config(self.domain).get(
                "model_name",
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

    async def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate analysis confidence.

        Args:
            analysis: Analysis results

        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Get findings
            findings = analysis.get("findings", [])
            if not findings:
                return 0.0

            # Calculate average confidence
            confidences = [
                finding.get("confidence", 0.0)
                for finding in findings
            ]
            return sum(confidences) / len(confidences)

        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0

    async def _generate_report(
        self,
        job_id: str,
        analysis: Dict[str, Any]
    ) -> None:
        """Generate analysis report.

        Args:
            job_id: Job identifier
            analysis: Analysis results
        """
        try:
            # Get report path
            report_dir = Path(self.config.report_path) / self.domain / "analysis"
            report_path = report_dir / f"{job_id}.json"

            # Write report
            import json
            with open(report_path, "w") as f:
                json.dump(analysis, f, indent=2, default=str)

            logger.info(f"Generated report: {report_path}")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    async def get_health(self) -> Dict[str, Any]:
        """Get analyzer health.

        Returns:
            Health status dictionary
        """
        try:
            # Check model
            model_health = "healthy" if hasattr(self, "model") else "not_initialized"

            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Calculate overall health
            healthy = all([
                model_health == "healthy",
                metrics_health == "healthy",
                not self.active_jobs  # No stuck jobs
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "model": model_health,
                    "metrics": metrics_health,
                    "active_jobs": len(self.active_jobs)
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
                    "domain": self.domain,
                    "analyzer": self.__class__.__name__
                },
                "help": {
                    "active_jobs": "Number of active analysis jobs",
                    "total_jobs": "Total number of analysis jobs",
                    "success_rate": "Analysis success rate percentage",
                    "average_duration": "Average analysis duration in seconds",
                    "average_confidence": "Average analysis confidence score"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

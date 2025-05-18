"""
Base analyzer class for result analysis.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ...server.config import ServerConfig

logger = logging.getLogger("base_analyzer")

class BaseAnalyzer(ABC):
    """Base class for result analyzers."""

    def __init__(self, domain: str, config: ServerConfig):
        """Initialize base analyzer.

        Args:
            domain: Domain name
            config: Server configuration
        """
        self.domain = domain
        self.config = config
        self.analyzer_config = config.get_analyzer_config(domain)
        self.metrics = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for analyzer."""
        try:
            # Get logging config
            log_config = self.config.logging_config
            log_level = log_config.get("level", "INFO")
            log_format = log_config.get("format")

            # Configure logger
            logger.setLevel(log_level)
            if log_format:
                formatter = logging.Formatter(log_format)
                for handler in logger.handlers:
                    handler.setFormatter(formatter)

        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the analyzer."""
        try:
            logger.info(f"Starting {self.domain} analyzer...")

            # Initialize CodeBERT model
            await self._init_model()

            logger.info(f"{self.domain} analyzer started successfully")

        except Exception as e:
            logger.error(f"Error starting {self.domain} analyzer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the analyzer."""
        try:
            logger.info(f"Stopping {self.domain} analyzer...")

            # Clean up resources
            await self._cleanup()

            logger.info(f"{self.domain} analyzer stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} analyzer: {e}")
            raise

    async def analyze(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results.

        Args:
            results: Results to analyze

        Returns:
            Analysis results
        """
        try:
            logger.info(f"Analyzing {self.domain} results...")

            # Run analysis
            analysis = await self._analyze_results(results)

            # Update metrics
            self.metrics = {
                "last_analysis": datetime.now(),
                "total_analyses": self.metrics.get("total_analyses", 0) + 1,
                "average_duration": self._calculate_average_duration(analysis),
                "success_rate": self._calculate_success_rate()
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {self.domain} results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def generate_fixes(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fixes from analysis.

        Args:
            analysis: Analysis to generate fixes from

        Returns:
            Generated fixes
        """
        try:
            logger.info(f"Generating {self.domain} fixes...")

            # Generate fixes
            fixes = await self._generate_fixes(analysis)

            # Update metrics
            self.metrics["total_fixes"] = self.metrics.get("total_fixes", 0) + 1

            return fixes

        except Exception as e:
            logger.error(f"Error generating {self.domain} fixes: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    @abstractmethod
    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze domain-specific results.

        Args:
            results: Results to analyze

        Returns:
            Analysis results
        """
        pass

    @abstractmethod
    async def _generate_fixes(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate domain-specific fixes.

        Args:
            analysis: Analysis to generate fixes from

        Returns:
            Generated fixes
        """
        pass

    async def _init_model(self) -> None:
        """Initialize CodeBERT model."""
        try:
            # Import here to avoid circular imports
            from transformers import AutoModel, AutoTokenizer

            # Load model and tokenizer
            model_name = self.analyzer_config.get("model_name", "microsoft/codebert-base")
            self.model = AutoModel.from_pretrained(model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up analyzer resources."""
        try:
            # Clean up model
            if hasattr(self, "model"):
                del self.model
            if hasattr(self, "tokenizer"):
                del self.tokenizer

            # Clear metrics
            self.metrics.clear()

        except Exception as e:
            logger.error(f"Error cleaning up analyzer: {e}")
            raise

    def _calculate_average_duration(self, analysis: Dict[str, Any]) -> float:
        """Calculate average analysis duration.

        Args:
            analysis: Current analysis results

        Returns:
            Average duration in seconds
        """
        try:
            # Get duration history
            history = self.metrics.get("duration_history", [])
            if not history:
                return 0.0

            # Add current duration
            current_duration = (
                datetime.now() -
                analysis.get("timestamp", datetime.now())
            ).total_seconds()
            history.append(current_duration)

            # Calculate average
            return sum(history) / len(history)

        except Exception as e:
            logger.error(f"Error calculating average duration: {e}")
            return 0.0

    def _calculate_success_rate(self) -> float:
        """Calculate analysis success rate.

        Returns:
            Success rate percentage
        """
        try:
            # Get analysis history
            history = self.metrics.get("analysis_history", [])
            if not history:
                return 0.0

            # Calculate success rate
            successful = sum(1 for a in history if a.get("status") == "completed")
            return (successful / len(history) * 100)

        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.0

    async def get_health(self) -> Dict[str, Any]:
        """Get analyzer health.

        Returns:
            Health status dictionary
        """
        try:
            # Check model health
            model_health = "healthy" if hasattr(self, "model") else "not_initialized"

            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Calculate overall health
            healthy = all([
                model_health == "healthy",
                metrics_health == "healthy"
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "model": model_health,
                    "metrics": metrics_health
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
                    "total_analyses": "Total number of analyses run",
                    "total_fixes": "Total number of fixes generated",
                    "average_duration": "Average analysis duration in seconds",
                    "success_rate": "Analysis success rate percentage"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

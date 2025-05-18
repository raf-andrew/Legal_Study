"""
AI-powered analysis and fix suggestion for sniffing results.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger("ai_analyzer")

class AIAnalyzer:
    """AI-powered analyzer for sniffing results."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize AI analyzer.

        Args:
            config: Configuration dictionary for the analyzer
        """
        self.config = config
        self.model_name = config.get("model", "microsoft/codebert-base")
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
        self.batch_size = config.get("batch_size", 32)
        self.max_sequence_length = config.get("max_sequence_length", 512)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model and tokenizer
        self._load_model()
        self._setup_storage()

    def _load_model(self) -> None:
        """Load AI model and tokenizer."""
        try:
            logger.info(f"Loading model {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def _setup_storage(self) -> None:
        """Set up storage directories."""
        try:
            self.analysis_dir = Path("reports") / "analysis"
            self.analysis_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (self.analysis_dir / "results").mkdir(exist_ok=True)
            (self.analysis_dir / "fixes").mkdir(exist_ok=True)
            (self.analysis_dir / "patterns").mkdir(exist_ok=True)
            (self.analysis_dir / "models").mkdir(exist_ok=True)

        except Exception as e:
            logger.error(f"Error setting up storage: {e}")
            raise

    async def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sniffing results using AI.

        Args:
            results: List of sniffing results to analyze

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Extract relevant information
            issues = []
            patterns = []
            metrics = []
            for result in results:
                issues.extend(result.get("issues", []))
                patterns.extend(self._extract_patterns(result))
                metrics.append(result.get("metrics", {}))

            # Analyze issues
            issue_analysis = await self._analyze_issues(issues)

            # Analyze patterns
            pattern_analysis = await self._analyze_patterns(patterns)

            # Analyze metrics
            metric_analysis = self._analyze_metrics(metrics)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                issue_analysis,
                pattern_analysis,
                metric_analysis
            )

            # Compile analysis
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "issue_analysis": issue_analysis,
                "pattern_analysis": pattern_analysis,
                "metric_analysis": metric_analysis,
                "recommendations": recommendations
            }

            # Save analysis
            self._save_analysis(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_fix_suggestions(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get AI-generated fix suggestions for issues.

        Args:
            issues: List of issues to fix

        Returns:
            List of fix suggestions
        """
        try:
            suggestions = []
            for issue in issues:
                # Generate fix suggestion
                suggestion = await self._generate_fix(issue)

                # Add to suggestions if confidence is high enough
                if suggestion["confidence"] >= self.confidence_threshold:
                    suggestions.append(suggestion)

            # Save suggestions
            self._save_suggestions(suggestions)

            return suggestions

        except Exception as e:
            logger.error(f"Error generating fix suggestions: {e}")
            return []

    async def _analyze_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze issues using AI.

        Args:
            issues: List of issues to analyze

        Returns:
            Dictionary containing issue analysis
        """
        try:
            # Group issues by type
            issue_groups = {}
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                if issue_type not in issue_groups:
                    issue_groups[issue_type] = []
                issue_groups[issue_type].append(issue)

            # Analyze each group
            analysis = {}
            for issue_type, group in issue_groups.items():
                # Encode issues
                encodings = self._encode_issues(group)

                # Get model predictions
                with torch.no_grad():
                    outputs = self.model(**encodings)
                    embeddings = outputs.last_hidden_state[:, 0, :].cpu()

                # Analyze embeddings
                group_analysis = {
                    "count": len(group),
                    "severity_distribution": self._analyze_severity(group),
                    "patterns": self._find_patterns(embeddings, group),
                    "common_causes": self._find_common_causes(embeddings, group),
                    "impact": self._assess_impact(group)
                }
                analysis[issue_type] = group_analysis

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing issues: {e}")
            return {}

    async def _analyze_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze code patterns using AI.

        Args:
            patterns: List of code patterns to analyze

        Returns:
            Dictionary containing pattern analysis
        """
        try:
            # Encode patterns
            encodings = self._encode_patterns(patterns)

            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**encodings)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu()

            # Analyze embeddings
            analysis = {
                "clusters": self._cluster_patterns(embeddings, patterns),
                "anomalies": self._detect_anomalies(embeddings, patterns),
                "trends": self._analyze_trends(patterns),
                "recommendations": self._get_pattern_recommendations(embeddings, patterns)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {}

    def _analyze_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance and resource metrics.

        Args:
            metrics: List of metrics to analyze

        Returns:
            Dictionary containing metric analysis
        """
        try:
            analysis = {
                "performance": {
                    "response_times": self._analyze_response_times(metrics),
                    "throughput": self._analyze_throughput(metrics),
                    "error_rates": self._analyze_error_rates(metrics)
                },
                "resources": {
                    "cpu_usage": self._analyze_resource_usage(metrics, "cpu"),
                    "memory_usage": self._analyze_resource_usage(metrics, "memory"),
                    "disk_usage": self._analyze_resource_usage(metrics, "disk")
                },
                "trends": self._analyze_metric_trends(metrics),
                "anomalies": self._detect_metric_anomalies(metrics)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing metrics: {e}")
            return {}

    async def _generate_recommendations(
        self,
        issue_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any],
        metric_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis results.

        Args:
            issue_analysis: Issue analysis results
            pattern_analysis: Pattern analysis results
            metric_analysis: Metric analysis results

        Returns:
            List of recommendations
        """
        try:
            recommendations = []

            # Add issue-based recommendations
            recommendations.extend(self._get_issue_recommendations(issue_analysis))

            # Add pattern-based recommendations
            recommendations.extend(pattern_analysis.get("recommendations", []))

            # Add metric-based recommendations
            recommendations.extend(self._get_metric_recommendations(metric_analysis))

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    async def _generate_fix(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fix suggestion for an issue.

        Args:
            issue: Issue to generate fix for

        Returns:
            Dictionary containing fix suggestion
        """
        try:
            # Encode issue
            encodings = self._encode_issue(issue)

            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**encodings)
                embedding = outputs.last_hidden_state[:, 0, :].cpu()

            # Generate fix
            fix = {
                "issue_id": issue.get("id"),
                "issue_type": issue.get("type"),
                "confidence": float(torch.max(torch.softmax(embedding, dim=1))),
                "suggestion": self._generate_fix_code(embedding, issue),
                "description": self._generate_fix_description(embedding, issue),
                "steps": self._generate_fix_steps(embedding, issue)
            }

            return fix

        except Exception as e:
            logger.error(f"Error generating fix: {e}")
            return {
                "issue_id": issue.get("id"),
                "error": str(e),
                "confidence": 0.0
            }

    def _encode_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        """Encode issues for model input.

        Args:
            issues: List of issues to encode

        Returns:
            Dictionary of encoded tensors
        """
        try:
            texts = [
                f"{issue.get('type', '')} {issue.get('description', '')}"
                for issue in issues
            ]

            encodings = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_sequence_length,
                return_tensors="pt"
            )

            return {k: v.to(self.device) for k, v in encodings.items()}

        except Exception as e:
            logger.error(f"Error encoding issues: {e}")
            return {}

    def _encode_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
        """Encode code patterns for model input.

        Args:
            patterns: List of patterns to encode

        Returns:
            Dictionary of encoded tensors
        """
        try:
            texts = [
                pattern.get("code", "")
                for pattern in patterns
            ]

            encodings = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_sequence_length,
                return_tensors="pt"
            )

            return {k: v.to(self.device) for k, v in encodings.items()}

        except Exception as e:
            logger.error(f"Error encoding patterns: {e}")
            return {}

    def _encode_issue(self, issue: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """Encode single issue for model input.

        Args:
            issue: Issue to encode

        Returns:
            Dictionary of encoded tensors
        """
        try:
            text = f"{issue.get('type', '')} {issue.get('description', '')}"

            encodings = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=self.max_sequence_length,
                return_tensors="pt"
            )

            return {k: v.to(self.device) for k, v in encodings.items()}

        except Exception as e:
            logger.error(f"Error encoding issue: {e}")
            return {}

    def _save_analysis(self, analysis: Dict[str, Any]) -> None:
        """Save analysis results to file.

        Args:
            analysis: Analysis results to save
        """
        try:
            analysis_file = (
                self.analysis_dir /
                "results" /
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

    def _save_suggestions(self, suggestions: List[Dict[str, Any]]) -> None:
        """Save fix suggestions to file.

        Args:
            suggestions: Fix suggestions to save
        """
        try:
            suggestions_file = (
                self.analysis_dir /
                "fixes" /
                f"suggestions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(suggestions_file, "w") as f:
                json.dump(suggestions, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving suggestions: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            logger.error(f"Error cleaning up AI analyzer: {e}")

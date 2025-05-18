#!/usr/bin/env python3
"""
Performance Sniffing Module
This module implements performance analysis and monitoring capabilities
"""

import os
import sys
import logging
import asyncio
import json
import ast
import time
import psutil
import cProfile
import pstats
import io
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from ..config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing/performance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class PerformanceIssue:
    """Data class for performance issues"""
    type: str
    severity: str
    description: str
    location: str
    metric_name: str
    current_value: float
    threshold: float
    recommendation: str
    profiling_data: Optional[Dict] = None
    stack_trace: Optional[str] = None

class PerformanceSniffer:
    """Implements performance analysis capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["performance"]
        self.thresholds = self.config["thresholds"]
        self.monitoring = self.config["monitoring"]
        self.report_dir = Path("reports/sniffing/performance")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.profiler = cProfile.Profile()

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform performance sniffing on a file"""
        logger.info(f"Starting performance sniffing for file: {file_path}")

        issues = []
        metrics = {}
        profiling_data = {}

        try:
            # Analyze file performance
            perf_analysis = await self._analyze_performance(file_path)
            issues.extend(perf_analysis["issues"])
            metrics.update(perf_analysis["metrics"])
            profiling_data.update(perf_analysis["profiling"])

            # Calculate scores
            scores = self._calculate_scores(issues, metrics)

            return {
                "file_path": file_path,
                "domain": "performance",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": self._calculate_coverage(profiling_data),
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, issues, metrics, profiling_data)
            }

        except Exception as e:
            logger.error(f"Error in performance sniffing: {e}")
            return self._generate_error_result(file_path, str(e))

    async def _analyze_performance(self, file_path: str) -> Dict:
        """Analyze file performance"""
        issues = []
        metrics = {
            "execution_time": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "throughput": 0.0
        }
        profiling_data = {}

        try:
            # Static analysis for performance issues
            static_issues = await self._analyze_static_performance(file_path)
            issues.extend(static_issues)

            # Profile code execution
            profile_results = await self._profile_code(file_path)
            issues.extend(profile_results["issues"])
            metrics.update(profile_results["metrics"])
            profiling_data.update(profile_results["profiling"])

            # Monitor resource usage
            resource_metrics = await self._monitor_resources(file_path)
            metrics.update(resource_metrics)

            # Check performance thresholds
            threshold_issues = self._check_performance_thresholds(metrics)
            issues.extend(threshold_issues)

        except Exception as e:
            logger.error(f"Error analyzing performance in {file_path}: {e}")
            issues.append(PerformanceIssue(
                type="analysis_error",
                severity="critical",
                description=f"Error analyzing performance: {str(e)}",
                location=file_path,
                metric_name="analysis",
                current_value=0.0,
                threshold=0.0,
                recommendation="Fix performance analysis errors",
                stack_trace=str(e)
            ))

        return {
            "issues": issues,
            "metrics": metrics,
            "profiling": profiling_data
        }

    async def _analyze_static_performance(self, file_path: str) -> List[PerformanceIssue]:
        """Analyze static performance issues"""
        issues = []

        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())

            # Visit AST nodes
            visitor = PerformanceVisitor(file_path)
            visitor.visit(tree)
            issues.extend(visitor.issues)

        except Exception as e:
            logger.error(f"Error in static performance analysis: {e}")
            issues.append(PerformanceIssue(
                type="static_analysis_error",
                severity="high",
                description=f"Static analysis error: {str(e)}",
                location=file_path,
                metric_name="static_analysis",
                current_value=0.0,
                threshold=0.0,
                recommendation="Fix static analysis errors"
            ))

        return issues

    async def _profile_code(self, file_path: str) -> Dict:
        """Profile code execution"""
        issues = []
        metrics = {}
        profiling_data = {}

        try:
            # Start profiling
            self.profiler.enable()

            # Import and execute the module
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Stop profiling
            self.profiler.disable()

            # Analyze profiling results
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats()

            # Parse profiling data
            profiling_data = self._parse_profiling_stats(s.getvalue())

            # Calculate metrics
            metrics["execution_time"] = profiling_data["total_time"]
            metrics["function_calls"] = profiling_data["total_calls"]

            # Check for performance bottlenecks
            for func, stats in profiling_data["functions"].items():
                if stats["cumtime"] > self.thresholds["max_function_time"]:
                    issues.append(PerformanceIssue(
                        type="slow_function",
                        severity="high",
                        description=f"Function {func} is too slow",
                        location=file_path,
                        metric_name="execution_time",
                        current_value=stats["cumtime"],
                        threshold=self.thresholds["max_function_time"],
                        recommendation="Optimize function execution time",
                        profiling_data=stats
                    ))

        except Exception as e:
            logger.error(f"Error profiling code: {e}")
            issues.append(PerformanceIssue(
                type="profiling_error",
                severity="high",
                description=f"Profiling error: {str(e)}",
                location=file_path,
                metric_name="profiling",
                current_value=0.0,
                threshold=0.0,
                recommendation="Fix profiling errors"
            ))

        return {
            "issues": issues,
            "metrics": metrics,
            "profiling": profiling_data
        }

    async def _monitor_resources(self, file_path: str) -> Dict:
        """Monitor resource usage"""
        metrics = {}

        try:
            # Get process
            process = psutil.Process()

            # Monitor CPU usage
            cpu_percent = process.cpu_percent(interval=1.0)
            metrics["cpu_usage"] = cpu_percent

            # Monitor memory usage
            memory_info = process.memory_info()
            metrics["memory_usage"] = memory_info.rss / 1024 / 1024  # Convert to MB

            # Monitor I/O operations
            io_counters = process.io_counters()
            metrics["io_read_bytes"] = io_counters.read_bytes
            metrics["io_write_bytes"] = io_counters.write_bytes

        except Exception as e:
            logger.error(f"Error monitoring resources: {e}")

        return metrics

    def _parse_profiling_stats(self, stats_output: str) -> Dict:
        """Parse profiling statistics"""
        stats = {
            "total_time": 0.0,
            "total_calls": 0,
            "functions": {}
        }

        try:
            lines = stats_output.split('\n')
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 6:
                    ncalls = int(parts[0].split('/')[0])
                    tottime = float(parts[1])
                    percall = float(parts[2])
                    cumtime = float(parts[3])
                    percall_cum = float(parts[4])
                    function_name = ' '.join(parts[5:])

                    stats["total_calls"] += ncalls
                    stats["total_time"] += cumtime
                    stats["functions"][function_name] = {
                        "ncalls": ncalls,
                        "tottime": tottime,
                        "percall": percall,
                        "cumtime": cumtime,
                        "percall_cum": percall_cum
                    }

        except Exception as e:
            logger.error(f"Error parsing profiling stats: {e}")

        return stats

    def _check_performance_thresholds(self, metrics: Dict) -> List[PerformanceIssue]:
        """Check if metrics meet thresholds"""
        issues = []

        for metric, value in metrics.items():
            threshold_key = f"max_{metric}" if "max" in self.thresholds else f"min_{metric}"
            if threshold_key in self.thresholds:
                threshold = self.thresholds[threshold_key]

                if ("max" in threshold_key and value > threshold) or \
                   ("min" in threshold_key and value < threshold):
                    issues.append(PerformanceIssue(
                        type=f"{metric}_threshold",
                        severity="high",
                        description=f"{metric} threshold exceeded",
                        location="performance_metrics",
                        metric_name=metric,
                        current_value=value,
                        threshold=threshold,
                        recommendation=f"Optimize {metric} to meet threshold"
                    ))

        return issues

    def _calculate_scores(self, issues: List[PerformanceIssue], metrics: Dict) -> Dict[str, float]:
        """Calculate performance scores"""
        scores = {
            "performance": 100.0,
            "efficiency": 100.0,
            "resource_usage": 100.0
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["performance"] -= 20.0
            elif issue.severity == "high":
                scores["performance"] -= 10.0
            elif issue.severity == "medium":
                scores["performance"] -= 5.0
            elif issue.severity == "low":
                scores["performance"] -= 2.0

        # Calculate efficiency score
        if "execution_time" in metrics:
            max_time = self.thresholds["max_response_time"]
            actual_time = metrics["execution_time"] * 1000  # Convert to ms
            scores["efficiency"] = max(0.0, 100.0 * (1 - actual_time / max_time))

        # Calculate resource usage score
        if "memory_usage" in metrics and "cpu_usage" in metrics:
            memory_score = max(0.0, 100.0 * (1 - metrics["memory_usage"] / self.thresholds["max_memory_usage"]))
            cpu_score = max(0.0, 100.0 * (1 - metrics["cpu_usage"] / self.thresholds["max_cpu_usage"]))
            scores["resource_usage"] = (memory_score + cpu_score) / 2

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _calculate_coverage(self, profiling_data: Dict) -> float:
        """Calculate performance analysis coverage"""
        if not profiling_data or "functions" not in profiling_data:
            return 0.0

        return min(100.0, len(profiling_data["functions"]) * 10.0)

    def _generate_audit_info(self, file_path: str, issues: List[PerformanceIssue],
                           metrics: Dict, profiling_data: Dict) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "total_issues": len(issues),
            "metrics": metrics,
            "profiling_summary": {
                "total_time": profiling_data.get("total_time", 0.0),
                "total_calls": profiling_data.get("total_calls", 0),
                "function_count": len(profiling_data.get("functions", {}))
            },
            "compliance": {
                "performance_threshold_met": all(
                    i.current_value <= i.threshold
                    for i in issues if "max" in i.metric_name
                ),
                "resource_usage_met": metrics.get("memory_usage", 0) <= self.thresholds["max_memory_usage"]
                                    and metrics.get("cpu_usage", 0) <= self.thresholds["max_cpu_usage"]
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "performance",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during performance sniffing: {error}",
                "location": file_path,
                "metric_name": "sniffing",
                "current_value": 0.0,
                "threshold": 0.0,
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"performance": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

class PerformanceVisitor(ast.NodeVisitor):
    """AST visitor for analyzing performance patterns"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.loop_depth = 0

    def visit_For(self, node):
        """Visit for loop"""
        self.loop_depth += 1
        if self.loop_depth > 2:
            self.issues.append(PerformanceIssue(
                type="nested_loops",
                severity="medium",
                description="Deeply nested loops detected",
                location=f"{self.file_path}:{node.lineno}",
                metric_name="complexity",
                current_value=self.loop_depth,
                threshold=2,
                recommendation="Refactor nested loops to improve performance"
            ))
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node):
        """Visit while loop"""
        self.loop_depth += 1
        if self.loop_depth > 2:
            self.issues.append(PerformanceIssue(
                type="nested_loops",
                severity="medium",
                description="Deeply nested loops detected",
                location=f"{self.file_path}:{node.lineno}",
                metric_name="complexity",
                current_value=self.loop_depth,
                threshold=2,
                recommendation="Refactor nested loops to improve performance"
            ))
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_ListComp(self, node):
        """Visit list comprehension"""
        generators = len(node.generators)
        if generators > 1:
            self.issues.append(PerformanceIssue(
                type="complex_comprehension",
                severity="low",
                description="Complex list comprehension detected",
                location=f"{self.file_path}:{node.lineno}",
                metric_name="complexity",
                current_value=generators,
                threshold=1,
                recommendation="Simplify list comprehension or use regular loops"
            ))
        self.generic_visit(node)

async def main():
    """Main function"""
    try:
        sniffer = PerformanceSniffer()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Performance sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

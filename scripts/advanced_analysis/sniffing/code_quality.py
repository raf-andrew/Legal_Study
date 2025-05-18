#!/usr/bin/env python3
"""
Code Quality Sniffing Module
This module implements code quality analysis and validation capabilities
"""

import os
import sys
import logging
import asyncio
import json
import ast
import re
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
        logging.FileHandler('logs/sniffing/code_quality.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class CodeQualityIssue:
    """Data class for code quality issues"""
    type: str
    severity: str
    description: str
    location: str
    line_number: int
    code_snippet: str
    recommendation: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None

class CodeQualitySniffer:
    """Implements code quality analysis capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["code_quality"]
        self.thresholds = self.config["thresholds"]
        self.metrics = self.config["metrics"]
        self.report_dir = Path("reports/sniffing/code_quality")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform code quality sniffing on a file"""
        logger.info(f"Starting code quality sniffing for file: {file_path}")

        issues = []
        metrics = {}

        try:
            # Analyze code quality
            quality_analysis = await self._analyze_code_quality(file_path)
            issues.extend(quality_analysis["issues"])
            metrics.update(quality_analysis["metrics"])

            # Calculate scores
            scores = self._calculate_scores(issues, metrics)

            return {
                "file_path": file_path,
                "domain": "code_quality",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": self._calculate_coverage(metrics),
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, issues, metrics)
            }

        except Exception as e:
            logger.error(f"Error in code quality sniffing: {e}")
            return self._generate_error_result(file_path, str(e))

    async def _analyze_code_quality(self, file_path: str) -> Dict:
        """Analyze code quality"""
        issues = []
        metrics = {
            "complexity": 0.0,
            "maintainability": 0.0,
            "duplicates": 0,
            "style": 0.0
        }

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)
                lines = content.split('\n')

            # Analyze code complexity
            complexity_visitor = ComplexityVisitor(file_path)
            complexity_visitor.visit(tree)
            issues.extend(complexity_visitor.issues)
            metrics["complexity"] = complexity_visitor.complexity

            # Analyze code style
            style_issues = await self._analyze_style(file_path, lines)
            issues.extend(style_issues)
            metrics["style"] = 100.0 - (len(style_issues) * 5)

            # Analyze maintainability
            maintainability_issues = await self._analyze_maintainability(file_path, tree)
            issues.extend(maintainability_issues)
            metrics["maintainability"] = self._calculate_maintainability_index(tree)

            # Analyze code duplication
            duplicate_issues = await self._analyze_duplicates(file_path, lines)
            issues.extend(duplicate_issues)
            metrics["duplicates"] = len(duplicate_issues)

            # Check quality thresholds
            threshold_issues = self._check_quality_thresholds(metrics)
            issues.extend(threshold_issues)

        except Exception as e:
            logger.error(f"Error analyzing code quality in {file_path}: {e}")
            issues.append(CodeQualityIssue(
                type="analysis_error",
                severity="critical",
                description=f"Error analyzing code quality: {str(e)}",
                location=file_path,
                line_number=0,
                code_snippet="N/A",
                recommendation="Fix code quality analysis errors"
            ))

        return {
            "issues": issues,
            "metrics": metrics
        }

    async def _analyze_style(self, file_path: str, lines: List[str]) -> List[CodeQualityIssue]:
        """Analyze code style"""
        issues = []

        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(CodeQualityIssue(
                    type="style",
                    severity="low",
                    description="Line too long",
                    location=file_path,
                    line_number=i,
                    code_snippet=line,
                    recommendation="Keep lines under 100 characters",
                    metric_name="line_length",
                    current_value=len(line),
                    threshold=100
                ))

        # Check naming conventions
        for node in ast.walk(ast.parse('\n'.join(lines))):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append(CodeQualityIssue(
                        type="style",
                        severity="low",
                        description="Invalid function name",
                        location=file_path,
                        line_number=node.lineno,
                        code_snippet=lines[node.lineno - 1],
                        recommendation="Use snake_case for function names",
                        metric_name="naming_convention"
                    ))
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append(CodeQualityIssue(
                        type="style",
                        severity="low",
                        description="Invalid class name",
                        location=file_path,
                        line_number=node.lineno,
                        code_snippet=lines[node.lineno - 1],
                        recommendation="Use PascalCase for class names",
                        metric_name="naming_convention"
                    ))

        return issues

    async def _analyze_maintainability(self, file_path: str, tree: ast.AST) -> List[CodeQualityIssue]:
        """Analyze code maintainability"""
        issues = []

        # Check function length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = len(node.body)
                if func_lines > 50:
                    issues.append(CodeQualityIssue(
                        type="maintainability",
                        severity="medium",
                        description="Function too long",
                        location=file_path,
                        line_number=node.lineno,
                        code_snippet=f"Function {node.name} ({func_lines} lines)",
                        recommendation="Break down large functions into smaller ones",
                        metric_name="function_length",
                        current_value=func_lines,
                        threshold=50
                    ))

        # Check class complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                if methods > 10:
                    issues.append(CodeQualityIssue(
                        type="maintainability",
                        severity="medium",
                        description="Class has too many methods",
                        location=file_path,
                        line_number=node.lineno,
                        code_snippet=f"Class {node.name} ({methods} methods)",
                        recommendation="Split class into smaller classes",
                        metric_name="class_size",
                        current_value=methods,
                        threshold=10
                    ))

        return issues

    async def _analyze_duplicates(self, file_path: str, lines: List[str]) -> List[CodeQualityIssue]:
        """Analyze code duplication"""
        issues = []
        min_duplicate_lines = 6
        line_hashes = {}

        # Calculate line hashes
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith(('#', '"', "'")):
                line_hash = hash(stripped_line)
                if line_hash in line_hashes:
                    line_hashes[line_hash].append(i)
                else:
                    line_hashes[line_hash] = [i]

        # Check for duplicate blocks
        for line_numbers in line_hashes.values():
            if len(line_numbers) > 1:
                block = '\n'.join(lines[line_numbers[0]:line_numbers[0] + min_duplicate_lines])
                issues.append(CodeQualityIssue(
                    type="duplication",
                    severity="medium",
                    description="Duplicate code block detected",
                    location=file_path,
                    line_number=line_numbers[0] + 1,
                    code_snippet=block,
                    recommendation="Refactor duplicate code into reusable functions",
                    metric_name="duplicates",
                    current_value=len(line_numbers),
                    threshold=1
                ))

        return issues

    def _calculate_maintainability_index(self, tree: ast.AST) -> float:
        """Calculate maintainability index"""
        # Halstead volume
        operators = set()
        operands = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.operator):
                operators.add(node.__class__.__name__)
            elif isinstance(node, ast.Name):
                operands.add(node.id)

        n1 = len(operators)  # unique operators
        n2 = len(operands)   # unique operands
        N1 = sum(1 for node in ast.walk(tree) if isinstance(node, ast.operator))  # total operators
        N2 = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Name))      # total operands

        volume = (N1 + N2) * (n1 + n2).bit_length() if n1 + n2 > 0 else 0

        # Cyclomatic complexity
        complexity = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)))

        # Lines of code
        loc = len(ast.unparse(tree).split('\n'))

        # Calculate maintainability index
        mi = max(0, (171 - 5.2 * volume - 0.23 * complexity - 16.2 * loc) * 100 / 171)
        return mi

    def _check_quality_thresholds(self, metrics: Dict) -> List[CodeQualityIssue]:
        """Check if metrics meet thresholds"""
        issues = []

        for metric, value in metrics.items():
            threshold_key = f"{'max' if metric in ['complexity', 'duplicates'] else 'min'}_{metric}"
            if threshold_key in self.thresholds:
                threshold = self.thresholds[threshold_key]
                if (metric in ['complexity', 'duplicates'] and value > threshold) or \
                   (metric not in ['complexity', 'duplicates'] and value < threshold):
                    issues.append(CodeQualityIssue(
                        type=f"{metric}_threshold",
                        severity="high",
                        description=f"{metric.capitalize()} threshold not met",
                        location="metrics",
                        line_number=0,
                        code_snippet="N/A",
                        recommendation=f"Improve code {metric}",
                        metric_name=metric,
                        current_value=value,
                        threshold=threshold
                    ))

        return issues

    def _calculate_scores(self, issues: List[CodeQualityIssue], metrics: Dict) -> Dict[str, float]:
        """Calculate code quality scores"""
        scores = {
            "code_quality": 100.0,
            "style": metrics.get("style", 0.0),
            "maintainability": metrics.get("maintainability", 0.0)
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["code_quality"] -= 20.0
            elif issue.severity == "high":
                scores["code_quality"] -= 10.0
            elif issue.severity == "medium":
                scores["code_quality"] -= 5.0
            elif issue.severity == "low":
                scores["code_quality"] -= 2.0

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _calculate_coverage(self, metrics: Dict) -> float:
        """Calculate code quality analysis coverage"""
        return sum(1 for metric in self.metrics if metric in metrics) / len(self.metrics) * 100.0

    def _generate_audit_info(self, file_path: str, issues: List[CodeQualityIssue], metrics: Dict) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "total_issues": len(issues),
            "metrics": metrics,
            "compliance": {
                "quality_threshold_met": metrics.get("maintainability", 0) >=
                                      self.thresholds["min_maintainability"],
                "complexity_threshold_met": metrics.get("complexity", float('inf')) <=
                                         self.thresholds["max_complexity"]
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "code_quality",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during code quality sniffing: {error}",
                "location": file_path,
                "line_number": 0,
                "code_snippet": "N/A",
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"code_quality": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for analyzing code complexity"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.complexity = 0
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Visit function definition"""
        self.current_function = node.name
        complexity = 1  # Base complexity

        # Count branches
        complexity += sum(1 for n in ast.walk(node)
                        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try)))

        if complexity > 10:
            self.issues.append(CodeQualityIssue(
                type="complexity",
                severity="high",
                description=f"Function {node.name} is too complex",
                location=self.file_path,
                line_number=node.lineno,
                code_snippet=f"Function {node.name} (complexity: {complexity})",
                recommendation="Reduce function complexity",
                metric_name="cyclomatic_complexity",
                current_value=complexity,
                threshold=10
            ))

        self.complexity = max(self.complexity, complexity)
        self.generic_visit(node)
        self.current_function = None

async def main():
    """Main function"""
    try:
        sniffer = CodeQualitySniffer()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Code quality sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

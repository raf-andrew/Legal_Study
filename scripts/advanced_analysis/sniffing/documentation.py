#!/usr/bin/env python3
"""
Documentation Sniffing Module
This module implements documentation analysis and validation capabilities
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
        logging.FileHandler('logs/sniffing/documentation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class DocumentationIssue:
    """Data class for documentation issues"""
    type: str
    severity: str
    description: str
    location: str
    element_type: str
    element_name: str
    expected: str
    actual: str
    recommendation: str
    line_number: Optional[int] = None

class DocumentationSniffer:
    """Implements documentation analysis capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["documentation"]
        self.thresholds = self.config["thresholds"]
        self.doc_types = self.config["doc_types"]
        self.report_dir = Path("reports/sniffing/documentation")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform documentation sniffing on a file"""
        logger.info(f"Starting documentation sniffing for file: {file_path}")

        issues = []
        metrics = {}
        doc_elements = []

        try:
            # Analyze file documentation
            doc_analysis = await self._analyze_documentation(file_path)
            issues.extend(doc_analysis["issues"])
            metrics.update(doc_analysis["metrics"])
            doc_elements.extend(doc_analysis["elements"])

            # Calculate scores
            scores = self._calculate_scores(issues, metrics)

            return {
                "file_path": file_path,
                "domain": "documentation",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": self._calculate_coverage(doc_elements, metrics),
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, doc_elements, issues, metrics)
            }

        except Exception as e:
            logger.error(f"Error in documentation sniffing: {e}")
            return self._generate_error_result(file_path, str(e))

    async def _analyze_documentation(self, file_path: str) -> Dict:
        """Analyze file documentation"""
        issues = []
        metrics = {
            "total_elements": 0,
            "documented_elements": 0,
            "doc_quality_score": 0.0,
            "api_doc_coverage": 0.0
        }
        doc_elements = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)

            # Analyze module docstring
            module_doc = ast.get_docstring(tree)
            if not module_doc:
                issues.append(DocumentationIssue(
                    type="missing_docstring",
                    severity="high",
                    description="Module missing docstring",
                    location=file_path,
                    element_type="module",
                    element_name=Path(file_path).name,
                    expected="Module level docstring",
                    actual="No docstring",
                    recommendation="Add module level docstring"
                ))
            else:
                doc_elements.append({
                    "type": "module",
                    "name": Path(file_path).name,
                    "docstring": module_doc
                })
                metrics["documented_elements"] += 1

            # Visit all nodes
            visitor = DocVisitor(file_path)
            visitor.visit(tree)

            # Process visitor results
            issues.extend(visitor.issues)
            doc_elements.extend(visitor.doc_elements)

            # Update metrics
            metrics["total_elements"] = len(visitor.all_elements)
            metrics["documented_elements"] += len(visitor.doc_elements)

            if metrics["total_elements"] > 0:
                metrics["doc_quality_score"] = self._calculate_doc_quality(doc_elements)
                metrics["api_doc_coverage"] = (metrics["documented_elements"] /
                                             metrics["total_elements"]) * 100.0

            # Check documentation standards
            standard_issues = self._check_documentation_standards(doc_elements)
            issues.extend(standard_issues)

        except Exception as e:
            logger.error(f"Error analyzing documentation in {file_path}: {e}")
            issues.append(DocumentationIssue(
                type="analysis_error",
                severity="critical",
                description=f"Error analyzing documentation: {str(e)}",
                location=file_path,
                element_type="file",
                element_name=Path(file_path).name,
                expected="Successful analysis",
                actual=str(e),
                recommendation="Fix documentation analysis errors"
            ))

        return {
            "issues": issues,
            "metrics": metrics,
            "elements": doc_elements
        }

    def _calculate_doc_quality(self, doc_elements: List[Dict]) -> float:
        """Calculate documentation quality score"""
        if not doc_elements:
            return 0.0

        total_score = 0.0
        for element in doc_elements:
            docstring = element["docstring"]
            if not docstring:
                continue

            # Score based on various quality metrics
            score = 100.0

            # Check length
            if len(docstring.split()) < 10:
                score -= 20.0

            # Check sections
            if "Parameters:" not in docstring and "Args:" not in docstring:
                score -= 10.0
            if "Returns:" not in docstring:
                score -= 10.0
            if "Raises:" not in docstring and "Exceptions:" not in docstring:
                score -= 10.0

            # Check examples
            if "Example:" not in docstring and "Examples:" not in docstring:
                score -= 10.0

            total_score += max(0.0, score)

        return total_score / len(doc_elements)

    def _check_documentation_standards(self, doc_elements: List[Dict]) -> List[DocumentationIssue]:
        """Check documentation against standards"""
        issues = []

        for element in doc_elements:
            docstring = element["docstring"]
            if not docstring:
                continue

            # Check format (Google style)
            if not self._is_google_style(docstring):
                issues.append(DocumentationIssue(
                    type="style_violation",
                    severity="medium",
                    description="Docstring not in Google style format",
                    location=element.get("location", "unknown"),
                    element_type=element["type"],
                    element_name=element["name"],
                    expected="Google style docstring",
                    actual="Non-standard format",
                    recommendation="Convert docstring to Google style format"
                ))

            # Check completeness
            if element["type"] in ["class", "function"]:
                if not self._has_complete_sections(docstring):
                    issues.append(DocumentationIssue(
                        type="incomplete_docstring",
                        severity="medium",
                        description="Docstring missing required sections",
                        location=element.get("location", "unknown"),
                        element_type=element["type"],
                        element_name=element["name"],
                        expected="Complete docstring sections",
                        actual="Missing sections",
                        recommendation="Add missing docstring sections"
                    ))

        return issues

    def _is_google_style(self, docstring: str) -> bool:
        """Check if docstring follows Google style"""
        patterns = [
            r"Args:",
            r"Returns:",
            r"Raises:",
            r"Examples?:"
        ]

        # Check indentation and section headers
        lines = docstring.split("\n")
        if len(lines) < 2:
            return False

        # Check for section headers
        has_sections = any(re.search(pattern, docstring) for pattern in patterns)

        # Check indentation
        content_lines = [line.strip() for line in lines[1:] if line.strip()]
        proper_indent = all(line.startswith("    ") for line in content_lines)

        return has_sections and proper_indent

    def _has_complete_sections(self, docstring: str) -> bool:
        """Check if docstring has all required sections"""
        required_sections = {
            "description": r"^\s*[A-Z].*\.$",  # Starts with capital, ends with period
            "arguments": r"Args:|Parameters:",
            "returns": r"Returns:|Yields:",
            "raises": r"Raises:|Exceptions:"
        }

        return all(re.search(pattern, docstring, re.MULTILINE)
                  for pattern in required_sections.values())

    def _calculate_scores(self, issues: List[DocumentationIssue], metrics: Dict) -> Dict[str, float]:
        """Calculate documentation scores"""
        scores = {
            "documentation": 100.0,
            "quality": metrics.get("doc_quality_score", 0.0),
            "coverage": metrics.get("api_doc_coverage", 0.0)
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["documentation"] -= 20.0
            elif issue.severity == "high":
                scores["documentation"] -= 10.0
            elif issue.severity == "medium":
                scores["documentation"] -= 5.0
            elif issue.severity == "low":
                scores["documentation"] -= 2.0

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _calculate_coverage(self, doc_elements: List[Dict], metrics: Dict) -> float:
        """Calculate documentation coverage"""
        if not doc_elements:
            return 0.0
        return metrics.get("api_doc_coverage", 0.0)

    def _generate_audit_info(self, file_path: str, doc_elements: List[Dict],
                           issues: List[DocumentationIssue], metrics: Dict) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "elements_analyzed": [f"{e['type']} {e['name']}" for e in doc_elements],
            "total_issues": len(issues),
            "metrics": metrics,
            "compliance": {
                "coverage_threshold_met": metrics.get("api_doc_coverage", 0) >=
                                       self.thresholds["min_api_doc_coverage"],
                "quality_threshold_met": metrics.get("doc_quality_score", 0) >=
                                      self.thresholds["min_doc_quality"]
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "documentation",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during documentation sniffing: {error}",
                "location": file_path,
                "element_type": "file",
                "element_name": Path(file_path).name,
                "expected": "Successful sniffing",
                "actual": error,
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"documentation": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

class DocVisitor(ast.NodeVisitor):
    """AST visitor for analyzing documentation"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.doc_elements = []
        self.all_elements = []
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit class definition"""
        self.all_elements.append({
            "type": "class",
            "name": node.name,
            "location": f"{self.file_path}:{node.lineno}"
        })

        docstring = ast.get_docstring(node)
        if not docstring:
            self.issues.append(DocumentationIssue(
                type="missing_docstring",
                severity="high",
                description="Class missing docstring",
                location=self.file_path,
                element_type="class",
                element_name=node.name,
                expected="Class level docstring",
                actual="No docstring",
                recommendation="Add class level docstring",
                line_number=node.lineno
            ))
        else:
            self.doc_elements.append({
                "type": "class",
                "name": node.name,
                "docstring": docstring,
                "location": f"{self.file_path}:{node.lineno}"
            })

        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definition"""
        self.all_elements.append({
            "type": "function",
            "name": f"{self.current_class}.{node.name}" if self.current_class else node.name,
            "location": f"{self.file_path}:{node.lineno}"
        })

        docstring = ast.get_docstring(node)
        if not docstring:
            self.issues.append(DocumentationIssue(
                type="missing_docstring",
                severity="high",
                description="Function missing docstring",
                location=self.file_path,
                element_type="function",
                element_name=node.name,
                expected="Function level docstring",
                actual="No docstring",
                recommendation="Add function level docstring",
                line_number=node.lineno
            ))
        else:
            self.doc_elements.append({
                "type": "function",
                "name": f"{self.current_class}.{node.name}" if self.current_class else node.name,
                "docstring": docstring,
                "location": f"{self.file_path}:{node.lineno}"
            })

        self.generic_visit(node)

async def main():
    """Main function"""
    try:
        sniffer = DocumentationSniffer()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Documentation sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

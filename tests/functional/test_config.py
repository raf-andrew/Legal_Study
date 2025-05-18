"""
Configuration for systematic functional testing framework.
"""
from dataclasses import dataclass
from typing import Dict, List, Set
from pathlib import Path

@dataclass
class TestCategory:
    """Represents a test category with its requirements."""
    name: str
    description: str
    checklist_items: List[str]
    required_steps: List[str]
    min_coverage: float
    required_evidence: List[str]

# Test categories and their requirements
TEST_CATEGORIES = {
    "api": TestCategory(
        name="API Endpoints",
        description="Functional testing of all API endpoints",
        checklist_items=[
            "api_health",
            "api_security",
            "api_performance",
            "api_error_handling"
        ],
        required_steps=[
            "Health check",
            "Authentication",
            "Authorization",
            "Rate limiting",
            "Error handling",
            "Response validation"
        ],
        min_coverage=95.0,
        required_evidence=[
            "coverage_report",
            "response_logs",
            "error_logs"
        ]
    ),
    "core": TestCategory(
        name="Core Services",
        description="Testing of core service functionality",
        checklist_items=[
            "core_health",
            "core_security",
            "core_performance"
        ],
        required_steps=[
            "Service initialization",
            "Configuration loading",
            "Dependency checks",
            "Resource management"
        ],
        min_coverage=90.0,
        required_evidence=[
            "service_logs",
            "resource_usage",
            "dependency_graph"
        ]
    ),
    "security": TestCategory(
        name="Security Features",
        description="Testing of security features and controls",
        checklist_items=[
            "security_auth",
            "security_encryption",
            "security_audit"
        ],
        required_steps=[
            "Authentication",
            "Authorization",
            "Encryption",
            "Audit logging",
            "Vulnerability scan"
        ],
        min_coverage=100.0,
        required_evidence=[
            "security_logs",
            "audit_trail",
            "vulnerability_report"
        ]
    )
}

# Directory structure for test artifacts
TEST_DIRS = {
    "reports": Path("reports/functional_tests"),
    "evidence": Path("reports/functional_tests/evidence"),
    "logs": Path("reports/functional_tests/logs"),
    "coverage": Path("reports/functional_tests/coverage")
}

# Certification requirements
CERTIFICATION_REQUIREMENTS = {
    "min_coverage": 90.0,
    "required_categories": {"api", "core", "security"},
    "required_evidence": {
        "coverage_report",
        "test_logs",
        "verification_steps"
    }
}

def get_test_category(category: str) -> TestCategory:
    """Get test category configuration."""
    if category not in TEST_CATEGORIES:
        raise ValueError(f"Unknown test category: {category}")
    return TEST_CATEGORIES[category]

def get_checklist_items(category: str) -> List[str]:
    """Get checklist items for a test category."""
    return get_test_category(category).checklist_items

def get_required_coverage(category: str) -> float:
    """Get required coverage for a test category."""
    return get_test_category(category).min_coverage

def get_required_steps(category: str) -> List[str]:
    """Get required verification steps for a test category."""
    return get_test_category(category).required_steps

def get_required_evidence(category: str) -> List[str]:
    """Get required evidence for a test category."""
    return get_test_category(category).required_evidence

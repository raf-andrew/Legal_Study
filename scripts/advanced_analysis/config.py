"""
Advanced Analysis Configuration
This module contains configuration settings for the advanced analysis system
"""

from pathlib import Path
from typing import Dict, List

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Create base directories
for directory in [REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Sniffing configuration
SNIFFING_CONFIG = {
    "version": "2.0.0",
    "max_workers": 4,
    "file_extensions": [
        ".py", ".js", ".ts", ".html", ".css", ".vue", ".jsx", ".tsx",
        ".json", ".yaml", ".yml", ".md", ".sql", ".sh"
    ],
    "domains": {
        "security": {
            "enabled": True,
            "priority": 1,
            "thresholds": {
                "min_security_score": 95.0,
                "max_vulnerabilities": 0,
                "min_authentication_score": 95.0,
                "min_authorization_score": 95.0,
                "max_critical_issues": 0,
                "max_high_issues": 0
            },
            "compliance": {
                "soc2": True,
                "hipaa": False,
                "gdpr": True,
                "pci": False
            },
            "scan_targets": {
                "static": ["*.py", "*.js", "*.ts"],
                "dynamic": ["http://localhost:8000"],
                "dependencies": ["requirements.txt", "package.json"]
            }
        },
        "browser": {
            "enabled": True,
            "priority": 2,
            "thresholds": {
                "min_compatibility_score": 95.0,
                "min_responsive_score": 95.0,
                "min_accessibility_score": 95.0,
                "max_visual_differences": 0
            },
            "browsers": ["chrome", "firefox", "safari"],
            "viewport_sizes": [
                {"width": 1920, "height": 1080},  # Desktop
                {"width": 1366, "height": 768},   # Laptop
                {"width": 768, "height": 1024},   # Tablet
                {"width": 375, "height": 812}     # Mobile
            ],
            "accessibility": {
                "wcag_level": "AA",
                "check_contrast": True,
                "check_aria": True,
                "check_keyboard": True
            }
        },
        "functional": {
            "enabled": True,
            "priority": 3,
            "thresholds": {
                "min_functional_score": 95.0,
                "max_failed_tests": 0,
                "min_api_coverage": 95.0,
                "max_regression_issues": 0
            },
            "test_types": [
                "unit",
                "integration",
                "e2e",
                "regression"
            ]
        },
        "unit": {
            "enabled": True,
            "priority": 4,
            "thresholds": {
                "min_coverage": 90.0,
                "max_failed_tests": 0,
                "min_test_score": 95.0,
                "min_mutation_score": 85.0
            },
            "coverage_types": [
                "line",
                "branch",
                "function",
                "statement"
            ]
        },
        "api": {
            "enabled": True,
            "priority": 5,
            "thresholds": {
                "min_api_coverage": 95.0,
                "max_response_time": 500,  # ms
                "min_success_rate": 99.9,
                "max_error_rate": 0.1
            },
            "monitoring": {
                "health_check_interval": 60,  # seconds
                "performance_check_interval": 300,  # seconds
                "alert_threshold": 0.95
            }
        },
        "documentation": {
            "enabled": True,
            "priority": 6,
            "thresholds": {
                "min_doc_coverage": 95.0,
                "min_doc_quality": 90.0,
                "min_api_doc_coverage": 100.0,
                "max_outdated_docs": 0
            },
            "doc_types": [
                "readme",
                "api",
                "architecture",
                "deployment",
                "maintenance"
            ]
        },
        "performance": {
            "enabled": True,
            "priority": 7,
            "thresholds": {
                "max_response_time": 500,  # ms
                "max_memory_usage": 512,   # MB
                "min_throughput": 100,     # req/sec
                "max_cpu_usage": 80.0      # percent
            },
            "monitoring": {
                "check_interval": 60,      # seconds
                "history_retention": 30,    # days
                "alert_threshold": 0.9
            }
        },
        "code_quality": {
            "enabled": True,
            "priority": 8,
            "thresholds": {
                "min_quality_score": 90.0,
                "max_complexity": 10,
                "min_maintainability": 85.0,
                "max_duplicates": 3
            },
            "metrics": [
                "complexity",
                "maintainability",
                "duplicates",
                "style"
            ]
        }
    },
    "reporting": {
        "formats": ["json", "html", "markdown"],
        "consolidation": True,
        "history_retention": 30,  # days
        "metrics_tracking": True,
        "trend_analysis": True,
        "notification": {
            "slack": True,
            "email": True,
            "threshold": "error"
        }
    },
    "git_integration": {
        "pre_commit": {
            "enabled": True,
            "domains": ["security", "unit", "code_quality"]
        },
        "pre_push": {
            "enabled": True,
            "domains": ["security", "functional", "browser", "api"]
        },
        "post_merge": {
            "enabled": True,
            "domains": ["security", "functional", "browser", "api", "performance"]
        }
    },
    "audit": {
        "enabled": True,
        "retention": 365,  # days
        "compliance": {
            "soc2": True,
            "hipaa": False,
            "gdpr": True,
            "pci": False
        },
        "report_frequency": "daily"
    }
}

# MCP Configuration
MCP_CONFIG = {
    "version": "2.0.0",
    "analysis_interval": 3600,  # seconds
    "security_check_interval": 3600,  # seconds
    "api_check_interval": 60,   # seconds
    "parallel_jobs": 4,
    "max_api_response_time": 1.0,  # seconds
    "priority_order": [
        "security",
        "browser",
        "functional",
        "unit",
        "api",
        "documentation",
        "performance",
        "code_quality"
    ],
    "monitoring": {
        "enabled": True,
        "intervals": {
            "file_watch": 1,    # seconds
            "api_health": 60,   # seconds
            "performance": 300,  # seconds
            "security": 3600    # seconds
        },
        "retention": {
            "logs": 30,        # days
            "metrics": 90,     # days
            "reports": 365     # days
        }
    },
    "notification": {
        "slack_webhook": "SLACK_WEBHOOK_URL",
        "email": "team@example.com",
        "threshold": "error",
        "batch_interval": 300  # seconds
    },
    "ai_integration": {
        "enabled": True,
        "feedback_interval": 3600,  # seconds
        "learning_rate": 0.01,
        "adaptation_threshold": 0.8,
        "metrics": [
            "code_quality",
            "security",
            "performance",
            "test_coverage"
        ]
    }
}

# File-specific configurations
FILE_CONFIGS = {
    "**/*.py": {
        "linters": ["flake8", "pylint", "mypy"],
        "formatters": ["black", "isort"],
        "test_framework": "pytest",
        "documentation": ["docstring", "sphinx"],
        "security": ["bandit", "safety"]
    },
    "**/*.js": {
        "linters": ["eslint", "tsc"],
        "formatters": ["prettier"],
        "test_framework": "jest",
        "documentation": ["jsdoc"],
        "security": ["npm audit", "snyk"]
    },
    "**/*.ts": {
        "linters": ["tslint", "tsc"],
        "formatters": ["prettier"],
        "test_framework": "jest",
        "documentation": ["typedoc"],
        "security": ["npm audit", "snyk"]
    }
}

# Git hooks configuration
GIT_HOOKS = {
    "pre-commit": [
        "code_quality",
        "security_static",
        "unit_tests"
    ],
    "pre-push": [
        "full_analysis",
        "security_dynamic",
        "integration_tests"
    ],
    "post-merge": [
        "dependency_check",
        "security_scan",
        "performance_test"
    ]
}

# Security simulation configuration
SECURITY_SIMULATION = {
    "enabled": True,
    "interval": 3600,  # seconds
    "attack_vectors": [
        "sql_injection",
        "xss",
        "csrf",
        "file_upload",
        "authentication_bypass",
        "rate_limiting"
    ],
    "intensity_levels": ["low", "medium", "high"],
    "target_components": [
        "api_endpoints",
        "authentication",
        "file_handlers",
        "database",
        "ai_models"
    ],
    "reporting": {
        "detailed_logs": True,
        "attack_patterns": True,
        "vulnerability_mapping": True
    }
}

# AI Feedback configuration
AI_FEEDBACK = {
    "enabled": True,
    "learning_rate": 0.01,
    "feedback_metrics": [
        "code_quality_score",
        "test_coverage",
        "security_score",
        "performance_score"
    ],
    "adaptation_threshold": 0.8,
    "memory_retention": 1000,  # number of samples
    "reporting": {
        "frequency": "hourly",
        "metrics_history": 30,  # days
        "trend_analysis": True
    }
}

# Report configuration
REPORT_CONFIG = {
    "formats": ["html", "json", "markdown"],
    "consolidation": True,
    "history_retention": 30,  # days
    "metrics_tracking": True,
    "trend_analysis": True,
    "templates": {
        "html": "templates/report.html",
        "markdown": "templates/report.md",
        "notification": "templates/notification.md"
    }
}

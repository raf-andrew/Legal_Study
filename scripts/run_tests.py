#!/usr/bin/env python3
"""
Test Runner Script
This script automates the execution of all platform tests and generates reports.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_test_suite(suite_name, test_path, report_dir):
    """Run a test suite and record results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(report_dir) / f"{suite_name}_{timestamp}.json"

    # Run tests and capture results
    result = pytest.main([
        test_path,
        "-v",
        "--json-report",
        f"--json-report-file={report_file}",
        "--capture=tee-sys"
    ])

    # Add metadata to report
    with open(report_file, 'r') as f:
        report_data = json.load(f)

    report_data['suite_name'] = suite_name
    report_data['timestamp'] = timestamp
    report_data['exit_code'] = result

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    return result, report_file

def main():
    # Create reports directory
    report_dir = Path("test_reports/temp")
    report_dir.mkdir(parents=True, exist_ok=True)

    # Define test suites
    test_suites = [
        ("unit", "tests/unit"),
        ("security", "tests/security"),
        ("acid", "tests/acid"),
        ("notifications", "tests/notifications"),
        ("monitoring", "tests/monitoring"),
        ("error_handling", "tests/error_handling"),
        ("ai", "tests/ai")
    ]

    # Run each suite
    results = []
    for suite_name, test_path in test_suites:
        print(f"\nRunning {suite_name} tests...")
        result, report_file = run_test_suite(suite_name, test_path, report_dir)
        results.append({
            "suite": suite_name,
            "result": result,
            "report": str(report_file)
        })

    # Generate summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

    summary_file = report_dir / "test_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nTest summary written to {summary_file}")

if __name__ == "__main__":
    main()

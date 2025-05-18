"""
Pytest Configuration

This module configures pytest for the test suite.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "chaos: mark test as a chaos test"
    )
    config.addinivalue_line(
        "markers",
        "acid: mark test as an ACID test"
    )
    config.addinivalue_line(
        "markers",
        "smoke: mark test as a smoke test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test items in-place to handle test markers."""
    for item in items:
        if "test_chaos" in item.nodeid:
            item.add_marker("chaos")
        elif "test_acid" in item.nodeid:
            item.add_marker("acid")
        elif "test_smoke" in item.nodeid:
            item.add_marker("smoke") 
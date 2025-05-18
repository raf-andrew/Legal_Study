#!/usr/bin/env python3
"""
Setup script for the Health Check command.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="legal_study",
    version="0.1.0",
    author="Legal Study Team",
    author_email="legal-study@example.com",
    description="Console commands for the Legal Study System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/legal-study/console",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "requests",
        "prometheus-client",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-dotenv",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-json-report",
    ],
    entry_points={
        "console_scripts": [
            "legal-study=legal_study.console.cli:main",
            "legal-study-health=legal_study.console.health:main",
            "legal-study-security=legal_study.console.security:main",
            "legal-study-monitor=legal_study.console.monitor:main",
            "legal-study-test=legal_study.console.test:main",
            "legal-study-docs=legal_study.console.docs:main",
        ],
    },
    data_files=[
        ("config", ["config/config.yaml"]),
        ("docs", ["docs/README.md"]),
        ("tests", ["tests/__init__.py"]),
    ],
)

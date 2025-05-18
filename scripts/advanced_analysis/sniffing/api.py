#!/usr/bin/env python3
"""
API Sniffing Module
This module implements API testing and monitoring capabilities
"""

import os
import sys
import logging
import asyncio
import json
import aiohttp
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse

from ..config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing/api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ApiIssue:
    """Data class for API testing issues"""
    type: str
    severity: str
    description: str
    endpoint: str
    method: str
    expected: Any
    actual: Any
    recommendation: str
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    headers: Optional[Dict] = None

class ApiSniffer:
    """Implements API testing and monitoring capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["api"]
        self.thresholds = self.config["thresholds"]
        self.monitoring = self.config["monitoring"]
        self.report_dir = Path("reports/sniffing/api")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.endpoints = {}
        self.session = None

    async def initialize(self):
        """Initialize API sniffer"""
        self.session = aiohttp.ClientSession()
        await self._load_api_endpoints()

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform API sniffing on a file"""
        logger.info(f"Starting API sniffing for file: {file_path}")

        issues = []
        metrics = {}
        endpoints = []

        try:
            # Extract API endpoints from file
            endpoints = await self._extract_endpoints(file_path)

            # Test each endpoint
            for endpoint in endpoints:
                endpoint_results = await self._test_endpoint(endpoint)
                issues.extend(endpoint_results["issues"])
                metrics.update(endpoint_results["metrics"])

            # Calculate scores
            scores = self._calculate_scores(issues, metrics)

            return {
                "file_path": file_path,
                "domain": "api",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": self._calculate_coverage(endpoints, metrics),
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, endpoints, issues, metrics)
            }

        except Exception as e:
            logger.error(f"Error in API sniffing: {e}")
            return self._generate_error_result(file_path, str(e))

    async def _load_api_endpoints(self):
        """Load API endpoints from configuration files"""
        try:
            # Look for OpenAPI/Swagger specs
            spec_files = [
                "openapi.yaml",
                "openapi.json",
                "swagger.yaml",
                "swagger.json"
            ]

            for spec_file in spec_files:
                if os.path.exists(spec_file):
                    with open(spec_file, 'r') as f:
                        if spec_file.endswith('.yaml'):
                            spec = yaml.safe_load(f)
                        else:
                            spec = json.load(f)
                        self.endpoints.update(self._parse_openapi_spec(spec))
                        break

        except Exception as e:
            logger.error(f"Error loading API endpoints: {e}")

    def _parse_openapi_spec(self, spec: Dict) -> Dict:
        """Parse OpenAPI specification"""
        endpoints = {}
        base_path = spec.get('basePath', '')

        for path, path_spec in spec.get('paths', {}).items():
            full_path = f"{base_path}{path}"

            for method, operation in path_spec.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue

                endpoints[f"{method.upper()} {full_path}"] = {
                    'method': method.upper(),
                    'path': full_path,
                    'parameters': operation.get('parameters', []),
                    'responses': operation.get('responses', {}),
                    'security': operation.get('security', [])
                }

        return endpoints

    async def _extract_endpoints(self, file_path: str) -> List[Dict]:
        """Extract API endpoints from file"""
        endpoints = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for route decorators and definitions
            route_patterns = [
                r'@app.route\([\'"]([^\'"]+)[\'"](,\s*methods=\[([^\]]+)\])?\)',
                r'@api.route\([\'"]([^\'"]+)[\'"](,\s*methods=\[([^\]]+)\])?\)',
                r'router.(\w+)\([\'"]([^\'"]+)[\'"]\)'
            ]

            for pattern in route_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    if len(match.groups()) == 3:  # Flask-style route
                        path = match.group(1)
                        methods = match.group(3).split(',') if match.group(3) else ['GET']
                    else:  # Router-style route
                        path = match.group(2)
                        methods = [match.group(1).upper()]

                    for method in methods:
                        endpoints.append({
                            'method': method.strip().strip("'\"").upper(),
                            'path': path,
                            'source': file_path
                        })

        except Exception as e:
            logger.error(f"Error extracting endpoints from {file_path}: {e}")

        return endpoints

    async def _test_endpoint(self, endpoint: Dict) -> Dict:
        """Test an API endpoint"""
        issues = []
        metrics = {
            "response_time": 0.0,
            "success_rate": 0.0,
            "error_rate": 0.0
        }

        try:
            # Prepare request
            url = self._build_url(endpoint['path'])
            method = endpoint['method']

            # Make request
            start_time = datetime.now()
            async with self.session.request(method, url) as response:
                response_time = (datetime.now() - start_time).total_seconds()

                # Check response
                status_code = response.status
                response_data = await response.json()

                # Record metrics
                metrics["response_time"] = response_time
                metrics["success_rate"] = 100.0 if 200 <= status_code < 300 else 0.0
                metrics["error_rate"] = 100.0 if status_code >= 400 else 0.0

                # Check thresholds
                if response_time > self.thresholds["max_response_time"] / 1000:  # Convert to seconds
                    issues.append(ApiIssue(
                        type="performance",
                        severity="high",
                        description="Response time exceeds threshold",
                        endpoint=endpoint['path'],
                        method=method,
                        expected=f"<= {self.thresholds['max_response_time']}ms",
                        actual=f"{response_time * 1000:.2f}ms",
                        recommendation="Optimize endpoint performance",
                        response_time=response_time,
                        status_code=status_code,
                        headers=dict(response.headers)
                    ))

                if status_code >= 400:
                    issues.append(ApiIssue(
                        type="error",
                        severity="high",
                        description=f"Endpoint returned error status {status_code}",
                        endpoint=endpoint['path'],
                        method=method,
                        expected="2xx status code",
                        actual=f"{status_code}",
                        recommendation="Fix endpoint error handling",
                        response_time=response_time,
                        status_code=status_code,
                        headers=dict(response.headers)
                    ))

        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint['path']}: {e}")
            issues.append(ApiIssue(
                type="error",
                severity="critical",
                description=f"Failed to test endpoint: {str(e)}",
                endpoint=endpoint['path'],
                method=endpoint['method'],
                expected="Successful response",
                actual=str(e),
                recommendation="Fix endpoint availability"
            ))

        return {
            "issues": issues,
            "metrics": metrics
        }

    def _build_url(self, path: str) -> str:
        """Build full URL for endpoint"""
        # Implementation would use configuration for base URL
        base_url = "http://localhost:8000"  # Default for testing
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    def _calculate_scores(self, issues: List[ApiIssue], metrics: Dict) -> Dict[str, float]:
        """Calculate API testing scores"""
        scores = {
            "api": 100.0,
            "performance": 100.0,
            "reliability": 100.0
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["api"] -= 20.0
                scores["reliability"] -= 20.0
            elif issue.severity == "high":
                scores["api"] -= 10.0
                scores["reliability"] -= 10.0
            elif issue.severity == "medium":
                scores["api"] -= 5.0
            elif issue.severity == "low":
                scores["api"] -= 2.0

        # Adjust performance score
        if "response_time" in metrics:
            max_time = self.thresholds["max_response_time"]
            actual_time = metrics["response_time"] * 1000  # Convert to ms
            scores["performance"] = max(0.0, 100.0 * (1 - actual_time / max_time))

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _calculate_coverage(self, endpoints: List[Dict], metrics: Dict) -> float:
        """Calculate API coverage"""
        if not endpoints:
            return 0.0

        tested_endpoints = len([m for m in metrics.values() if m > 0])
        return (tested_endpoints / len(endpoints)) * 100.0

    def _generate_audit_info(self, file_path: str, endpoints: List[Dict],
                           issues: List[ApiIssue], metrics: Dict) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "endpoints_tested": [f"{e['method']} {e['path']}" for e in endpoints],
            "total_issues": len(issues),
            "metrics": metrics,
            "compliance": {
                "performance_threshold_met": all(
                    i.response_time <= self.thresholds["max_response_time"] / 1000
                    for i in issues if i.response_time is not None
                ),
                "error_rate_threshold_met": metrics.get("error_rate", 0) <= self.thresholds["max_error_rate"]
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "api",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during API sniffing: {error}",
                "endpoint": "unknown",
                "method": "unknown",
                "expected": "Successful sniffing",
                "actual": error,
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"api": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

async def main():
    """Main function"""
    try:
        sniffer = ApiSniffer()
        await sniffer.initialize()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
        await sniffer.cleanup()
    except Exception as e:
        logger.error(f"API sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

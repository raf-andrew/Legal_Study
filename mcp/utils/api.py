"""
MCP API integration utilities.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import yaml

logger = logging.getLogger("mcp_api")

class APIIntegration:
    """API integration manager."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize API integration.

        Args:
            config: API configuration
        """
        self.config = config
        self.session = None
        self.active_tests: Set[str] = set()
        self.metrics: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start API integration."""
        try:
            logger.info("Starting API integration...")
            self.session = aiohttp.ClientSession()
            logger.info("API integration started successfully")

        except Exception as e:
            logger.error(f"Error starting API integration: {e}")
            raise

    async def stop(self) -> None:
        """Stop API integration."""
        try:
            logger.info("Stopping API integration...")
            if self.session:
                await self.session.close()
            self.active_tests.clear()
            self.metrics.clear()
            logger.info("API integration stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping API integration: {e}")
            raise

    async def test_endpoint(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        expected_response: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Test API endpoint.

        Args:
            method: HTTP method
            url: Endpoint URL
            headers: Optional request headers
            params: Optional query parameters
            data: Optional form data
            json_data: Optional JSON data
            expected_status: Expected status code
            expected_response: Optional expected response
            timeout: Request timeout in seconds

        Returns:
            Test results
        """
        try:
            # Create test ID
            test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_tests.add(test_id)

            try:
                # Send request
                start_time = datetime.now()
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=timeout
                ) as response:
                    # Get response
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    end_time = datetime.now()

                # Create results
                duration = (end_time - start_time).total_seconds()
                success = status == expected_status
                if expected_response and success:
                    success = self._validate_response(response_data, expected_response)

                results = {
                    "id": test_id,
                    "timestamp": datetime.now(),
                    "request": {
                        "method": method,
                        "url": url,
                        "headers": headers,
                        "params": params,
                        "data": data,
                        "json": json_data
                    },
                    "response": {
                        "status": status,
                        "data": response_data
                    },
                    "expected": {
                        "status": expected_status,
                        "response": expected_response
                    },
                    "metrics": {
                        "duration": duration,
                        "success": success
                    }
                }

                # Update metrics
                self._update_metrics(results)

                return results

            finally:
                self.active_tests.remove(test_id)

        except Exception as e:
            logger.error(f"Error testing endpoint: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def _validate_response(
        self,
        response: Any,
        expected: Any
    ) -> bool:
        """Validate response against expected value.

        Args:
            response: Response value
            expected: Expected value

        Returns:
            Whether validation passed
        """
        try:
            if isinstance(expected, dict):
                if not isinstance(response, dict):
                    return False
                return all(
                    key in response and self._validate_response(response[key], value)
                    for key, value in expected.items()
                )
            elif isinstance(expected, list):
                if not isinstance(response, list):
                    return False
                return len(response) == len(expected) and all(
                    self._validate_response(a, b)
                    for a, b in zip(response, expected)
                )
            else:
                return response == expected

        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return False

    def _update_metrics(self, results: Dict[str, Any]) -> None:
        """Update metrics with test results.

        Args:
            results: Test results
        """
        try:
            # Get metrics
            metrics = self.metrics.get(results["request"]["url"], {
                "total": 0,
                "success": 0,
                "failure": 0,
                "duration": {
                    "count": 0,
                    "sum": 0.0
                }
            })

            # Update metrics
            metrics["total"] += 1
            if results["metrics"]["success"]:
                metrics["success"] += 1
            else:
                metrics["failure"] += 1
            metrics["duration"]["count"] += 1
            metrics["duration"]["sum"] += results["metrics"]["duration"]

            # Save metrics
            self.metrics[results["request"]["url"]] = metrics

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    async def load_contract(self, contract_path: str) -> Dict[str, Any]:
        """Load API contract.

        Args:
            contract_path: Path to contract file

        Returns:
            Contract dictionary
        """
        try:
            # Load contract
            with open(contract_path) as f:
                return yaml.safe_load(f)

        except Exception as e:
            logger.error(f"Error loading contract: {e}")
            return {}

    async def validate_contract(
        self,
        contract: Dict[str, Any],
        base_url: str
    ) -> Dict[str, Any]:
        """Validate API contract.

        Args:
            contract: API contract
            base_url: Base URL for endpoints

        Returns:
            Validation results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "endpoints": {}
            }

            # Test each endpoint
            for path, endpoint in contract.get("paths", {}).items():
                endpoint_results = {}
                url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

                for method, spec in endpoint.items():
                    # Get test cases
                    test_cases = spec.get("test_cases", [{"name": "default"}])

                    # Run test cases
                    method_results = []
                    for test_case in test_cases:
                        # Get test parameters
                        headers = test_case.get("headers")
                        params = test_case.get("params")
                        data = test_case.get("data")
                        json_data = test_case.get("json")
                        expected_status = test_case.get(
                            "expected_status",
                            spec.get("responses", {}).get("200", {}).get("status", 200)
                        )
                        expected_response = test_case.get(
                            "expected_response",
                            spec.get("responses", {}).get(str(expected_status), {}).get("schema")
                        )

                        # Run test
                        test_results = await self.test_endpoint(
                            method.upper(),
                            url,
                            headers=headers,
                            params=params,
                            data=data,
                            json_data=json_data,
                            expected_status=expected_status,
                            expected_response=expected_response
                        )
                        method_results.append(test_results)

                    endpoint_results[method] = method_results

                results["endpoints"][path] = endpoint_results

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error validating contract: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get API metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "active_tests": len(self.active_tests),
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def reset_metrics(self) -> None:
        """Reset API metrics."""
        try:
            self.metrics.clear()

        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")

    def get_health(self) -> Dict[str, Any]:
        """Get API health.

        Returns:
            Health status dictionary
        """
        try:
            return {
                "status": "healthy" if self.session else "unhealthy",
                "active_tests": len(self.active_tests),
                "metrics": self.get_metrics(),
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

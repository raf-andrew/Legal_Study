"""
API models for MCP server.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class SniffRequest(BaseModel):
    """Model for sniffing request."""

    files: Optional[List[str]] = Field(
        None,
        description="List of files to sniff"
    )
    domains: Optional[List[str]] = Field(
        None,
        description="List of domains to sniff"
    )
    priority: int = Field(
        1,
        description="Priority of sniffing job (1-10)"
    )
    fix: bool = Field(
        False,
        description="Whether to automatically fix issues"
    )
    verbose: bool = Field(
        False,
        description="Whether to enable verbose output"
    )
    trace: bool = Field(
        False,
        description="Whether to enable trace output"
    )

class SniffResult(BaseModel):
    """Model for sniffing result."""

    status: str = Field(
        ...,
        description="Status of sniffing job"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of result"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    results: Optional[Dict[str, Any]] = Field(
        None,
        description="Domain-specific results"
    )
    issues: Optional[Dict[str, int]] = Field(
        None,
        description="Issue counts by severity"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics"
    )

class FixRequest(BaseModel):
    """Model for fix request."""

    job_id: str = Field(
        ...,
        description="ID of job to fix issues for"
    )
    issues: List[str] = Field(
        ...,
        description="List of issue IDs to fix"
    )
    domains: Optional[List[str]] = Field(
        None,
        description="List of domains to fix issues for"
    )
    dry_run: bool = Field(
        False,
        description="Whether to simulate fixes without applying them"
    )

class FixResult(BaseModel):
    """Model for fix result."""

    status: str = Field(
        ...,
        description="Status of fix job"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of result"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    fixes: Optional[Dict[str, Any]] = Field(
        None,
        description="Applied fixes by domain"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics"
    )

class AnalyzeRequest(BaseModel):
    """Model for analysis request."""

    job_id: str = Field(
        ...,
        description="ID of job to analyze"
    )
    domains: Optional[List[str]] = Field(
        None,
        description="List of domains to analyze"
    )
    patterns: Optional[List[str]] = Field(
        None,
        description="List of patterns to detect"
    )
    confidence: float = Field(
        0.8,
        description="Minimum confidence threshold"
    )

class AnalyzeResult(BaseModel):
    """Model for analysis result."""

    status: str = Field(
        ...,
        description="Status of analysis job"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of result"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if job failed"
    )
    analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Analysis results by domain"
    )
    patterns: Optional[Dict[str, Any]] = Field(
        None,
        description="Detected patterns by domain"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics"
    )

class StatusResponse(BaseModel):
    """Model for status response."""

    status: str = Field(
        ...,
        description="Overall status"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of status"
    )
    active_jobs: int = Field(
        ...,
        description="Number of active jobs"
    )
    queued_jobs: int = Field(
        ...,
        description="Number of queued jobs"
    )
    runners: Dict[str, Any] = Field(
        ...,
        description="Runner status by domain"
    )
    metrics: Dict[str, Any] = Field(
        ...,
        description="Performance metrics"
    )

class HealthResponse(BaseModel):
    """Model for health response."""

    status: str = Field(
        ...,
        description="Overall health status"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of health check"
    )
    checks: Dict[str, Any] = Field(
        ...,
        description="Health check results"
    )
    metrics: Dict[str, Any] = Field(
        ...,
        description="Health metrics"
    )

class MetricsResponse(BaseModel):
    """Model for metrics response."""

    timestamp: datetime = Field(
        ...,
        description="Timestamp of metrics"
    )
    metrics: Dict[str, Any] = Field(
        ...,
        description="Collected metrics"
    )
    labels: Dict[str, str] = Field(
        ...,
        description="Metric labels"
    )
    help: Dict[str, str] = Field(
        ...,
        description="Metric descriptions"
    )

"""
Enhanced result class for storing and managing sniffing results.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class SniffingResult:
    """Class for storing and managing sniffing results."""

    def __init__(
        self,
        file: str,
        sniffer_type: str,
        status: bool = True,
        issues: Optional[List[Dict[str, Any]]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Initialize sniffing result.

        Args:
            file: Path to the sniffed file
            sniffer_type: Type of sniffer that produced this result
            status: Whether the sniffing was successful
            issues: Optional list of detected issues
            metrics: Optional metrics dictionary
        """
        self.file = file
        self.sniffer_type = sniffer_type
        self.status = status
        self.issues = issues or []
        self.metrics = metrics or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def add_issue(self, issue: Dict[str, Any]) -> None:
        """Add an issue to the result.

        Args:
            issue: Issue dictionary to add
        """
        issue["detected_at"] = datetime.now().isoformat()
        issue["file"] = self.file
        issue["sniffer_type"] = self.sniffer_type
        self.issues.append(issue)
        self.updated_at = datetime.now()

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update result metrics.

        Args:
            metrics: Metrics dictionary to update with
        """
        self.metrics.update(metrics)
        self.updated_at = datetime.now()

    def has_issues(self) -> bool:
        """Check if result has any issues.

        Returns:
            True if there are issues, False otherwise
        """
        return len(self.issues) > 0

    def has_critical_issues(self) -> bool:
        """Check if result has any critical issues.

        Returns:
            True if there are critical issues, False otherwise
        """
        return any(
            issue.get("severity") == "critical"
            for issue in self.issues
        )

    def get_issue_count(self, severity: Optional[str] = None) -> int:
        """Get count of issues with optional severity filter.

        Args:
            severity: Optional severity level to filter by

        Returns:
            Number of matching issues
        """
        if severity:
            return sum(1 for i in self.issues if i.get("severity") == severity)
        return len(self.issues)

    def get_metrics_value(self, key: str, default: Any = None) -> Any:
        """Get value of a specific metric.

        Args:
            key: Metric key to get
            default: Default value if key not found

        Returns:
            Metric value or default
        """
        return self.metrics.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of result
        """
        return {
            "file": self.file,
            "sniffer_type": self.sniffer_type,
            "status": self.status,
            "issues": self.issues,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def to_json(self) -> str:
        """Convert result to JSON string.

        Returns:
            JSON string representation of result
        """
        return json.dumps(self.to_dict(), indent=2)

    def save(self, path: Optional[str] = None) -> None:
        """Save result to file.

        Args:
            path: Optional path to save to. If not provided, uses default path.
        """
        if not path:
            # Create default path
            file_stem = Path(self.file).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"reports/{self.sniffer_type}/results/{file_stem}_{timestamp}.json"

        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save result
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "SniffingResult":
        """Load result from file.

        Args:
            path: Path to load from

        Returns:
            Loaded SniffingResult object
        """
        with open(path) as f:
            data = json.load(f)

        # Convert timestamps back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Create result object
        result = cls(
            file=data["file"],
            sniffer_type=data["sniffer_type"],
            status=data["status"]
        )
        result.issues = data["issues"]
        result.metrics = data["metrics"]
        result.created_at = data["created_at"]
        result.updated_at = data["updated_at"]

        return result

    def merge(self, other: "SniffingResult") -> None:
        """Merge another result into this one.

        Args:
            other: Other SniffingResult to merge
        """
        if self.file != other.file:
            raise ValueError("Cannot merge results from different files")

        # Merge issues
        self.issues.extend(other.issues)

        # Merge metrics
        self.metrics.update(other.metrics)

        # Update timestamp
        self.updated_at = datetime.now()

    def filter_issues(
        self,
        severity: Optional[str] = None,
        type: Optional[str] = None,
        fixed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filter issues based on criteria.

        Args:
            severity: Optional severity level to filter by
            type: Optional issue type to filter by
            fixed: Optional fixed status to filter by

        Returns:
            List of matching issues
        """
        filtered = self.issues

        if severity:
            filtered = [i for i in filtered if i.get("severity") == severity]

        if type:
            filtered = [i for i in filtered if i.get("type") == type]

        if fixed is not None:
            filtered = [i for i in filtered if i.get("fixed", False) == fixed]

        return filtered

    def mark_issue_fixed(self, issue_id: str) -> bool:
        """Mark an issue as fixed.

        Args:
            issue_id: ID of issue to mark as fixed

        Returns:
            True if issue was found and marked, False otherwise
        """
        for issue in self.issues:
            if issue.get("id") == issue_id:
                issue["fixed"] = True
                issue["fixed_at"] = datetime.now().isoformat()
                self.updated_at = datetime.now()
                return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of sniffing result.

        Returns:
            Summary dictionary
        """
        return {
            "file": self.file,
            "sniffer_type": self.sniffer_type,
            "status": self.status,
            "total_issues": len(self.issues),
            "critical_issues": self.get_issue_count("critical"),
            "high_issues": self.get_issue_count("high"),
            "medium_issues": self.get_issue_count("medium"),
            "low_issues": self.get_issue_count("low"),
            "fixed_issues": len([i for i in self.issues if i.get("fixed", False)]),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

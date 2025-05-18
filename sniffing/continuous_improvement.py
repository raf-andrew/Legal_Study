"""
Continuous improvement module for managing ongoing analysis and improvements.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

class ImprovementSession:
    """Represents a continuous improvement session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.improvements: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}

    def add_improvement(self, improvement: Dict[str, Any]) -> None:
        """Add an improvement to the session."""
        self.improvements.append({
            **improvement,
            "timestamp": datetime.now().isoformat()
        })

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update session metrics."""
        self.metrics.update(metrics)

    def end_session(self) -> None:
        """End the improvement session."""
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "improvements": self.improvements,
            "metrics": self.metrics
        }

class ContinuousImprovement:
    """Manages continuous improvement process."""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.sessions_dir = self.workspace_path / "improvement" / "sessions"
        self.current_session: Optional[ImprovementSession] = None

    def start_session(self) -> str:
        """Start a new improvement session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = ImprovementSession(session_id)
        return session_id

    def end_session(self) -> None:
        """End the current improvement session."""
        if self.current_session:
            self.current_session.end_session()
            self._save_session(self.current_session)
            self.current_session = None

    def add_improvement(self,
                       category: str,
                       description: str,
                       changes: List[Dict[str, Any]],
                       metrics: Optional[Dict[str, Any]] = None) -> None:
        """Add an improvement to the current session."""
        if not self.current_session:
            raise RuntimeError("No active improvement session")

        improvement = {
            "category": category,
            "description": description,
            "changes": changes,
            "metrics": metrics or {}
        }

        self.current_session.add_improvement(improvement)

    def update_session_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update metrics for the current session."""
        if not self.current_session:
            raise RuntimeError("No active improvement session")

        self.current_session.update_metrics(metrics)

    def get_session_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history of improvement sessions."""
        sessions = []

        # Ensure sessions directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Load session files
        session_files = sorted(self.sessions_dir.glob("*.json"), reverse=True)
        if limit:
            session_files = session_files[:limit]

        for session_file in session_files:
            with open(session_file, 'r') as f:
                sessions.append(json.load(f))

        return sessions

    def analyze_improvements(self) -> Dict[str, Any]:
        """Analyze improvement history and generate insights."""
        sessions = self.get_session_history()

        # Calculate improvement metrics
        total_improvements = sum(len(s["improvements"]) for s in sessions)
        categories = {}
        impact_metrics = {}

        for session in sessions:
            for improvement in session["improvements"]:
                # Track categories
                cat = improvement["category"]
                categories[cat] = categories.get(cat, 0) + 1

                # Track impact metrics
                for metric, value in improvement.get("metrics", {}).items():
                    if metric not in impact_metrics:
                        impact_metrics[metric] = []
                    impact_metrics[metric].append(value)

        return {
            "total_sessions": len(sessions),
            "total_improvements": total_improvements,
            "improvement_categories": categories,
            "impact_metrics": {
                metric: {
                    "count": len(values),
                    "average": sum(values) / len(values) if values else 0
                }
                for metric, values in impact_metrics.items()
            }
        }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on improvement history."""
        analysis = self.analyze_improvements()
        recommendations = []

        # Identify areas needing attention
        categories = analysis["improvement_categories"]
        if categories:
            least_improved = min(categories.items(), key=lambda x: x[1])[0]
            recommendations.append({
                "category": "focus_area",
                "description": f"Increase focus on {least_improved} improvements",
                "priority": "high"
            })

        # Analyze impact metrics
        metrics = analysis["impact_metrics"]
        for metric, stats in metrics.items():
            if stats["average"] < 0.5:  # Example threshold
                recommendations.append({
                    "category": "metric_improvement",
                    "description": f"Work on improving {metric} metric",
                    "priority": "medium"
                })

        return recommendations

    def _save_session(self, session: ImprovementSession) -> None:
        """Save session data to file."""
        # Ensure sessions directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Save session data
        session_path = self.sessions_dir / f"session_{session.session_id}.json"
        with open(session_path, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

    def get_improvement_metrics(self) -> Dict[str, Any]:
        """Get current improvement metrics."""
        if not self.current_session:
            return {}

        return {
            "session_id": self.current_session.session_id,
            "duration": (datetime.now() - self.current_session.start_time).total_seconds(),
            "improvements_count": len(self.current_session.improvements),
            "metrics": self.current_session.metrics
        }

    def export_report(self, output_path: Optional[Path] = None) -> Path:
        """Export improvement report to file."""
        if not output_path:
            output_path = self.workspace_path / "improvement" / "reports" / f"report_{datetime.now().strftime('%Y%m%d')}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "generated_at": datetime.now().isoformat(),
            "analysis": self.analyze_improvements(),
            "recommendations": self.generate_recommendations(),
            "recent_sessions": self.get_session_history(limit=5)
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return output_path

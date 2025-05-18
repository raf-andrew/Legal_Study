#!/usr/bin/env python3
"""
Continuous Improvement Script
This script manages continuous sniffing, analysis, and improvement workflow
"""

import os
import sys
import logging
import asyncio
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass

from .config import SNIFFING_CONFIG
from .sniffing import SniffingSystem
from .mcp import MasterControlProgram
from .fix_issues import IssueFixer
from .git_integration import GitIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_improvement.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ImprovementSession:
    """Data class for improvement session"""
    session_id: str
    start_time: datetime
    target: str
    domains: List[str]
    initial_scores: Dict[str, float]
    current_scores: Dict[str, float]
    fixed_issues: List[Dict]
    remaining_issues: List[Dict]
    audit_trail: List[Dict]

class ContinuousImprovement:
    """Manages continuous improvement workflow"""

    def __init__(self):
        self.mcp = MasterControlProgram()
        self.sniffing_system = SniffingSystem()
        self.issue_fixer = IssueFixer()
        self.git_integration = GitIntegration()
        self.base_dir = Path("reports/continuous_improvement")
        self.session_dir = None
        self.current_session = None
        self._setup_directories()

    def _setup_directories(self):
        """Set up directory structure"""
        directories = [
            self.base_dir,
            self.base_dir / "sessions",
            self.base_dir / "audit",
            self.base_dir / "metrics",
            self.base_dir / "ai_feedback"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize components"""
        await self.mcp.initialize()
        await self.issue_fixer.initialize()
        await self.git_integration.initialize()

    async def start_session(self, target: str, domains: Optional[List[str]] = None,
                          continuous: bool = True, interval: int = None):
        """Start improvement session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.base_dir / "sessions" / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting improvement session {session_id} for {target}")

        try:
            # Initial sniffing
            initial_results = await self.mcp.run_sniffing(target, domains)
            initial_scores = self._extract_scores(initial_results)

            # Create session
            self.current_session = ImprovementSession(
                session_id=session_id,
                start_time=datetime.now(),
                target=target,
                domains=domains or list(SNIFFING_CONFIG["domains"].keys()),
                initial_scores=initial_scores,
                current_scores=initial_scores.copy(),
                fixed_issues=[],
                remaining_issues=self._extract_issues(initial_results),
                audit_trail=[]
            )

            # Save initial state
            await self._save_session_state("initial")

            if continuous:
                await self._run_continuous_improvement(interval)
            else:
                await self._run_single_improvement()

        except Exception as e:
            logger.error(f"Error in improvement session: {e}")
            raise

    async def _run_continuous_improvement(self, interval: Optional[int] = None):
        """Run continuous improvement loop"""
        try:
            while True:
                # Run improvement cycle
                await self._run_improvement_cycle()

                # Check if we've reached target scores
                if self._check_target_scores():
                    logger.info("Reached target scores, stopping continuous improvement")
                    break

                # Wait for interval
                await asyncio.sleep(interval or SNIFFING_CONFIG.get("improvement_interval", 3600))

        except asyncio.CancelledError:
            logger.info("Continuous improvement cancelled")
        except Exception as e:
            logger.error(f"Error in continuous improvement: {e}")
            raise

    async def _run_single_improvement(self):
        """Run single improvement cycle"""
        await self._run_improvement_cycle()

    async def _run_improvement_cycle(self):
        """Run one improvement cycle"""
        try:
            # Get current issues
            current_results = await self.mcp.run_sniffing(
                self.current_session.target,
                self.current_session.domains
            )

            # Fix issues
            fixed = await self.issue_fixer.fix_issues(
                self.current_session.target,
                self.current_session.domains,
                interactive=False
            )

            # Update session state
            self.current_session.current_scores = self._extract_scores(current_results)
            self.current_session.fixed_issues.extend(fixed["fixed_issues"])
            self.current_session.remaining_issues = self._extract_issues(fixed["verification_results"])
            self.current_session.audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "improvement_cycle",
                "scores": self.current_session.current_scores,
                "fixed_count": len(fixed["fixed_issues"]),
                "remaining_count": len(self.current_session.remaining_issues)
            })

            # Save current state
            await self._save_session_state("cycle")

            # Update AI feedback
            await self._update_ai_feedback()

            # Check Git workflow
            await self._check_git_workflow()

        except Exception as e:
            logger.error(f"Error in improvement cycle: {e}")
            raise

    def _extract_scores(self, results: Dict) -> Dict[str, float]:
        """Extract scores from results"""
        scores = {}
        for result in results.values():
            for domain, score in result.get("scores", {}).items():
                if domain not in scores:
                    scores[domain] = []
                scores[domain].append(score)

        return {
            domain: sum(domain_scores) / len(domain_scores)
            for domain, domain_scores in scores.items()
        }

    def _extract_issues(self, results: Dict) -> List[Dict]:
        """Extract issues from results"""
        issues = []
        for result in results.values():
            for issue in result.get("issues", []):
                issues.append({
                    "file_path": result["file_path"],
                    **issue
                })
        return issues

    def _check_target_scores(self) -> bool:
        """Check if we've reached target scores"""
        for domain, scores in self.current_session.current_scores.items():
            threshold = SNIFFING_CONFIG["domains"][domain]["thresholds"].get("target_score", 95.0)
            if scores < threshold:
                return False
        return True

    async def _save_session_state(self, state_type: str):
        """Save session state"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_file = self.session_dir / f"{state_type}_state_{timestamp}.json"

        state = {
            "session_id": self.current_session.session_id,
            "timestamp": datetime.now().isoformat(),
            "target": self.current_session.target,
            "domains": self.current_session.domains,
            "scores": {
                "initial": self.current_session.initial_scores,
                "current": self.current_session.current_scores
            },
            "issues": {
                "fixed": len(self.current_session.fixed_issues),
                "remaining": len(self.current_session.remaining_issues)
            },
            "audit_trail": self.current_session.audit_trail
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    async def _update_ai_feedback(self):
        """Update AI feedback"""
        feedback_file = self.base_dir / "ai_feedback" / f"{self.current_session.session_id}.json"

        feedback = {
            "session_id": self.current_session.session_id,
            "timestamp": datetime.now().isoformat(),
            "learning_metrics": {
                "improvement_rate": self._calculate_improvement_rate(),
                "fix_success_rate": self._calculate_fix_success_rate(),
                "domain_progress": self._calculate_domain_progress()
            },
            "recommendations": self._generate_ai_recommendations()
        }

        with open(feedback_file, 'w') as f:
            json.dump(feedback, f, indent=2)

    def _calculate_improvement_rate(self) -> Dict[str, float]:
        """Calculate improvement rate by domain"""
        rates = {}
        for domain in self.current_session.domains:
            initial = self.current_session.initial_scores.get(domain, 0.0)
            current = self.current_session.current_scores.get(domain, 0.0)
            rates[domain] = max(0.0, (current - initial) / initial * 100) if initial > 0 else 0.0
        return rates

    def _calculate_fix_success_rate(self) -> float:
        """Calculate fix success rate"""
        total_attempts = len(self.current_session.fixed_issues) + len(self.current_session.remaining_issues)
        if total_attempts == 0:
            return 0.0
        return len(self.current_session.fixed_issues) / total_attempts * 100.0

    def _calculate_domain_progress(self) -> Dict[str, Dict[str, float]]:
        """Calculate progress by domain"""
        progress = {}
        for domain in self.current_session.domains:
            threshold = SNIFFING_CONFIG["domains"][domain]["thresholds"].get("target_score", 95.0)
            current = self.current_session.current_scores.get(domain, 0.0)
            progress[domain] = {
                "current": current,
                "target": threshold,
                "progress": (current / threshold * 100) if threshold > 0 else 0.0
            }
        return progress

    def _generate_ai_recommendations(self) -> List[Dict]:
        """Generate AI recommendations"""
        recommendations = []

        # Analyze patterns in remaining issues
        issue_patterns = self._analyze_issue_patterns()

        # Generate recommendations based on patterns
        for pattern in issue_patterns:
            recommendations.append({
                "type": pattern["type"],
                "frequency": pattern["frequency"],
                "recommendation": pattern["recommendation"],
                "priority": pattern["priority"]
            })

        return sorted(recommendations, key=lambda x: x["priority"], reverse=True)

    def _analyze_issue_patterns(self) -> List[Dict]:
        """Analyze patterns in issues"""
        patterns = {}

        for issue in self.current_session.remaining_issues:
            key = (issue["type"], issue["severity"])
            if key not in patterns:
                patterns[key] = {
                    "type": issue["type"],
                    "severity": issue["severity"],
                    "count": 0,
                    "files": set(),
                    "recommendation": issue["recommendation"]
                }
            patterns[key]["count"] += 1
            patterns[key]["files"].add(issue["file_path"])

        return [
            {
                "type": p["type"],
                "frequency": p["count"],
                "affected_files": len(p["files"]),
                "recommendation": p["recommendation"],
                "priority": self._calculate_pattern_priority(p)
            }
            for p in patterns.values()
        ]

    def _calculate_pattern_priority(self, pattern: Dict) -> int:
        """Calculate priority for a pattern"""
        severity_weights = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        severity_score = severity_weights.get(pattern["severity"], 0)
        frequency_score = min(pattern["count"] / 10, 1.0)  # Normalize frequency
        file_score = min(len(pattern["files"]) / 5, 1.0)   # Normalize file count

        return int((severity_score * 0.5 + frequency_score * 0.3 + file_score * 0.2) * 100)

    async def _check_git_workflow(self):
        """Check Git workflow integration"""
        try:
            # Run pre-commit check
            pre_commit = await self.git_integration.run_pre_commit_check()

            if pre_commit["status"] == "fail":
                logger.warning("Pre-commit checks failing - fixes needed before commit")

            # Add to audit trail
            self.current_session.audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "git_workflow_check",
                "pre_commit_status": pre_commit["status"]
            })

        except Exception as e:
            logger.error(f"Error checking Git workflow: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run continuous improvement")
    parser.add_argument("target", help="Target file or directory")
    parser.add_argument("--domains", nargs="+", help="Specific domains to improve")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, help="Interval between cycles (seconds)")

    args = parser.parse_args()

    try:
        improver = ContinuousImprovement()
        await improver.initialize()
        await improver.start_session(
            args.target,
            domains=args.domains,
            continuous=args.continuous,
            interval=args.interval
        )
    except Exception as e:
        logger.error(f"Continuous improvement failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

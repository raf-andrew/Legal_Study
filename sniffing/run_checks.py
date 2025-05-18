"""
Main entry point for running sniffing checks.
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .core import BaseSniffer, SnifferType, SniffingResult
from .continuous_improvement import ContinuousImprovement
from .git_integration import GitIntegration

def load_sniffers() -> Dict[SnifferType, Type[BaseSniffer]]:
    """Load all available sniffers."""
    from .functional_sniffer import FunctionalSniffer
    # Import other sniffers here

    return {
        SnifferType.FUNCTIONAL: FunctionalSniffer,
        # Add other sniffer mappings
    }

def run_checks(args: argparse.Namespace) -> bool:
    """Run sniffing checks based on command line arguments."""
    # Initialize components
    git = GitIntegration()
    improvement = ContinuousImprovement()

    # Start improvement session
    session_id = improvement.start_session()

    try:
        # Load configuration
        config = load_config(args)

        # Get changed files for targeted checking
        changed_files = git.get_changed_files() if args.pre_commit else None

        # Initialize sniffers
        sniffers = initialize_sniffers(config, changed_files)

        # Run checks
        results = run_sniffer_checks(sniffers, args.comprehensive)

        # Process results
        success = process_results(results, improvement, git)

        # Generate reports
        if args.report:
            generate_reports(results, improvement)

        return success

    finally:
        # End improvement session
        improvement.end_session()

def load_config(args: argparse.Namespace) -> Dict:
    """Load configuration from file or defaults."""
    import yaml

    config_path = Path(args.config) if args.config else Path("sniffing.yaml")

    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)

    return {
        "workspace_path": ".",
        "min_coverage": 80,
        "style_guide": "google",
        "performance_thresholds": {
            "response_time": 200,
            "memory_usage": 100
        }
    }

def initialize_sniffers(
    config: Dict,
    changed_files: Optional[List[str]] = None
) -> Dict[SnifferType, BaseSniffer]:
    """Initialize sniffers with configuration."""
    sniffer_classes = load_sniffers()
    sniffers = {}

    for sniffer_type, sniffer_class in sniffer_classes.items():
        sniffer_config = {
            **config,
            "changed_files": changed_files
        }
        sniffers[sniffer_type] = sniffer_class(sniffer_config)

    return sniffers

def run_sniffer_checks(
    sniffers: Dict[SnifferType, BaseSniffer],
    comprehensive: bool = False
) -> Dict[SnifferType, SniffingResult]:
    """Run checks using initialized sniffers."""
    results = {}

    for sniffer_type, sniffer in sniffers.items():
        # Skip non-critical checks in quick mode
        if not comprehensive and sniffer_type not in [SnifferType.FUNCTIONAL, SnifferType.UNIT]:
            continue

        results[sniffer_type] = sniffer.sniff()

    return results

def process_results(
    results: Dict[SnifferType, SniffingResult],
    improvement: ContinuousImprovement,
    git: GitIntegration
) -> bool:
    """Process sniffing results and take appropriate actions."""
    success = True

    for sniffer_type, result in results.items():
        # Track improvements
        if result.issues:
            improvement.add_improvement(
                category=sniffer_type.value,
                description=f"Found {len(result.issues)} issues in {sniffer_type.value} check",
                changes=[{"type": "issue", "data": issue} for issue in result.issues],
                metrics=result.metrics
            )

        # Update metrics
        improvement.update_session_metrics(result.metrics)

        # Create audit trail
        if result.audit_trail:
            git.create_audit_commit({
                "type": sniffer_type.value,
                "timestamp": result.timestamp.isoformat(),
                "data": result.audit_trail
            })

        # Update success flag
        success = success and result.status

    return success

def generate_reports(
    results: Dict[SnifferType, SniffingResult],
    improvement: ContinuousImprovement
) -> None:
    """Generate comprehensive reports."""
    # Export improvement report
    improvement.export_report()

    # Generate recommendations
    recommendations = improvement.generate_recommendations()

    # Print summary
    print("\nCheck Results:")
    for sniffer_type, result in results.items():
        status = "✓" if result.status else "✗"
        print(f"{status} {sniffer_type.value}: {len(result.issues)} issues found")

    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"- [{rec['priority']}] {rec['description']}")

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run code sniffing checks")

    parser.add_argument("--pre-commit", action="store_true", help="Run pre-commit checks")
    parser.add_argument("--pre-push", action="store_true", help="Run pre-push checks")
    parser.add_argument("--post-merge", action="store_true", help="Run post-merge checks")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive checks")
    parser.add_argument("--report", action="store_true", help="Generate detailed reports")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--update-dependencies", action="store_true", help="Update dependencies")

    args = parser.parse_args()

    try:
        success = run_checks(args)
        return 0 if success else 1
    except Exception as e:
        print(f"Error running checks: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())

"""
Main entry point for sniffing infrastructure.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from rich.console import Console
from rich.logging import RichHandler

from .mcp.server.mcp_server import MCPServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("sniffing")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Sniffing infrastructure")

    # File selection
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to check"
    )
    parser.add_argument(
        "--domains",
        nargs="*",
        choices=["security", "browser", "functional", "unit", "documentation"],
        help="Specific domains to check"
    )

    # Test options
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full test suite"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues"
    )

    # Output options
    parser.add_argument(
        "--report",
        choices=["json", "html", "pdf"],
        default="json",
        help="Report format"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

async def run_sniffing(args: argparse.Namespace) -> int:
    """Run sniffing infrastructure."""
    try:
        console = Console()

        # Load configuration
        config = load_config()
        if not config:
            return 1

        # Initialize MCP server
        mcp_server = MCPServer(config.get("mcp", {}))

        # Get files to check
        files = get_files_to_check(args)
        if not files and not args.full:
            logger.error("No files to check")
            return 1

        # Get domains to check
        domains = get_domains_to_check(args)

        # Run checks
        console.print("\n[bold blue]Running Sniffing Infrastructure[/bold blue]")

        if args.full:
            results = await run_full_suite(mcp_server)
        else:
            results = await run_targeted_checks(mcp_server, files, domains)

        if not results:
            return 1

        # Generate report
        report = await generate_report(mcp_server, results, args.report)
        if not report:
            return 1

        # Handle results
        return handle_results(results, report, args)

    except Exception as e:
        logger.error(f"Error running sniffing: {e}")
        return 1

def get_files_to_check(args: argparse.Namespace) -> List[str]:
    """Get list of files to check."""
    try:
        if args.files:
            return args.files

        # Get all relevant files
        files = []
        for ext in [".py", ".js", ".ts", ".html", ".css"]:
            files.extend(str(f) for f in Path(".").glob(f"**/*{ext}"))

        return files

    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return []

def get_domains_to_check(args: argparse.Namespace) -> List[str]:
    """Get list of domains to check."""
    if args.domains:
        return args.domains

    # Check all domains by default
    return [
        "security",
        "browser",
        "functional",
        "unit",
        "documentation"
    ]

async def run_full_suite(mcp_server: MCPServer) -> Optional[Dict[str, Any]]:
    """Run full test suite."""
    try:
        console = Console()
        console.print("\n[bold green]Running Full Test Suite[/bold green]")

        # Get all files
        files = get_files_to_check(argparse.Namespace(files=None))

        # Get all domains
        domains = get_domains_to_check(argparse.Namespace(domains=None))

        # Run sniffing
        results = await mcp_server.run_sniffing(files, domains)

        # Analyze results
        analysis = await mcp_server.analyze_results(results.get("results", []))

        # Run compliance checks
        compliance = await check_compliance(mcp_server, results)

        return {
            "status": results.get("status") and compliance.get("status", False),
            "results": results.get("results", []),
            "analysis": analysis,
            "compliance": compliance
        }

    except Exception as e:
        logger.error(f"Error running full suite: {e}")
        return None

async def run_targeted_checks(
    mcp_server: MCPServer,
    files: List[str],
    domains: List[str]
) -> Optional[Dict[str, Any]]:
    """Run targeted checks on specific files and domains."""
    try:
        console = Console()
        console.print(f"\n[bold green]Running Targeted Checks[/bold green]")
        console.print(f"Files: {', '.join(files)}")
        console.print(f"Domains: {', '.join(domains)}")

        # Run sniffing
        results = await mcp_server.run_sniffing(files, domains)

        # Analyze results
        analysis = await mcp_server.analyze_results(results.get("results", []))

        return {
            "status": results.get("status"),
            "results": results.get("results", []),
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error running targeted checks: {e}")
        return None

async def check_compliance(mcp_server: MCPServer, results: Dict[str, Any]) -> Dict[str, Any]:
    """Check compliance requirements."""
    try:
        console = Console()
        console.print("\n[bold blue]Checking Compliance Requirements[/bold blue]")

        compliance_checks = {
            "coverage": check_coverage_requirements(results),
            "security": check_security_requirements(results),
            "documentation": check_documentation_requirements(results)
        }

        # Check all requirements are met
        status = all(check.get("status", False) for check in compliance_checks.values())

        return {
            "status": status,
            "checks": compliance_checks
        }

    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_coverage_requirements(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check code coverage requirements."""
    try:
        # Get coverage metrics
        coverage = {}
        for result in results.get("results", []):
            if "coverage" in result.get("metrics", {}):
                domain = result.get("domain", "unknown")
                coverage[domain] = result["metrics"]["coverage"]

        # Check against thresholds
        thresholds = {
            "unit": 90,
            "functional": 80,
            "browser": 70
        }

        failures = []
        for domain, threshold in thresholds.items():
            if domain in coverage and coverage[domain] < threshold:
                failures.append({
                    "domain": domain,
                    "coverage": coverage[domain],
                    "threshold": threshold
                })

        return {
            "status": len(failures) == 0,
            "coverage": coverage,
            "failures": failures
        }

    except Exception as e:
        logger.error(f"Error checking coverage: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_security_requirements(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check security requirements."""
    try:
        # Get security metrics
        security_results = None
        for result in results.get("results", []):
            if result.get("domain") == "security":
                security_results = result
                break

        if not security_results:
            return {
                "status": False,
                "error": "No security results found"
            }

        # Check requirements
        requirements = {
            "vulnerabilities": check_vulnerabilities(security_results),
            "compliance": check_security_compliance(security_results),
            "dependencies": check_dependencies(security_results)
        }

        # Check all requirements are met
        status = all(req.get("status", False) for req in requirements.values())

        return {
            "status": status,
            "requirements": requirements
        }

    except Exception as e:
        logger.error(f"Error checking security: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_vulnerabilities(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check vulnerability requirements."""
    try:
        issues = results.get("issues", [])
        high_severity = sum(1 for i in issues if i.get("severity") == "high")
        medium_severity = sum(1 for i in issues if i.get("severity") == "medium")

        # No high severity vulnerabilities allowed
        # Maximum 5 medium severity vulnerabilities
        status = high_severity == 0 and medium_severity <= 5

        return {
            "status": status,
            "high_severity": high_severity,
            "medium_severity": medium_severity
        }

    except Exception as e:
        logger.error(f"Error checking vulnerabilities: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_security_compliance(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check security compliance requirements."""
    try:
        metrics = results.get("metrics", {})
        compliance_score = metrics.get("compliance_score", 0)

        # Minimum compliance score of 80%
        status = compliance_score >= 80

        return {
            "status": status,
            "compliance_score": compliance_score
        }

    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_dependencies(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check dependency requirements."""
    try:
        metrics = results.get("metrics", {})
        outdated_deps = metrics.get("outdated_dependencies", 0)
        vulnerable_deps = metrics.get("vulnerable_dependencies", 0)

        # Maximum 3 outdated dependencies
        # No vulnerable dependencies
        status = outdated_deps <= 3 and vulnerable_deps == 0

        return {
            "status": status,
            "outdated_dependencies": outdated_deps,
            "vulnerable_dependencies": vulnerable_deps
        }

    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        return {
            "status": False,
            "error": str(e)
        }

def check_documentation_requirements(results: Dict[str, Any]) -> Dict[str, Any]:
    """Check documentation requirements."""
    try:
        # Get documentation metrics
        doc_results = None
        for result in results.get("results", []):
            if result.get("domain") == "documentation":
                doc_results = result
                break

        if not doc_results:
            return {
                "status": False,
                "error": "No documentation results found"
            }

        metrics = doc_results.get("metrics", {})
        coverage = metrics.get("coverage", 0)

        # Minimum documentation coverage of 95%
        status = coverage >= 95

        return {
            "status": status,
            "coverage": coverage
        }

    except Exception as e:
        logger.error(f"Error checking documentation: {e}")
        return {
            "status": False,
            "error": str(e)
        }

async def generate_report(
    mcp_server: MCPServer,
    results: Dict[str, Any],
    format: str
) -> Optional[Dict[str, Any]]:
    """Generate report in specified format."""
    try:
        console = Console()
        console.print(f"\n[bold blue]Generating {format.upper()} Report[/bold blue]")

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(f"reports/sniffing_report_{timestamp}.{format}")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            import json
            with open(report_file, "w") as f:
                json.dump(results, f, indent=2)

        elif format == "html":
            # Generate HTML report
            from jinja2 import Template
            template = Template(get_html_template())
            html = template.render(results=results)

            with open(report_file, "w") as f:
                f.write(html)

        elif format == "pdf":
            # Generate PDF report
            from weasyprint import HTML
            html = generate_html_report(results)
            HTML(string=html).write_pdf(report_file)

        console.print(f"Report saved to: {report_file}")
        return {
            "format": format,
            "path": str(report_file)
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return None

def get_html_template() -> str:
    """Get HTML template for report."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Sniffing Report</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .success { color: green; }
        .failure { color: red; }
        .warning { color: orange; }
    </style>
</head>
<body>
    <h1>Sniffing Report</h1>

    <h2>Overview</h2>
    <p>Status: <span class="{{ 'success' if results.status else 'failure' }}">
        {{ 'PASSED' if results.status else 'FAILED' }}
    </span></p>

    <h2>Results</h2>
    {% for result in results.results %}
    <h3>{{ result.domain }}</h3>
    <ul>
        {% for issue in result.issues %}
        <li>{{ issue.description }}</li>
        {% endfor %}
    </ul>
    {% endfor %}

    <h2>Recommendations</h2>
    <ul>
    {% for rec in results.analysis.recommendations %}
        <li>{{ rec }}</li>
    {% endfor %}
    </ul>
</body>
</html>
"""

def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate HTML report content."""
    from jinja2 import Template
    template = Template(get_html_template())
    return template.render(results=results)

def handle_results(
    results: Dict[str, Any],
    report: Dict[str, Any],
    args: argparse.Namespace
) -> int:
    """Handle sniffing results."""
    try:
        console = Console()

        # Print summary
        console.print("\n[bold blue]Results Summary[/bold blue]")

        if results["status"]:
            console.print("[bold green]✓ All checks passed[/bold green]")
            return 0

        # Get issues
        issues = []
        for result in results.get("results", []):
            issues.extend(result.get("issues", []))

        if not issues:
            return 0

        # Print issues
        console.print("\n[bold red]❌ Checks failed[/bold red]")
        console.print("The following issues were found:\n")

        # Group issues by domain
        issues_by_domain = {}
        for issue in issues:
            domain = issue.get("domain", "unknown")
            if domain not in issues_by_domain:
                issues_by_domain[domain] = []
            issues_by_domain[domain].append(issue)

        # Print issues
        for domain, domain_issues in issues_by_domain.items():
            console.print(f"\n[bold blue]{domain.upper()} Issues:[/bold blue]")
            for issue in domain_issues:
                console.print(f"  • {issue.get('description', 'Unknown issue')}")
                if issue.get("file"):
                    console.print(f"    File: {issue['file']}")
                if issue.get("location"):
                    console.print(f"    Location: {issue['location']}")
                if issue.get("severity"):
                    console.print(f"    Severity: {issue['severity']}")

        # Print compliance failures
        compliance = results.get("compliance", {})
        if not compliance.get("status", False):
            console.print("\n[bold yellow]⚠️ Compliance Requirements Not Met:[/bold yellow]")
            checks = compliance.get("checks", {})

            # Coverage failures
            coverage = checks.get("coverage", {})
            if not coverage.get("status", False):
                console.print("\n[bold blue]📊 Coverage Requirements:[/bold blue]")
                for failure in coverage.get("failures", []):
                    console.print(
                        f"  • {failure['domain']}: {failure['coverage']}% "
                        f"(required: {failure['threshold']}%)"
                    )

            # Security failures
            security = checks.get("security", {})
            if not security.get("status", False):
                console.print("\n[bold blue]🔒 Security Requirements:[/bold blue]")
                requirements = security.get("requirements", {})

                vulns = requirements.get("vulnerabilities", {})
                if not vulns.get("status", False):
                    console.print(
                        f"  • High severity vulnerabilities: {vulns.get('high_severity', 0)} "
                        "(required: 0)"
                    )
                    console.print(
                        f"  • Medium severity vulnerabilities: {vulns.get('medium_severity', 0)} "
                        "(maximum: 5)"
                    )

                compliance = requirements.get("compliance", {})
                if not compliance.get("status", False):
                    console.print(
                        f"  • Compliance score: {compliance.get('compliance_score', 0)}% "
                        "(required: 80%)"
                    )

                deps = requirements.get("dependencies", {})
                if not deps.get("status", False):
                    console.print(
                        f"  • Outdated dependencies: {deps.get('outdated_dependencies', 0)} "
                        "(maximum: 3)"
                    )
                    console.print(
                        f"  • Vulnerable dependencies: {deps.get('vulnerable_dependencies', 0)} "
                        "(required: 0)"
                    )

            # Documentation failures
            docs = checks.get("documentation", {})
            if not docs.get("status", False):
                console.print("\n[bold blue]📝 Documentation Requirements:[/bold blue]")
                console.print(
                    f"  • Documentation coverage: {docs.get('coverage', 0)}% "
                    "(required: 95%)"
                )

        # Print recommendations
        recommendations = results.get("analysis", {}).get("recommendations", [])
        if recommendations:
            console.print("\n[bold green]💡 Recommendations:[/bold green]")
            for recommendation in recommendations:
                console.print(f"  • {recommendation}")

        # Print report location
        console.print(f"\nDetailed report saved to: {report['path']}")

        return 1

    except Exception as e:
        logger.error(f"Error handling results: {e}")
        return 1

if __name__ == "__main__":
    # Parse arguments
    args = parse_args()

    # Run sniffing
    exit_code = asyncio.run(run_sniffing(args))
    sys.exit(exit_code)

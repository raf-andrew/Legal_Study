"""
Management script for sniffing infrastructure.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("manage")

class SniffingManager:
    """Manager for sniffing infrastructure."""

    def __init__(self):
        self.console = Console()
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration."""
        try:
            config_file = Path("sniffing/config/sniffing_config.yaml")
            if not config_file.exists():
                raise FileNotFoundError("Configuration file not found")

            with open(config_file, "r") as f:
                return yaml.safe_load(f)

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

    def run(self, args: argparse.Namespace) -> None:
        """Run management command."""
        try:
            if args.command == "start":
                self._start(args)
            elif args.command == "stop":
                self._stop(args)
            elif args.command == "status":
                self._status(args)
            elif args.command == "clean":
                self._clean(args)
            elif args.command == "configure":
                self._configure(args)
            elif args.command == "report":
                self._report(args)
            elif args.command == "test":
                self._test(args)
            elif args.command == "install":
                self._install(args)
            elif args.command == "update":
                self._update(args)
            elif args.command == "backup":
                self._backup(args)
            elif args.command == "restore":
                self._restore(args)
            else:
                self.console.print("[red]Unknown command[/red]")

        except Exception as e:
            logger.error(f"Error running command: {e}")
            sys.exit(1)

    def _start(self, args: argparse.Namespace) -> None:
        """Start sniffing infrastructure."""
        try:
            mode = args.mode or "production"
            if mode == "production":
                os.system("python scripts/run_prod.py")
            elif mode == "development":
                os.system("python scripts/run_dev.py")
            else:
                self.console.print(f"[red]Unknown mode: {mode}[/red]")

        except Exception as e:
            logger.error(f"Error starting infrastructure: {e}")
            raise

    def _stop(self, args: argparse.Namespace) -> None:
        """Stop sniffing infrastructure."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any(x in str(proc.cmdline()) for x in ['run_prod.py', 'run_dev.py']):
                        proc.terminate()
                        self.console.print(f"[green]Stopped process {proc.pid}[/green]")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except Exception as e:
            logger.error(f"Error stopping infrastructure: {e}")
            raise

    def _status(self, args: argparse.Namespace) -> None:
        """Check infrastructure status."""
        try:
            import psutil
            running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any(x in str(proc.cmdline()) for x in ['run_prod.py', 'run_dev.py']):
                        running = True
                        mode = "production" if 'run_prod.py' in str(proc.cmdline()) else "development"
                        self.console.print(f"[green]Running in {mode} mode (PID: {proc.pid})[/green]")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if not running:
                self.console.print("[yellow]Not running[/yellow]")

        except Exception as e:
            logger.error(f"Error checking status: {e}")
            raise

    def _clean(self, args: argparse.Namespace) -> None:
        """Clean infrastructure files."""
        try:
            # Clean reports
            if args.reports:
                import shutil
                report_dir = Path(self.config["mcp"]["report_path"])
                if report_dir.exists():
                    shutil.rmtree(report_dir)
                    self.console.print("[green]Cleaned reports[/green]")

            # Clean metrics
            if args.metrics:
                metrics_dir = Path(self.config["mcp"]["metrics_path"])
                if metrics_dir.exists():
                    shutil.rmtree(metrics_dir)
                    self.console.print("[green]Cleaned metrics[/green]")

            # Clean logs
            if args.logs:
                log_files = [
                    "sniffing.log",
                    "dev.log",
                    "production.log",
                    "full_sniffing.log"
                ]
                for log_file in log_files:
                    path = Path(log_file)
                    if path.exists():
                        path.unlink()
                self.console.print("[green]Cleaned logs[/green]")

            # Clean cache
            if args.cache:
                cache_dirs = [
                    "__pycache__",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".coverage"
                ]
                for cache_dir in cache_dirs:
                    for path in Path(".").rglob(cache_dir):
                        if path.is_dir():
                            shutil.rmtree(path)
                self.console.print("[green]Cleaned cache[/green]")

        except Exception as e:
            logger.error(f"Error cleaning files: {e}")
            raise

    def _configure(self, args: argparse.Namespace) -> None:
        """Configure infrastructure."""
        try:
            if args.show:
                # Show current configuration
                self.console.print(yaml.dump(self.config, default_flow_style=False))
            elif args.edit:
                # Open configuration in editor
                editor = os.environ.get("EDITOR", "vim")
                os.system(f"{editor} sniffing/config/sniffing_config.yaml")
            elif args.reset:
                # Reset configuration to defaults
                import shutil
                config_file = Path("sniffing/config/sniffing_config.yaml")
                default_config = Path("sniffing/config/sniffing_config.yaml.default")
                if default_config.exists():
                    shutil.copy2(default_config, config_file)
                    self.console.print("[green]Reset configuration to defaults[/green]")
                else:
                    self.console.print("[red]Default configuration not found[/red]")

        except Exception as e:
            logger.error(f"Error configuring infrastructure: {e}")
            raise

    def _report(self, args: argparse.Namespace) -> None:
        """Generate infrastructure report."""
        try:
            if args.type == "summary":
                os.system("python scripts/run_full_sniffing.py")
            elif args.type == "security":
                os.system("python scripts/run_sniffing.py --domains security")
            elif args.type == "browser":
                os.system("python scripts/run_sniffing.py --domains browser")
            elif args.type == "functional":
                os.system("python scripts/run_sniffing.py --domains functional")
            elif args.type == "unit":
                os.system("python scripts/run_sniffing.py --domains unit")
            elif args.type == "documentation":
                os.system("python scripts/run_sniffing.py --domains documentation")
            else:
                self.console.print(f"[red]Unknown report type: {args.type}[/red]")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _test(self, args: argparse.Namespace) -> None:
        """Run infrastructure tests."""
        try:
            test_cmd = ["pytest"]

            # Add coverage
            if args.coverage:
                test_cmd.extend(["--cov=sniffing", "--cov-report=html"])

            # Add verbosity
            if args.verbose:
                test_cmd.append("-v")

            # Add specific test file or directory
            if args.target:
                test_cmd.append(args.target)

            # Run tests
            os.system(" ".join(test_cmd))

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            raise

    def _install(self, args: argparse.Namespace) -> None:
        """Install infrastructure components."""
        try:
            # Install dependencies
            if args.dependencies:
                os.system("pip install -r requirements.txt")
                self.console.print("[green]Installed dependencies[/green]")

            # Install Git hooks
            if args.hooks:
                os.system("python scripts/install_git_hooks.py")
                self.console.print("[green]Installed Git hooks[/green]")

            # Install AI models
            if args.models:
                model_dir = Path("models")
                model_dir.mkdir(exist_ok=True)
                os.system("python -c 'from transformers import AutoModel; AutoModel.from_pretrained(\"microsoft/codebert-base\", cache_dir=\"models\")'")
                self.console.print("[green]Installed AI models[/green]")

        except Exception as e:
            logger.error(f"Error installing components: {e}")
            raise

    def _update(self, args: argparse.Namespace) -> None:
        """Update infrastructure components."""
        try:
            # Update dependencies
            if args.dependencies:
                os.system("pip install -r requirements.txt --upgrade")
                self.console.print("[green]Updated dependencies[/green]")

            # Update AI models
            if args.models:
                model_dir = Path("models")
                if model_dir.exists():
                    import shutil
                    shutil.rmtree(model_dir)
                model_dir.mkdir()
                os.system("python -c 'from transformers import AutoModel; AutoModel.from_pretrained(\"microsoft/codebert-base\", cache_dir=\"models\", force_download=True)'")
                self.console.print("[green]Updated AI models[/green]")

        except Exception as e:
            logger.error(f"Error updating components: {e}")
            raise

    def _backup(self, args: argparse.Namespace) -> None:
        """Backup infrastructure data."""
        try:
            import datetime
            import shutil

            # Create backup directory
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            # Create timestamped backup directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"backup_{timestamp}"
            backup_path.mkdir()

            # Backup configuration
            shutil.copy2("sniffing/config/sniffing_config.yaml", backup_path)

            # Backup reports
            report_dir = Path(self.config["mcp"]["report_path"])
            if report_dir.exists():
                shutil.copytree(report_dir, backup_path / "reports")

            # Backup metrics
            metrics_dir = Path(self.config["mcp"]["metrics_path"])
            if metrics_dir.exists():
                shutil.copytree(metrics_dir, backup_path / "metrics")

            # Create archive
            shutil.make_archive(str(backup_path), "zip", backup_path)
            shutil.rmtree(backup_path)

            self.console.print(f"[green]Created backup: backup_{timestamp}.zip[/green]")

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def _restore(self, args: argparse.Namespace) -> None:
        """Restore infrastructure data."""
        try:
            import shutil

            # Check backup file
            backup_file = Path(args.backup)
            if not backup_file.exists():
                self.console.print(f"[red]Backup file not found: {backup_file}[/red]")
                return

            # Create temporary directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup
                shutil.unpack_archive(str(backup_file), temp_dir)

                # Restore configuration
                config_file = Path(temp_dir) / "sniffing_config.yaml"
                if config_file.exists():
                    shutil.copy2(config_file, "sniffing/config/sniffing_config.yaml")

                # Restore reports
                report_dir = Path(temp_dir) / "reports"
                if report_dir.exists():
                    target_dir = Path(self.config["mcp"]["report_path"])
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(report_dir, target_dir)

                # Restore metrics
                metrics_dir = Path(temp_dir) / "metrics"
                if metrics_dir.exists():
                    target_dir = Path(self.config["mcp"]["metrics_path"])
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.copytree(metrics_dir, target_dir)

            self.console.print(f"[green]Restored backup: {backup_file}[/green]")

        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            raise

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage sniffing infrastructure")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start infrastructure")
    start_parser.add_argument("--mode", choices=["production", "development"], help="Mode to run in")

    # Stop command
    subparsers.add_parser("stop", help="Stop infrastructure")

    # Status command
    subparsers.add_parser("status", help="Check infrastructure status")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean infrastructure files")
    clean_parser.add_argument("--reports", action="store_true", help="Clean reports")
    clean_parser.add_argument("--metrics", action="store_true", help="Clean metrics")
    clean_parser.add_argument("--logs", action="store_true", help="Clean logs")
    clean_parser.add_argument("--cache", action="store_true", help="Clean cache")

    # Configure command
    configure_parser = subparsers.add_parser("configure", help="Configure infrastructure")
    configure_parser.add_argument("--show", action="store_true", help="Show current configuration")
    configure_parser.add_argument("--edit", action="store_true", help="Edit configuration")
    configure_parser.add_argument("--reset", action="store_true", help="Reset configuration to defaults")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate infrastructure report")
    report_parser.add_argument("--type", choices=["summary", "security", "browser", "functional", "unit", "documentation"], required=True, help="Report type")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run infrastructure tests")
    test_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    test_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("--target", help="Test file or directory")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install infrastructure components")
    install_parser.add_argument("--dependencies", action="store_true", help="Install dependencies")
    install_parser.add_argument("--hooks", action="store_true", help="Install Git hooks")
    install_parser.add_argument("--models", action="store_true", help="Install AI models")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update infrastructure components")
    update_parser.add_argument("--dependencies", action="store_true", help="Update dependencies")
    update_parser.add_argument("--models", action="store_true", help="Update AI models")

    # Backup command
    subparsers.add_parser("backup", help="Backup infrastructure data")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore infrastructure data")
    restore_parser.add_argument("backup", help="Backup file to restore")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    manager = SniffingManager()
    manager.run(args)

if __name__ == "__main__":
    main()

"""
Script to run sniffing infrastructure in benchmark mode.
"""
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set

import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table

from sniffing.mcp.server.mcp_server import MCPServer
from sniffing.mcp.orchestration.sniffing_loop import SniffingLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("benchmark.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("benchmark_mode")

class BenchmarkRunner:
    """Runner for benchmark mode."""

    def __init__(self):
        self.console = Console()
        self.config = self._load_config()
        self.mcp_server = MCPServer(self.config)
        self.sniffing_loop = SniffingLoop(self.config.get("sniffing", {}))
        self.benchmark_files = self._get_benchmark_files()
        self.stats: Dict[str, Any] = {
            "files_processed": 0,
            "total_time": 0,
            "avg_time_per_file": 0,
            "max_time_per_file": 0,
            "min_time_per_file": float("inf"),
            "cpu_usage": [],
            "memory_usage": [],
            "domains": {
                "security": {"time": 0, "files": 0},
                "browser": {"time": 0, "files": 0},
                "functional": {"time": 0, "files": 0},
                "unit": {"time": 0, "files": 0},
                "documentation": {"time": 0, "files": 0}
            }
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration."""
        try:
            import yaml
            config_file = Path("sniffing/config/sniffing_config.yaml")
            if not config_file.exists():
                raise FileNotFoundError("Configuration file not found")

            with open(config_file, "r") as f:
                return yaml.safe_load(f)

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

    def _get_benchmark_files(self) -> Set[Path]:
        """Get benchmark files."""
        try:
            files = set()
            workspace = Path(".")

            # Get file patterns from config
            patterns = self.config.get("sniffing", {}).get("file_patterns", ["*.py", "*.js", "*.ts"])
            ignore_patterns = self.config.get("sniffing", {}).get("ignore_patterns", ["**/tests/**", "**/vendor/**"])

            # Find files
            for pattern in patterns:
                files.update(workspace.glob(f"**/{pattern}"))

            # Filter ignored files
            for pattern in ignore_patterns:
                files = {f for f in files if not any(part.match(pattern) for part in f.parents)}

            return files

        except Exception as e:
            logger.error(f"Error getting benchmark files: {e}")
            return set()

    async def run(self) -> None:
        """Run benchmark mode."""
        try:
            self.console.print("[bold green]Starting benchmark mode...[/bold green]")

            # Start services
            await self.mcp_server.start()
            await self.sniffing_loop.start()

            # Run benchmarks
            await self._run_benchmarks()

            # Print results
            self._print_results()

            # Stop services
            await self.stop()

        except Exception as e:
            logger.error(f"Error running benchmark mode: {e}")
            await self.stop()
            sys.exit(1)

    async def stop(self) -> None:
        """Stop benchmark mode."""
        try:
            self.console.print("[bold red]Stopping benchmark mode...[/bold red]")

            # Stop services
            await self.sniffing_loop.stop()
            await self.mcp_server.stop()

        except Exception as e:
            logger.error(f"Error stopping benchmark mode: {e}")

    async def _run_benchmarks(self) -> None:
        """Run benchmarks."""
        try:
            with Live(self._generate_stats_table(), refresh_per_second=1) as live:
                # Run each file
                start_time = time.time()
                for file in self.benchmark_files:
                    self.console.print(f"\nBenchmarking {file}...")
                    self.stats["files_processed"] += 1

                    # Run sniffing
                    file_start_time = time.time()
                    await self.sniffing_loop.add_file(str(file))
                    while not self.sniffing_loop.results_cache.get(str(file), {}).get("completed", False):
                        await asyncio.sleep(0.1)
                    file_time = time.time() - file_start_time

                    # Update timing stats
                    self._update_timing_stats(file, file_time)

                    # Update resource stats
                    self._update_resource_stats()

                    # Update display
                    live.update(self._generate_stats_table())

                # Update total time
                self.stats["total_time"] = time.time() - start_time

        except Exception as e:
            logger.error(f"Error running benchmarks: {e}")
            raise

    def _update_timing_stats(self, file: Path, time_taken: float) -> None:
        """Update timing statistics."""
        try:
            # Update overall timing stats
            self.stats["avg_time_per_file"] = (
                (self.stats["avg_time_per_file"] * (self.stats["files_processed"] - 1) + time_taken)
                / self.stats["files_processed"]
            )
            self.stats["max_time_per_file"] = max(self.stats["max_time_per_file"], time_taken)
            self.stats["min_time_per_file"] = min(self.stats["min_time_per_file"], time_taken)

            # Update domain stats
            result = self.sniffing_loop.results_cache.get(str(file), {}).get("result", {})
            for domain in result.get("domains", []):
                if domain in self.stats["domains"]:
                    self.stats["domains"][domain]["time"] += time_taken
                    self.stats["domains"][domain]["files"] += 1

        except Exception as e:
            logger.error(f"Error updating timing stats: {e}")

    def _update_resource_stats(self) -> None:
        """Update resource statistics."""
        try:
            process = psutil.Process()

            # Update CPU usage
            self.stats["cpu_usage"].append(process.cpu_percent())

            # Update memory usage (MB)
            self.stats["memory_usage"].append(process.memory_info().rss / 1024 / 1024)

        except Exception as e:
            logger.error(f"Error updating resource stats: {e}")

    def _generate_stats_table(self) -> Table:
        """Generate statistics table."""
        table = Table(title="Benchmark Status")

        # Add columns
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        # Add timing stats
        table.add_row("Files Processed", str(self.stats["files_processed"]))
        table.add_row("Total Time", f"{self.stats['total_time']:.2f}s")
        table.add_row("Average Time/File", f"{self.stats['avg_time_per_file']:.2f}s")
        table.add_row("Max Time/File", f"{self.stats['max_time_per_file']:.2f}s")
        if self.stats["min_time_per_file"] != float("inf"):
            table.add_row("Min Time/File", f"{self.stats['min_time_per_file']:.2f}s")

        # Add resource stats
        if self.stats["cpu_usage"]:
            table.add_row("CPU Usage (avg)", f"{sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage']):.1f}%")
        if self.stats["memory_usage"]:
            table.add_row("Memory Usage (avg)", f"{sum(self.stats['memory_usage']) / len(self.stats['memory_usage']):.1f}MB")

        # Add domain stats
        table.add_section()
        for domain, stats in self.stats["domains"].items():
            if stats["files"] > 0:
                avg_time = stats["time"] / stats["files"]
                table.add_row(
                    f"{domain.capitalize()}",
                    f"Files: {stats['files']}, Avg Time: {avg_time:.2f}s"
                )

        return table

    def _print_results(self) -> None:
        """Print benchmark results."""
        try:
            # Create results table
            table = Table(title="Benchmark Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            # Add timing stats
            table.add_row("Total Files", str(self.stats["files_processed"]))
            table.add_row("Total Time", f"{self.stats['total_time']:.2f}s")
            table.add_row("Average Time/File", f"{self.stats['avg_time_per_file']:.2f}s")
            table.add_row("Max Time/File", f"{self.stats['max_time_per_file']:.2f}s")
            if self.stats["min_time_per_file"] != float("inf"):
                table.add_row("Min Time/File", f"{self.stats['min_time_per_file']:.2f}s")

            # Add resource stats
            if self.stats["cpu_usage"]:
                cpu_avg = sum(self.stats["cpu_usage"]) / len(self.stats["cpu_usage"])
                cpu_max = max(self.stats["cpu_usage"])
                table.add_row("CPU Usage (avg)", f"{cpu_avg:.1f}%")
                table.add_row("CPU Usage (max)", f"{cpu_max:.1f}%")

            if self.stats["memory_usage"]:
                mem_avg = sum(self.stats["memory_usage"]) / len(self.stats["memory_usage"])
                mem_max = max(self.stats["memory_usage"])
                table.add_row("Memory Usage (avg)", f"{mem_avg:.1f}MB")
                table.add_row("Memory Usage (max)", f"{mem_max:.1f}MB")

            # Add domain stats
            table.add_section()
            for domain, stats in self.stats["domains"].items():
                if stats["files"] > 0:
                    avg_time = stats["time"] / stats["files"]
                    table.add_row(
                        f"{domain.capitalize()} Summary",
                        f"Files: {stats['files']}, Total Time: {stats['time']:.2f}s, Avg Time: {avg_time:.2f}s"
                    )

            # Print table
            self.console.print("\n")
            self.console.print(table)

            # Save results
            self._save_results()

            # Print log location
            self.console.print("\nBenchmark log available at: benchmark.log")

        except Exception as e:
            logger.error(f"Error printing results: {e}")

    def _save_results(self) -> None:
        """Save benchmark results."""
        try:
            import json
            from datetime import datetime

            # Create results directory
            results_dir = Path("benchmark_results")
            results_dir.mkdir(exist_ok=True)

            # Create results file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"benchmark_{timestamp}.json"

            # Save results
            with open(results_file, "w") as f:
                json.dump(self.stats, f, indent=2)

            self.console.print(f"\nBenchmark results saved to: {results_file}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main() -> None:
    """Main entry point."""
    runner = BenchmarkRunner()
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())

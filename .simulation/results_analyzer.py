import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class ResultsAnalyzer:
    def __init__(self, results_dir=".simulation/results"):
        self.results_dir = Path(results_dir)

    def analyze_results(self, scenario_name=None):
        """Analyze simulation results for a specific scenario or all scenarios"""
        results = self._load_results(scenario_name)
        if not results:
            logger.warning("No results found for analysis")
            return None

        analysis = {
            "summary": self._generate_summary(results),
            "performance": self._analyze_performance(results),
            "reliability": self._analyze_reliability(results)
        }

        self._save_analysis(analysis, scenario_name)
        self._generate_visualizations(analysis, scenario_name)

        return analysis

    def _load_results(self, scenario_name=None):
        """Load simulation results from JSON files"""
        results = []
        pattern = f"{scenario_name}_*.json" if scenario_name else "*.json"

        for file in self.results_dir.glob(pattern):
            with open(file, 'r') as f:
                results.append(json.load(f))

        return results

    def _generate_summary(self, results):
        """Generate summary statistics from results"""
        total_iterations = sum(len(r["results"]) for r in results)
        successful_iterations = sum(
            sum(1 for r in iteration["results"] if r["status"] == "success")
            for iteration in results
        )

        return {
            "total_simulations": len(results),
            "total_iterations": total_iterations,
            "successful_iterations": successful_iterations,
            "success_rate": (successful_iterations / total_iterations) * 100 if total_iterations > 0 else 0
        }

    def _analyze_performance(self, results):
        """Analyze performance metrics from results"""
        durations = [r["duration"] for r in results]

        return {
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0
        }

    def _analyze_reliability(self, results):
        """Analyze reliability metrics from results"""
        step_results = {}
        for result in results:
            for iteration in result["results"]:
                for step_name, step_data in iteration.get("steps", {}).items():
                    if step_name not in step_results:
                        step_results[step_name] = {"success": 0, "total": 0}
                    step_results[step_name]["total"] += 1
                    if step_data["status"] == "success":
                        step_results[step_name]["success"] += 1

        reliability = {}
        for step, counts in step_results.items():
            reliability[step] = (counts["success"] / counts["total"]) * 100

        return reliability

    def _save_analysis(self, analysis, scenario_name):
        """Save analysis results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{scenario_name or 'all'}_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)
        logger.info(f"Analysis saved to {filepath}")

    def _generate_visualizations(self, analysis, scenario_name):
        """Generate visualization of analysis results"""
        # Performance visualization
        plt.figure(figsize=(10, 6))
        plt.bar(["Average", "Min", "Max"],
                [analysis["performance"]["average_duration"],
                 analysis["performance"]["min_duration"],
                 analysis["performance"]["max_duration"]])
        plt.title(f"Performance Metrics - {scenario_name or 'All Scenarios'}")
        plt.ylabel("Duration (seconds)")
        plt.savefig(self.results_dir / f"performance_{scenario_name or 'all'}.png")
        plt.close()

        # Reliability visualization
        plt.figure(figsize=(10, 6))
        steps = list(analysis["reliability"].keys())
        success_rates = list(analysis["reliability"].values())
        plt.bar(steps, success_rates)
        plt.title(f"Step Reliability - {scenario_name or 'All Scenarios'}")
        plt.ylabel("Success Rate (%)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.results_dir / f"reliability_{scenario_name or 'all'}.png")
        plt.close()

def main():
    analyzer = ResultsAnalyzer()
    analyzer.analyze_results()

if __name__ == "__main__":
    main()

"""
Benchmarking Framework
=======================
Automates running both Flood Fill and Incremental A* algorithms across
multiple maze configurations and collecting performance metrics.

The benchmark:
  1. Loads maze files from the `mazes/` directory (or uses a default).
  2. Runs each algorithm `n_runs` times per maze.
  3. Collects all RunMetrics.
  4. Exports results to CSV and JSON.
  5. Prints a comparative summary table.

Note: This module is designed for OFFLINE analysis (post-run) because the
mms simulator is an external process.  During live simulation, metrics are
collected by the algorithm itself and saved for later batch analysis.

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from evaluation.metrics import RunMetrics, MetricsCollector


class BenchmarkRunner:
    """
    Orchestrates multi-run, multi-maze benchmarking.

    For live simulator benchmarking, the workflow is:
      1. Run the simulator with FloodFill → save metrics JSON.
      2. Run the simulator with IncrementalAStar → save metrics JSON.
      3. Call `load_from_json()` on both result files.
      4. Call `run_analysis()` to produce comparisons.

    Attributes:
        collector (MetricsCollector): Aggregated metrics store.
        output_dir (Path): Directory for CSV/JSON output.
    """

    def __init__(self, output_dir: str | Path = "logs") -> None:
        """
        Initialise the benchmark runner.

        Args:
            output_dir: Directory where results will be saved.
        """
        self.collector = MetricsCollector()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Data ingestion
    # ------------------------------------------------------------------

    def add_run(self, metrics: RunMetrics) -> None:
        """
        Add a single run's metrics to the benchmark.

        Args:
            metrics: Completed RunMetrics instance.
        """
        self.collector.add(metrics)

    def load_from_json(self, path: str | Path) -> int:
        """
        Load run metrics from a previously saved JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Number of runs loaded.
        """
        path = Path(path)
        if not path.exists():
            print(f"[Benchmark] File not found: {path}")
            return 0

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for entry in data:
            m = RunMetrics(**{k: v for k, v in entry.items()
                              if k in RunMetrics.__dataclass_fields__})
            self.collector.add(m)
            count += 1

        print(f"[Benchmark] Loaded {count} runs from {path}")
        return count

    # ------------------------------------------------------------------
    # Analysis and output
    # ------------------------------------------------------------------

    def run_analysis(self) -> None:
        """
        Run full analysis: print comparison table, save CSV and JSON.
        """
        if len(self.collector) == 0:
            print("[Benchmark] No data to analyse.")
            return

        print(f"\n[Benchmark] Analysing {len(self.collector)} total runs...")

        # Per-algorithm summaries
        for algo in self.collector.algorithms():
            runs = self.collector.runs_for(algo)
            print(f"\n--- {algo} ({len(runs)} runs) ---")
            stats = self.collector.statistics(algo)
            for metric, s in stats.items():
                if metric in ("phase1", "phase2", "phase3"):
                    print(f"  {metric}:")
                    for p_metric, p_s in s.items():
                        print(
                            f"    {p_metric:<23}: mean={p_s['mean']:.3f}  "
                            f"median={p_s['median']:.3f}  "
                            f"stdev={p_s['stdev']:.3f}  "
                            f"[{p_s['min']} .. {p_s['max']}]"
                        )
                else:
                    print(
                        f"  {metric:<25}: mean={s['mean']:.3f}  "
                        f"median={s['median']:.3f}  "
                        f"stdev={s['stdev']:.3f}  "
                        f"[{s['min']} .. {s['max']}]"
                    )

        # Comparative table
        self.collector.print_comparison_table()

        # Export
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.collector.save_csv(self.output_dir / f"benchmark_{ts}.csv")
        self.collector.save_json(self.output_dir / f"benchmark_{ts}.json")

    def generate_summary_report(self) -> str:
        """
        Generate a Markdown-formatted summary report.

        Returns:
            Markdown string with full benchmark results.
        """
        lines: list[str] = []
        lines.append("# Micromouse Benchmark Report")
        lines.append(f"\n*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        lines.append(f"**Total runs:** {len(self.collector)}\n")

        for algo in self.collector.algorithms():
            lines.append(f"\n## {algo}")
            runs = self.collector.runs_for(algo)
            lines.append(f"\nRuns completed: {len(runs)}")
            lines.append(f"Goal success rate: "
                         f"{sum(1 for r in runs if r.reached_goal)}/{len(runs)}\n")

            stats = self.collector.statistics(algo)
            lines.append("### Whole-run Metrics")
            lines.append("| Metric | Mean | Median | StdDev | Min | Max |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for metric, s in stats.items():
                if metric not in ("phase1", "phase2", "phase3"):
                    lines.append(
                        f"| {metric} | {s['mean']} | {s['median']} | "
                        f"{s['stdev']} | {s['min']} | {s['max']} |"
                    )
            
            for phase in ("phase1", "phase2", "phase3"):
                if phase in stats:
                    lines.append(f"\n### {phase.capitalize()} Metrics")
                    lines.append("| Metric | Mean | Median | StdDev | Min | Max |")
                    lines.append("| --- | --- | --- | --- | --- | --- |")
                    for p_metric, p_s in stats[phase].items():
                        lines.append(
                            f"| {p_metric} | {p_s['mean']} | {p_s['median']} | "
                            f"{p_s['stdev']} | {p_s['min']} | {p_s['max']} |"
                        )

        return "\n".join(lines)

    def save_summary_report(self, path: Optional[str | Path] = None) -> None:
        """
        Save the Markdown summary report to a file.

        Args:
            path: Output path (default: logs/benchmark_report.md).
        """
        if path is None:
            path = self.output_dir / "benchmark_report.md"
        path = Path(path)
        report = self.generate_summary_report()
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[Benchmark] Report saved to {path}")


# ---------------------------------------------------------------------------
# Convenience function for quick analysis of saved JSON files
# ---------------------------------------------------------------------------

def analyse_saved_results(
    *json_paths: str | Path,
    output_dir: str | Path = "logs",
) -> None:
    """
    Load result JSON files and run full analysis.

    Example usage::

        analyse_saved_results(
            "logs/flood_fill_results.json",
            "logs/astar_results.json",
        )

    Args:
        *json_paths: One or more paths to result JSON files.
        output_dir: Directory for output files.
    """
    runner = BenchmarkRunner(output_dir=output_dir)
    for p in json_paths:
        runner.load_from_json(p)
    runner.run_analysis()
    runner.save_summary_report()

"""
Offline Analysis Script
========================
Run this script AFTER collecting benchmark data from the simulator.

It loads the JSON result files saved by main.py, runs statistical
analysis, generates plots, and saves a Markdown report.

Usage:
    python analyse_results.py
    python analyse_results.py --output-dir my_results

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evaluation.benchmark import BenchmarkRunner
from evaluation.plotting import MazePlotter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline analysis of Micromouse benchmark results",
    )
    parser.add_argument(
        "--logs-dir",
        default="logs",
        help="Directory containing JSON result files (default: logs/)",
    )
    parser.add_argument(
        "--output-dir",
        default="logs",
        help="Directory for output files and plots (default: logs/)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logs_dir = Path(args.logs_dir)
    output_dir = Path(args.output_dir)

    print("=" * 60)
    print(" Micromouse Benchmark Analysis")
    print("=" * 60)

    runner = BenchmarkRunner(output_dir=output_dir)

    # --- Load live-run results (logs/live/) ---
    live_dir = logs_dir / "live"
    live_files = sorted(live_dir.glob("*_results.json")) if live_dir.is_dir() else []

    if live_files:
        print(f"\n[Live runs]  {live_dir}")
        for json_file in live_files:
            count = runner.load_from_json(json_file)
            print(f"  Loaded {count:>4} run(s) from: {json_file.name}")
    else:
        print(f"\n[Live runs]  No result files found in '{live_dir}'.")
        print("  Run the mms simulator and results will appear here.")

    # --- Load batch-run results (logs/batch/) ---
    batch_dir = logs_dir / "batch"
    batch_files = sorted(batch_dir.glob("*_results.json")) if batch_dir.is_dir() else []

    if batch_files:
        print(f"\n[Batch runs] {batch_dir}")
        for json_file in batch_files:
            count = runner.load_from_json(json_file)
            print(f"  Loaded {count:>4} run(s) from: {json_file.name}")
    else:
        print(f"\n[Batch runs] No result files found in '{batch_dir}'.")
        print("  Run: python main.py --algorithm flood_fill --batch-dir mazes")

    if len(runner.collector) == 0:
        print("\n[ERROR] No valid run data found in either directory.")
        return

    print(f"\n  Total runs loaded: {len(runner.collector)}")

    # Run analysis and print comparison table
    runner.run_analysis()

    # Save Markdown report
    runner.save_summary_report(output_dir / "benchmark_report.md")

    # Generate plots (requires matplotlib)
    try:
        plotter = MazePlotter(
            runner.collector,
            output_dir=output_dir / "plots",
        )
        plotter.generate_all()
        print(f"\n[Plots] All plots saved to: {output_dir / 'plots'}")
    except Exception as e:
        print(f"\n[WARNING] Could not generate plots: {e}")
        print("Install matplotlib and numpy: pip install matplotlib numpy")

    print("\n" + "=" * 60)
    print(" Analysis complete!")
    print("=" * 60)



if __name__ == "__main__":
    main()

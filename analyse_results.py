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
    parser.add_argument(
        "--maze-typology", "-t",
        default=None,
        metavar="TYPOLOGY",
        help=(
            "Filter analysis to runs with this maze typology label only "
            "(e.g. 'long_corridors', 'dead_end_heavy'). "
            "Omit to include all typologies."
        ),
    )
    parser.add_argument(
        "--list-typologies",
        action="store_true",
        help="List all maze typology labels present in the log files, then exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logs_dir = Path(args.logs_dir)
    output_dir = Path(args.output_dir)

    print("=" * 60)
    print(" Micromouse Benchmark Analysis")
    print("=" * 60)

    # Load all JSON result files from the logs directory
    runner = BenchmarkRunner(output_dir=output_dir)
    json_files = list(logs_dir.glob("*_results.json"))

    if not json_files:
        print(f"\n[WARNING] No result JSON files found in '{logs_dir}'.")
        print("Run the simulator first, then re-run this script.")
        print("Expected files: floodfill_results.json, incrementalastar_results.json")
        return

    for json_file in sorted(json_files):
        count = runner.load_from_json(json_file)
        print(f"  Loaded {count} runs from: {json_file.name}")

    if len(runner.collector) == 0:
        print("\n[ERROR] No valid run data found.")
        return

    # --list-typologies: just enumerate and exit
    if args.list_typologies:
        typologies = runner.typologies()
        print(f"\nMaze typologies found ({len(typologies)}):")
        for t in typologies:
            runs = runner.runs_for_typology(t)
            print(f"  {t!r:30s}  ({len(runs)} runs)")
        return

    # Optional typology filter
    if args.maze_typology is not None:
        filtered = runner.runs_for_typology(args.maze_typology)
        if not filtered:
            available = runner.typologies()
            print(
                f"\n[WARNING] No runs found for typology {args.maze_typology!r}. "
                f"Available: {available}"
            )
            return
        # Re-populate the runner with only the matching runs
        from evaluation.metrics import MetricsCollector
        filtered_collector = MetricsCollector()
        for r in filtered:
            filtered_collector.add(r)
        runner.collector = filtered_collector
        print(
            f"\n[Filter] Restricted to typology={args.maze_typology!r} "
            f"({len(filtered)} runs)"
        )

    # Run analysis and print comparison table
    runner.run_analysis()

    # Save Markdown report
    report_name = (
        f"benchmark_report_{args.maze_typology}.md"
        if args.maze_typology
        else "benchmark_report.md"
    )
    runner.save_summary_report(output_dir / report_name)

    # Generate plots (requires matplotlib)
    try:
        plotter = MazePlotter(
            runner.collector,
            output_dir=output_dir / "plots",
        )
        # Build visit count maps from path histories (if available)
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

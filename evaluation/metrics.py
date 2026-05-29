"""
Metrics Collection Module
==========================
Defines structured metric data types and collection utilities for
benchmarking Micromouse algorithms.

Metrics tracked per run:
  - visited_cells:       Number of distinct cells visited during exploration
  - final_path_length:  Length of the shortest known path from start to goal
  - total_moves:        Total number of forward movement commands issued
  - total_turns:        Total number of 90-degree turn commands issued
  - elapsed_seconds:    Wall-clock time for the run
  - replan_count:       Number of path replanning events
  - new_walls_found:    Number of previously unknown walls discovered
  - exploration_ratio:  Fraction of total maze cells that were visited

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class RunMetrics:
    """
    Holds all performance metrics for a single algorithm run.

    Attributes:
        algorithm (str): Name of the algorithm ('FloodFill' or 'IncrementalAStar').
        maze_name (str): Identifier for the maze used.
        run_index (int): Run number (for repeated experiments).
        visited_cells (int): Distinct cells entered by the robot.
        total_cells (int): Total cells in the maze.
        final_path_length (int): Length of final solution path.
        total_moves (int): Total forward movement commands.
        total_turns (int): Total turn commands.
        elapsed_seconds (float): Wall-clock time.
        replan_count (int): Number of replanning events.
        new_walls_found (int): Number of new wall discoveries.
        reached_goal (bool): Whether the goal was reached.
        notes (str): Optional freeform notes.
    """
    algorithm: str = ""
    maze_name: str = ""
    run_index: int = 0
    visited_cells: int = 0
    total_cells: int = 256  # 16x16
    final_path_length: int = 0
    total_moves: int = 0
    total_turns: int = 0
    elapsed_seconds: float = 0.0
    replan_count: int = 0
    new_walls_found: int = 0
    reached_goal: bool = False
    notes: str = ""

    @property
    def exploration_ratio(self) -> float:
        """Fraction of maze cells that were visited (0.0 – 1.0)."""
        if self.total_cells == 0:
            return 0.0
        return self.visited_cells / self.total_cells

    @property
    def turn_ratio(self) -> float:
        """Ratio of turns to total moves (higher = more winding path)."""
        total = self.total_moves + self.total_turns
        if total == 0:
            return 0.0
        return self.total_turns / total

    @property
    def moves_per_cell(self) -> float:
        """Average forward moves per distinct cell visited."""
        if self.visited_cells == 0:
            return 0.0
        return self.total_moves / self.visited_cells

    def to_dict(self) -> dict:
        """Return a flat dictionary representation of all metrics."""
        d = asdict(self)
        d["exploration_ratio"] = round(self.exploration_ratio, 4)
        d["turn_ratio"] = round(self.turn_ratio, 4)
        d["moves_per_cell"] = round(self.moves_per_cell, 4)
        return d

    def summary_str(self) -> str:
        """Return a formatted summary string."""
        return (
            f"[{self.algorithm}] Maze: {self.maze_name} | Run: {self.run_index}\n"
            f"  Goal reached:      {self.reached_goal}\n"
            f"  Visited cells:     {self.visited_cells}/{self.total_cells} "
            f"({self.exploration_ratio:.1%})\n"
            f"  Final path len:    {self.final_path_length}\n"
            f"  Total moves:       {self.total_moves}\n"
            f"  Total turns:       {self.total_turns}\n"
            f"  Elapsed:           {self.elapsed_seconds:.4f}s\n"
            f"  Replan count:      {self.replan_count}\n"
            f"  New walls found:   {self.new_walls_found}\n"
        )


class MetricsCollector:
    """
    Aggregates RunMetrics from multiple runs for statistical analysis.

    Supports:
      - Appending individual run results
      - Computing per-algorithm statistics
      - Exporting to CSV and JSON
      - Printing comparative tables
    """

    def __init__(self) -> None:
        self._runs: list[RunMetrics] = []

    def add(self, metrics: RunMetrics) -> None:
        """
        Append a completed run's metrics to the collection.

        Args:
            metrics: RunMetrics instance from a completed run.
        """
        self._runs.append(metrics)

    def runs_for(self, algorithm: Optional[str] = None) -> list[RunMetrics]:
        """
        Filter runs by algorithm name.

        Args:
            algorithm: Algorithm name to filter by, or None for all runs.

        Returns:
            List of matching RunMetrics.
        """
        if algorithm is None:
            return list(self._runs)
        return [r for r in self._runs if r.algorithm == algorithm]

    def algorithms(self) -> list[str]:
        """Return sorted list of unique algorithm names in the collection."""
        return sorted({r.algorithm for r in self._runs})

    def statistics(self, algorithm: Optional[str] = None) -> dict:
        """
        Compute descriptive statistics for numeric fields.

        Args:
            algorithm: Filter by algorithm, or None for all.

        Returns:
            Dict mapping field_name -> {mean, median, stdev, min, max}.
        """
        runs = self.runs_for(algorithm)
        if not runs:
            return {}

        numeric_fields = [
            "visited_cells", "final_path_length", "total_moves",
            "total_turns", "elapsed_seconds", "replan_count",
            "new_walls_found",
        ]
        stats: dict[str, dict] = {}
        for field_name in numeric_fields:
            values = [getattr(r, field_name) for r in runs]
            if len(values) < 2:
                stats[field_name] = {
                    "mean": values[0] if values else 0,
                    "median": values[0] if values else 0,
                    "stdev": 0.0,
                    "min": values[0] if values else 0,
                    "max": values[0] if values else 0,
                    "n": len(values),
                }
            else:
                stats[field_name] = {
                    "mean": round(statistics.mean(values), 4),
                    "median": round(statistics.median(values), 4),
                    "stdev": round(statistics.stdev(values), 4),
                    "min": min(values),
                    "max": max(values),
                    "n": len(values),
                }
        return stats

    def save_csv(self, path: str | Path) -> None:
        """
        Save all runs to a CSV file.

        Args:
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not self._runs:
            return
        fieldnames = list(self._runs[0].to_dict().keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for run in self._runs:
                writer.writerow(run.to_dict())
        print(f"[MetricsCollector] Saved {len(self._runs)} runs to {path}")

    def save_json(self, path: str | Path) -> None:
        """
        Save all runs to a JSON file.

        Args:
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self._runs]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[MetricsCollector] Saved {len(self._runs)} runs to {path}")

    def print_comparison_table(self) -> None:
        """
        Print a formatted comparison table of all algorithms' statistics.
        """
        algos = self.algorithms()
        if not algos:
            print("No data collected yet.")
            return

        fields = [
            "visited_cells", "final_path_length",
            "total_moves", "total_turns",
            "elapsed_seconds", "replan_count",
        ]
        col_w = 20
        header = f"{'':<25}" + "".join(f"{a:>{col_w}}" for a in algos)
        print("\n" + "=" * (25 + col_w * len(algos)))
        print("  ALGORITHM COMPARISON  ")
        print("=" * (25 + col_w * len(algos)))
        print(header)
        print("-" * (25 + col_w * len(algos)))

        for f in fields:
            row = f"{f:<25}"
            for algo in algos:
                stats = self.statistics(algo)
                if f in stats:
                    mean_val = stats[f]["mean"]
                    stdev_val = stats[f]["stdev"]
                    cell = f"{mean_val:.2f} ±{stdev_val:.2f}"
                else:
                    cell = "N/A"
                row += f"{cell:>{col_w}}"
            print(row)

        print("=" * (25 + col_w * len(algos)) + "\n")

    def __len__(self) -> int:
        """Return total number of runs collected."""
        return len(self._runs)

    def __repr__(self) -> str:
        return f"MetricsCollector({len(self._runs)} runs, algorithms={self.algorithms()})"

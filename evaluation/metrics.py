"""
Metrics Collection Module
==========================
Defines structured metric data types and collection utilities for
benchmarking Micromouse algorithms.

Per-run data is now segmented into three phases:
  - Phase 1 (Exploration):         Start (0,0) → Goal centre
  - Phase 2 (Reverse Exploration): Goal centre → Start (0,0)
  - Phase 3 (Speed Run):           Start (0,0) → Goal centre, optimal path only

Flat totals (total_moves, total_turns, elapsed_seconds, etc.) are also stored
at the top level for backward compatibility with existing JSON logs.

Metrics tracked per phase (PhaseMetrics):
  - moves:          Forward movement commands issued
  - turns:          90-degree turn commands issued
  - cells_visited:  New distinct cells entered during this phase
  - time_seconds:   Wall-clock time for the phase
  - walls_found:    New wall discoveries
  - replan_count:   Path replanning events
  - reached_target: Whether the phase target was reached

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


# ---------------------------------------------------------------------------
# Per-phase metrics
# ---------------------------------------------------------------------------

@dataclass
class PhaseMetrics:
    """
    Holds performance metrics for a single phase of the 3-phase run.

    Attributes:
        phase_name (str):       Human-readable label, e.g. 'Exploration'.
        moves (int):            Forward movement commands during this phase.
        turns (int):            90° turn commands during this phase.
        cells_visited (int):    New distinct cells entered during this phase.
        time_seconds (float):   Wall-clock seconds spent in this phase.
        walls_found (int):      New wall observations recorded.
        replan_count (int):     Number of path replanning events.
        reached_target (bool):  Whether this phase's target was reached.
    """
    phase_name: str = ""
    moves: int = 0
    turns: int = 0
    cells_visited: int = 0
    time_seconds: float = 0.0
    walls_found: int = 0
    replan_count: int = 0
    reached_target: bool = False

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def total_commands(self) -> int:
        """Total number of commands issued in this phase (moves + turns)."""
        return self.moves + self.turns

    @property
    def turn_ratio(self) -> float:
        """Fraction of all commands that were turns (0.0 – 1.0)."""
        total = self.total_commands
        if total == 0:
            return 0.0
        return self.turns / total

    @property
    def moves_per_cell(self) -> float:
        """Average forward moves per new cell visited."""
        if self.cells_visited == 0:
            return 0.0
        return self.moves / self.cells_visited

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a flat dictionary representation of this phase's metrics."""
        d = asdict(self)
        d["total_commands"] = self.total_commands
        d["turn_ratio"] = round(self.turn_ratio, 4)
        d["moves_per_cell"] = round(self.moves_per_cell, 4)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PhaseMetrics":
        """Reconstruct a PhaseMetrics from a previously serialised dict."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid_keys})

    def summary_str(self, indent: str = "    ") -> str:
        """Return a compact human-readable summary of this phase."""
        status = "✓" if self.reached_target else "✗"
        return (
            f"{indent}[{self.phase_name}] {status}\n"
            f"{indent}  Moves:          {self.moves}\n"
            f"{indent}  Turns:          {self.turns}\n"
            f"{indent}  Cells visited:  {self.cells_visited}\n"
            f"{indent}  Time:           {self.time_seconds:.4f}s\n"
            f"{indent}  Walls found:    {self.walls_found}\n"
            f"{indent}  Replans:        {self.replan_count}\n"
        )


# ---------------------------------------------------------------------------
# Full-run metrics (3-phase)
# ---------------------------------------------------------------------------

@dataclass
class RunMetrics:
    """
    Holds all performance metrics for a single 3-phase algorithm run.

    The three PhaseMetrics fields (phase1, phase2, phase3) capture
    per-segment data.  All flat total_* fields are also stored for
    backward compatibility with existing JSON logs and analysis code.

    Attributes:
        algorithm (str):          Algorithm name ('FloodFill' or 'IncrementalAStar').
        algorithm_version (str):  Version tag for the algorithm implementation
                                  (e.g. 'v1', 'v2', 'weighted'). Allows comparing
                                  different revisions of the same algorithm.
        maze_name (str):          Identifier for the maze used.
        maze_typology (str):      Qualitative maze category (e.g. 'long_corridors',
                                  'dead_end_heavy', 'multiple_paths', 'unknown').
        run_index (int):          Run number for repeated experiments.
        visited_cells (int):      Total distinct cells entered across all phases.
        total_cells (int):        Total cells in the maze (e.g. 256 for 16×16).
        final_path_length (int):  Length of the speed-run path (Phase 3).
        total_moves (int):        Sum of moves across all three phases.
        total_turns (int):        Sum of turns across all three phases.
        elapsed_seconds (float):  Total wall-clock time for all three phases.
        replan_count (int):       Total replanning events across phases 1 & 2.
        new_walls_found (int):    Total new wall discoveries across phases 1 & 2.
        reached_goal (bool):      True if Phase 3 (speed run) reached the goal.
        notes (str):              Optional freeform notes.
        phase1 (PhaseMetrics):    Phase 1 — Exploration (start → centre).
        phase2 (PhaseMetrics):    Phase 2 — Reverse exploration (centre → start).
        phase3 (PhaseMetrics):    Phase 3 — Speed run (start → centre, optimal).
    """
    algorithm: str = ""
    algorithm_version: str = "v1"   # e.g. 'v1', 'v2', 'weighted' — for cross-version comparison
    maze_name: str = ""
    maze_typology: str = "unknown"  # e.g. 'long_corridors', 'dead_end_heavy', 'multiple_paths'
    run_index: int = 0
    visited_cells: int = 0
    total_cells: int = 256          # 16×16
    final_path_length: int = 0
    total_moves: int = 0
    total_turns: int = 0
    elapsed_seconds: float = 0.0
    replan_count: int = 0
    new_walls_found: int = 0
    reached_goal: bool = False
    notes: str = ""

    # Per-phase breakdown — default to empty PhaseMetrics instances
    phase1: PhaseMetrics = field(default_factory=lambda: PhaseMetrics(phase_name="Exploration"))
    phase2: PhaseMetrics = field(default_factory=lambda: PhaseMetrics(phase_name="ReverseExploration"))
    phase3: PhaseMetrics = field(default_factory=lambda: PhaseMetrics(phase_name="SpeedRun"))

    def __post_init__(self) -> None:
        """
        Ensure nested phase attributes are proper PhaseMetrics instances.
        This provides defensive initialization against dictionary unpacking (**kwargs).
        """
        if isinstance(self.phase1, dict):
            self.phase1 = PhaseMetrics.from_dict(self.phase1)
        if isinstance(self.phase2, dict):
            self.phase2 = PhaseMetrics.from_dict(self.phase2)
        if isinstance(self.phase3, dict):
            self.phase3 = PhaseMetrics.from_dict(self.phase3)

    # ------------------------------------------------------------------
    # Derived properties (whole-run)
    # ------------------------------------------------------------------

    @property
    def exploration_ratio(self) -> float:
        """Fraction of maze cells that were visited (0.0 – 1.0)."""
        if self.total_cells == 0:
            return 0.0
        return self.visited_cells / self.total_cells

    @property
    def turn_ratio(self) -> float:
        """Ratio of turns to total commands (higher = more winding route)."""
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

    @property
    def speedrun_efficiency(self) -> float:
        """
        Efficiency of Phase 3 vs. exploration phases.

        Compares Phase 3 move count against Phase 1 + Phase 2 combined.
        Values < 1.0 indicate the speed run is more efficient.
        Returns 0.0 if exploration produced no moves.
        """
        exploration_moves = self.phase1.moves + self.phase2.moves
        if exploration_moves == 0:
            return 0.0
        return self.phase3.moves / exploration_moves

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Return a dictionary representation including nested phase data.

        The top-level keys remain compatible with the original flat schema.
        Phase breakdowns are nested under 'phase1', 'phase2', 'phase3'.
        """
        d: dict = {
            "algorithm": self.algorithm,
            "algorithm_version": self.algorithm_version,
            "maze_name": self.maze_name,
            "maze_typology": self.maze_typology,
            "run_index": self.run_index,
            "visited_cells": self.visited_cells,
            "total_cells": self.total_cells,
            "final_path_length": self.final_path_length,
            "total_moves": self.total_moves,
            "total_turns": self.total_turns,
            "elapsed_seconds": self.elapsed_seconds,
            "replan_count": self.replan_count,
            "new_walls_found": self.new_walls_found,
            "reached_goal": self.reached_goal,
            "notes": self.notes,
            # Derived whole-run values
            "exploration_ratio": round(self.exploration_ratio, 4),
            "turn_ratio": round(self.turn_ratio, 4),
            "moves_per_cell": round(self.moves_per_cell, 4),
            "speedrun_efficiency": round(self.speedrun_efficiency, 4),
            # Per-phase breakdown
            "phase1": self.phase1.to_dict(),
            "phase2": self.phase2.to_dict(),
            "phase3": self.phase3.to_dict(),
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "RunMetrics":
        """
        Reconstruct a RunMetrics from a previously serialised dictionary.
        
        Delegates nested conversion to __post_init__ for robust initialization.
        """
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs: dict = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**kwargs)

    def summary_str(self) -> str:
        """Return a detailed multi-phase summary string."""
        sep = "-" * 60
        return (
            f"\n{sep}\n"
            f"[{self.algorithm}]  v{self.algorithm_version}  Maze: {self.maze_name}  |  Run: {self.run_index}\n"
            f"  Typology: {self.maze_typology}\n"
            f"{sep}\n"
            f"  Goal reached:        {self.reached_goal}\n"
            f"  Total visited cells: {self.visited_cells}/{self.total_cells} "
            f"({self.exploration_ratio:.1%})\n"
            f"  Total moves:         {self.total_moves}\n"
            f"  Total turns:         {self.total_turns}\n"
            f"  Total elapsed:       {self.elapsed_seconds:.4f}s\n"
            f"  Walls found:         {self.new_walls_found}\n"
            f"  Replans:             {self.replan_count}\n"
            f"  Speed-run eff.:      {self.speedrun_efficiency:.3f}  "
            f"(phase3 moves / (phase1+phase2 moves))\n"
            f"\n  ── Phase Breakdown ──\n"
            f"{self.phase1.summary_str()}"
            f"{self.phase2.summary_str()}"
            f"{self.phase3.summary_str()}"
            f"{sep}\n"
        )


# ---------------------------------------------------------------------------
# Aggregator — unchanged public API, updated internals
# ---------------------------------------------------------------------------

class MetricsCollector:
    """
    Aggregates RunMetrics from multiple runs for statistical analysis.

    Supports:
      - Appending individual run results
      - Computing per-algorithm statistics (including per-phase stats)
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
        Compute descriptive statistics for numeric fields, including per-phase.

        Args:
            algorithm: Filter by algorithm, or None for all.

        Returns:
            Dict mapping field_name → {mean, median, stdev, min, max, n}.
            Phase fields are nested under 'phase1', 'phase2', 'phase3'.
        """
        runs = self.runs_for(algorithm)
        if not runs:
            return {}

        # Whole-run numeric fields
        whole_run_fields = [
            "visited_cells", "final_path_length", "total_moves",
            "total_turns", "elapsed_seconds", "replan_count",
            "new_walls_found",
        ]
        # Per-phase numeric fields
        phase_numeric_fields = [
            "moves", "turns", "cells_visited", "time_seconds",
            "walls_found", "replan_count",
        ]

        def _stat(values: list) -> dict:
            n = len(values)
            if n == 0:
                return {"mean": 0, "median": 0, "stdev": 0.0, "min": 0, "max": 0, "n": 0}
            if n == 1:
                return {
                    "mean": values[0], "median": values[0],
                    "stdev": 0.0, "min": values[0], "max": values[0], "n": 1,
                }
            return {
                "mean": round(statistics.mean(values), 4),
                "median": round(statistics.median(values), 4),
                "stdev": round(statistics.stdev(values), 4),
                "min": min(values),
                "max": max(values),
                "n": n,
            }

        stats: dict = {}

        # Whole-run stats
        for fname in whole_run_fields:
            values = [getattr(r, fname) for r in runs]
            stats[fname] = _stat(values)

        # Per-phase stats
        for phase_attr in ("phase1", "phase2", "phase3"):
            phase_stats: dict = {}
            for fname in phase_numeric_fields:
                values = [getattr(getattr(r, phase_attr), fname) for r in runs]
                phase_stats[fname] = _stat(values)
            stats[phase_attr] = phase_stats

        return stats

    @classmethod
    def load_json(cls, path: str | Path) -> "MetricsCollector":
        """
        Load a MetricsCollector from a previously saved JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            A new MetricsCollector populated with the loaded runs.
        """
        path = Path(path)
        collector = cls()
        if not path.exists():
            return collector

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            collector.add(RunMetrics.from_dict(entry))

        return collector

    @classmethod
    def load_csv(cls, path: str | Path) -> "MetricsCollector":
        """
        Load a MetricsCollector from a previously saved CSV file.
        Phase data encoded as JSON strings will be automatically parsed.

        Args:
            path: Path to the CSV file.

        Returns:
            A new MetricsCollector populated with the loaded runs.
        """
        path = Path(path)
        collector = cls()
        if not path.exists():
            return collector

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = {}
                for k, v in row.items():
                    if k in RunMetrics.__dataclass_fields__:
                        field_type = str(RunMetrics.__dataclass_fields__[k].type)
                        # Perform basic type casting from CSV strings
                        if "int" in field_type:
                            entry[k] = int(v)
                        elif "float" in field_type:
                            entry[k] = float(v)
                        elif "bool" in field_type:
                            entry[k] = v.lower() == "true"
                        elif "PhaseMetrics" in field_type:
                            try:
                                entry[k] = json.loads(v)
                            except json.JSONDecodeError:
                                entry[k] = v
                        else:
                            entry[k] = v
                collector.add(RunMetrics.from_dict(entry))

        return collector

    def save_csv(self, path: str | Path) -> None:
        """
        Save all runs to a CSV file (flat representation).

        Phase data is serialised as JSON strings in dedicated columns.

        Args:
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not self._runs:
            return

        # Build flat rows; encode phase sub-dicts as JSON strings for CSV
        rows = []
        for run in self._runs:
            d = run.to_dict()
            for pk in ("phase1", "phase2", "phase3"):
                d[pk] = json.dumps(d[pk])
            rows.append(d)

        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[MetricsCollector] Saved {len(self._runs)} runs to {path}")

    def save_json(self, path: str | Path) -> None:
        """
        Save all runs to a JSON file (nested format).

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
        Print a formatted comparison table of all algorithms' statistics,
        including per-phase move/time breakdowns.
        """
        algos = self.algorithms()
        if not algos:
            print("No data collected yet.")
            return

        col_w = 22
        width = 32 + col_w * len(algos)
        sep = "=" * width

        print(f"\n{sep}")
        print("  ALGORITHM COMPARISON (3-PHASE)")
        print(sep)

        # Header
        header = f"{'Metric':<32}" + "".join(f"{a:>{col_w}}" for a in algos)
        print(header)
        print("-" * width)

        whole_run_fields = [
            ("visited_cells",   "Visited Cells"),
            ("final_path_length", "Final Path Len"),
            ("total_moves",     "Total Moves"),
            ("total_turns",     "Total Turns"),
            ("elapsed_seconds", "Elapsed (s)"),
            ("replan_count",    "Replans"),
            ("new_walls_found", "Walls Found"),
        ]

        for fname, label in whole_run_fields:
            row = f"{label:<32}"
            for algo in algos:
                s = self.statistics(algo).get(fname, {})
                cell = f"{s.get('mean', 0):.2f} ±{s.get('stdev', 0):.2f}" if s else "N/A"
                row += f"{cell:>{col_w}}"
            print(row)

        # Per-phase sub-tables
        phase_map = [
            ("phase1", "Phase 1 — Exploration"),
            ("phase2", "Phase 2 — Reverse Explor."),
            ("phase3", "Phase 3 — Speed Run"),
        ]
        phase_fields = [
            ("moves",         "  Moves"),
            ("turns",         "  Turns"),
            ("cells_visited", "  Cells Visited"),
            ("time_seconds",  "  Time (s)"),
            ("walls_found",   "  Walls Found"),
            ("replan_count",  "  Replans"),
        ]

        for phase_attr, phase_label in phase_map:
            print(f"\n  {phase_label}")
            print("  " + "-" * (width - 2))
            for fname, label in phase_fields:
                row = f"{label:<32}"
                for algo in algos:
                    phase_stats = self.statistics(algo).get(phase_attr, {})
                    s = phase_stats.get(fname, {})
                    cell = f"{s.get('mean', 0):.2f} ±{s.get('stdev', 0):.2f}" if s else "N/A"
                    row += f"{cell:>{col_w}}"
                print(row)

        print(sep + "\n")

    def __len__(self) -> int:
        """Return total number of runs collected."""
        return len(self._runs)

    def __repr__(self) -> str:
        return f"MetricsCollector({len(self._runs)} runs, algorithms={self.algorithms()})"

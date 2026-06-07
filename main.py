"""
Micromouse Main Entry Point
============================
This is the script that the mms simulator invokes via stdin/stdout.

Configuration:
  Set ALGORITHM = "flood_fill" or ALGORITHM = "astar" to choose the solver.
  Set SAVE_METRICS = True to persist results to logs/.

Usage (from mms simulator):
  Command: python main.py
  OR:      python main.py --algorithm flood_fill
  OR:      python main.py --algorithm astar

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path regardless of cwd
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import core.simulator_api as api
from core.maze import MazeMap
from core.robot import RobotState
from algorithms.flood_fill import FloodFill
from algorithms.incremental_astar import IncrementalAStar
from evaluation.metrics import RunMetrics, PhaseMetrics
from core.mock_simulator import mock_simulator_context, parse_typology


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_ALGORITHM = "flood_fill"   # "flood_fill" | "astar"
SAVE_METRICS = True
LOGS_DIR = project_root / "logs"
MAZE_WIDTH = 16
MAZE_HEIGHT = 16


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Micromouse solver for mms simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --algorithm astar
  python main.py --algorithm flood_fill --maze-name custom_maze_1
""",
    )
    parser.add_argument(
        "--algorithm", "-a",
        choices=["flood_fill", "astar"],
        default=DEFAULT_ALGORITHM,
        help="Algorithm to use (default: %(default)s)",
    )
    parser.add_argument(
        "--maze-name", "-m",
        default="default",
        help="Identifier for the maze being solved (for metrics logging)",
    )
    parser.add_argument(
        "--run-index", "-r",
        type=int,
        default=0,
        help="Run index for repeated experiments (default: 0)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save metrics to disk",
    )
    parser.add_argument(
        "--weight",
        type=float,
        default=1.0,
        help="Heuristic weight for A* (>1.0 = weighted A*; default: 1.0)",
    )
    parser.add_argument(
        "--batch-dir",
        type=str,
        default=None,
        help=(
            "Path to a directory of .txt maze files for automated batch "
            "execution.  When set, the solver runs headlessly against each "
            "maze file in sequence (no mms GUI required).  Results are saved "
            "to logs/batch_results_<algorithm>.json."
        ),
    )
    # Parse only known args to avoid issues with simulator injecting flags
    args, _ = parser.parse_known_args()
    return args


# ---------------------------------------------------------------------------
# Initialisation helpers
# ---------------------------------------------------------------------------

def initialise_display(maze: MazeMap) -> None:
    """
    Set up the simulator display at the start of a run.
    Colors goal cells green and clears all text.
    """
    api.clear_all_color()
    api.clear_all_text()
    # Highlight goal cells
    for gx, gy in maze.goal_cells:
        if maze.in_bounds(gx, gy):
            api.set_color(gx, gy, "G")
            api.set_text(gx, gy, "G")
    # Mark start
    api.set_color(0, 0, "Y")
    api.set_text(0, 0, "S")


def query_maze_dimensions() -> tuple[int, int]:
    """
    Query and validate maze dimensions from the simulator.

    Returns:
        (width, height) tuple.
    """
    try:
        w = api.maze_width()
        h = api.maze_height()
        api.log_info(f"Maze dimensions: {w}x{h}")
        return w, h
    except Exception as e:
        api.log_error(f"Failed to query maze dimensions: {e}")
        return MAZE_WIDTH, MAZE_HEIGHT


# ---------------------------------------------------------------------------
# Metrics saving
# ---------------------------------------------------------------------------

def save_metrics(metrics: RunMetrics, logs_dir: Path) -> None:
    """
    Append metrics to the algorithm's JSON log file.

    Args:
        metrics: Completed run metrics.
        logs_dir: Directory for log files.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    safe_algo = metrics.algorithm.lower().replace(" ", "_")
    log_file = logs_dir / f"{safe_algo}_results.json"

    # Load existing data
    existing: list[dict] = []
    if log_file.exists():
        try:
            with open(log_file, encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    existing.append(metrics.to_dict())

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    api.log_info(f"Metrics saved to {log_file}")


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main entry point called by the mms simulator.

    Lifecycle:
      1. Parse arguments.
      2. Query maze dimensions.
      3. Initialise maze map and robot state.
      4. Set up simulator display.
      5. Run the chosen algorithm.
      6. Save metrics.
      7. Handle reset events for repeated runs.
    """
    args = parse_args()
    api.log_info(
        f"Starting Micromouse solver | Algorithm: {args.algorithm} | "
        f"Maze: {args.maze_name} | Run: {args.run_index}"
    )

    run_index = args.run_index

    while True:
        # ---- Setup ----
        width, height = query_maze_dimensions()

        # Adjust goal cells for non-16x16 mazes
        if width == 16 and height == 16:
            goal_cells = MazeMap.DEFAULT_GOALS_16
        else:
            # Single centre cell for non-standard mazes
            goal_cells = [(width // 2, height // 2)]

        maze = MazeMap(width=width, height=height, goal_cells=goal_cells)
        robot = RobotState(x=0, y=0)
        maze.cell(0, 0).visited = True

        initialise_display(maze)

        # ── Phase 1: Exploration (0,0) → centre ──────────────────────────
        phase1_m, solver1 = _run_phase(
            phase_label=_PHASE_EXPLORE,
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=list(original_goals),
            weight=args.weight,
        )

        if not phase1_m.reached_target:
            api.log_error("Phase 1 failed to reach the goal. Skipping phases 2 & 3.")
            # Still save partial metrics and wait for reset
            _finalise_run(args, run_index, maze, robot, width, height,
                          phase1_m, PhaseMetrics(phase_name="ReverseExploration"),
                          PhaseMetrics(phase_name="SpeedRun"),
                          final_path_length=0)
            run_index = _wait_for_reset(run_index)
            continue

        # ── Phase 2: Reverse Exploration centre → (0,0) ──────────────────
        phase2_m, solver2 = _run_phase(
            phase_label=_PHASE_REVERSE,
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=origin_goals,
            weight=args.weight,
        )

        if not phase2_m.reached_target:
            api.log_error("Phase 2 failed to return to origin. Skipping phase 3.")
            _finalise_run(args, run_index, maze, robot, width, height,
                          phase1_m, phase2_m,
                          PhaseMetrics(phase_name="SpeedRun"),
                          final_path_length=0)
            run_index = _wait_for_reset(run_index)
            continue

        # ── Phase 3: Speed Run (0,0) → centre ────────────────────────────
        phase3_m, path_length = _run_speed_phase(
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=list(original_goals),
        )

        # ── Consolidate & save ────────────────────────────────────────────
        _finalise_run(
            args, run_index, maze, robot, width, height,
            phase1_m, phase2_m, phase3_m,
            final_path_length=path_length,
        )

        run_index = _wait_for_reset(run_index)


# ---------------------------------------------------------------------------
# Helper: consolidate metrics and save
# ---------------------------------------------------------------------------

def _finalise_run(
    args: argparse.Namespace,
    run_index: int,
    maze: MazeMap,
    robot: RobotState,
    width: int,
    height: int,
    phase1_m: PhaseMetrics,
    phase2_m: PhaseMetrics,
    phase3_m: PhaseMetrics,
    final_path_length: int,
) -> None:
    """
    Build a consolidated RunMetrics from the three phase objects, print a
    summary, and optionally persist to the JSON log.
    """
    # Determine canonical algorithm name from completed solvers
    algo_name_map = {"flood_fill": "FloodFill", "astar": "IncrementalAStar"}
    algo_name = algo_name_map.get(args.algorithm, args.algorithm)

    snap_final = robot.snapshot()

    metrics = RunMetrics(
        algorithm=algo_name,
        maze_name=args.maze_name,
        maze_typology=getattr(args, "maze_typology", "example"),
        run_index=run_index,
        visited_cells=robot.unique_cells_visited(),
        total_cells=width * height,
        final_path_length=final_path_length,
        total_moves=snap_final["moves"],
        total_turns=snap_final["turns"],
        elapsed_seconds=round(
            phase1_m.time_seconds + phase2_m.time_seconds + phase3_m.time_seconds, 4
        ),
        replan_count=phase1_m.replan_count + phase2_m.replan_count,
        new_walls_found=phase1_m.walls_found + phase2_m.walls_found,
        reached_goal=phase3_m.reached_target,
        phase1=phase1_m,
        phase2=phase2_m,
        phase3=phase3_m,
    )

    # Print summary to stderr (visible in simulator log panel)
    sys.stderr.write(metrics.summary_str())

        # ---- Save metrics ----
        if not args.no_save:
            try:
                save_metrics(metrics, LOGS_DIR)
            except Exception as e:
                api.log_error(f"Could not save metrics: {e}")


# ---------------------------------------------------------------------------
# Helper: wait for simulator reset
# ---------------------------------------------------------------------------

def _wait_for_reset(run_index: int) -> int:
    """
    Block until the simulator sends a reset signal, then acknowledge it.

    Args:
        run_index: Current run counter.

    Returns:
        Incremented run index.
    """
    api.log_info("Run complete. Waiting for reset signal...")
    while True:
        if api.was_reset():
            api.ack_reset()
            run_index += 1
            api.log_info(f"Reset acknowledged. Starting run {run_index}...")
            return run_index
        time.sleep(0.1)


# ---------------------------------------------------------------------------
# Batch mode — headless automated execution
# ---------------------------------------------------------------------------

def save_batch_metrics(metrics: RunMetrics, logs_dir: Path) -> None:
    """
    Append metrics to the batch-specific JSON log file.

    Output goes to ``batch_results_<algorithm>.json`` — separate from the
    standard live-run log files so that batch and manual data never mix.

    Args:
        metrics:  Completed run metrics.
        logs_dir: Directory for log files.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    safe_algo = metrics.algorithm.lower().replace(" ", "_")
    log_file = logs_dir / f"batch_results_{safe_algo}.json"

    existing: list[dict] = []
    if log_file.exists():
        try:
            with open(log_file, encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    existing.append(metrics.to_dict())

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    sys.stderr.write(f"[BATCH] Metrics appended to {log_file}\n")


def _run_single_batch_maze(
    args: argparse.Namespace,
    maze_path: Path,
    run_index: int,
) -> RunMetrics | None:
    """
    Execute a full 3-phase run against a single maze file using the
    mock simulator.

    Args:
        args:       Parsed CLI arguments (algorithm, weight, etc.).
        maze_path:  Path to the ASCII maze file.
        run_index:  Ordinal index of this maze in the batch.

    Returns:
        Completed RunMetrics, or None on critical failure.
    """
    maze_name = maze_path.stem
    typology = parse_typology(maze_path.name)

    # Temporarily inject batch-specific attributes into args
    args.maze_name = maze_name
    args.maze_typology = typology

    sys.stderr.write(
        f"\n{'=' * 60}\n"
        f"[BATCH] Maze: {maze_path.name}  |  Typology: {typology}  "
        f"|  Algorithm: {args.algorithm}\n"
        f"{'=' * 60}\n"
    )

    with mock_simulator_context(maze_path) as sim:
        # ── Setup ────────────────────────────────────────────────
        width = sim.maze_width()
        height = sim.maze_height()

        if width == 16 and height == 16:
            original_goals = MazeMap.DEFAULT_GOALS_16
        else:
            original_goals = [(width // 2, height // 2)]

        origin_goals: list[tuple[int, int]] = [(0, 0)]

        maze = MazeMap(width=width, height=height, goal_cells=list(original_goals))
        robot = RobotState(x=0, y=0)
        maze.cell(0, 0).visited = True

        # ── Phase 1: Exploration ─────────────────────────────────
        phase1_m, _ = _run_phase(
            phase_label=_PHASE_EXPLORE,
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=list(original_goals),
            weight=args.weight,
        )

        if not phase1_m.reached_target:
            sys.stderr.write(
                f"[BATCH] Phase 1 FAILED for {maze_name} — skipping phases 2 & 3\n"
            )
            _finalise_run(
                args, run_index, maze, robot, width, height,
                phase1_m,
                PhaseMetrics(phase_name="ReverseExploration"),
                PhaseMetrics(phase_name="SpeedRun"),
                final_path_length=0,
            )
            return None

        # ── Phase 2: Reverse Exploration ─────────────────────────
        phase2_m, _ = _run_phase(
            phase_label=_PHASE_REVERSE,
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=origin_goals,
            weight=args.weight,
        )

        if not phase2_m.reached_target:
            sys.stderr.write(
                f"[BATCH] Phase 2 FAILED for {maze_name} — skipping phase 3\n"
            )
            _finalise_run(
                args, run_index, maze, robot, width, height,
                phase1_m, phase2_m,
                PhaseMetrics(phase_name="SpeedRun"),
                final_path_length=0,
            )
            return None

        # ── Phase 3: Speed Run ───────────────────────────────────
        phase3_m, path_length = _run_speed_phase(
            algorithm=args.algorithm,
            maze=maze,
            robot=robot,
            goal_cells=list(original_goals),
        )

        # ── Consolidate ──────────────────────────────────────────
        algo_name_map = {"flood_fill": "FloodFill", "astar": "IncrementalAStar"}
        algo_name = algo_name_map.get(args.algorithm, args.algorithm)
        snap_final = robot.snapshot()

        metrics = RunMetrics(
            algorithm=algo_name,
            maze_name=maze_name,
            maze_typology=typology,
            run_index=run_index,
            visited_cells=robot.unique_cells_visited(),
            total_cells=width * height,
            final_path_length=path_length,
            total_moves=snap_final["moves"],
            total_turns=snap_final["turns"],
            elapsed_seconds=round(
                phase1_m.time_seconds + phase2_m.time_seconds
                + phase3_m.time_seconds, 4
            ),
            replan_count=phase1_m.replan_count + phase2_m.replan_count,
            new_walls_found=phase1_m.walls_found + phase2_m.walls_found,
            reached_goal=phase3_m.reached_target,
            phase1=phase1_m,
            phase2=phase2_m,
            phase3=phase3_m,
        )

        sys.stderr.write(metrics.summary_str())
        return metrics


def batch_main() -> None:
    """
    Automated batch entry point.

    Iterates over all ``.txt`` maze files in the ``--batch-dir`` directory,
    runs the full 3-phase state machine against each using the mock
    simulator, and saves results to ``logs/batch_results_<algorithm>.json``.

    No GUI, no manual interaction — fully headless.
    """
    args = parse_args()
    batch_dir = Path(args.batch_dir)

    if not batch_dir.is_dir():
        sys.stderr.write(f"[BATCH-ERROR] Directory not found: {batch_dir}\n")
        sys.exit(1)

    maze_files = sorted(batch_dir.glob("*.txt"))
    if not maze_files:
        sys.stderr.write(f"[BATCH-ERROR] No .txt maze files in: {batch_dir}\n")
        sys.exit(1)

    sys.stderr.write(
        f"\n{'#' * 60}\n"
        f"  BATCH MODE — {len(maze_files)} maze(s)  |  Algorithm: {args.algorithm}\n"
        f"{'#' * 60}\n"
    )

    results: list[RunMetrics] = []

    for idx, maze_path in enumerate(maze_files):
        metrics = _run_single_batch_maze(args, maze_path, run_index=idx)
        if metrics is not None:
            results.append(metrics)
            if not args.no_save:
                save_batch_metrics(metrics, LOGS_DIR)

    # Summary
    sys.stderr.write(
        f"\n{'#' * 60}\n"
        f"  BATCH COMPLETE — {len(results)}/{len(maze_files)} mazes solved\n"
        f"{'#' * 60}\n\n"
    )

    for m in results:
        sys.stderr.write(
            f"  {m.maze_name:<25} typology={m.maze_typology:<20} "
            f"goal={'YES' if m.reached_goal else 'NO ':>3}  "
            f"moves={m.total_moves:>5}  path={m.final_path_length:>3}\n"
        )
    sys.stderr.write("\n")


if __name__ == "__main__":
    args = parse_args()
    if args.batch_dir:
        batch_main()
    else:
        main()

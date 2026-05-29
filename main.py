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
from evaluation.metrics import RunMetrics


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

        # ---- Run algorithm ----
        start_time = time.perf_counter()
        reached_goal = False
        raw_metrics: dict = {}

        try:
            if args.algorithm == "flood_fill":
                solver = FloodFill(maze, robot)
                reached_goal = solver.run()
                raw_metrics = solver.get_metrics()

            elif args.algorithm == "astar":
                solver = IncrementalAStar(maze, robot, heuristic_weight=args.weight)
                reached_goal = solver.run()
                raw_metrics = solver.get_metrics()

        except Exception as exc:
            api.log_error(f"Algorithm exception: {exc}")
            import traceback
            traceback.print_exc(file=sys.stderr)

        elapsed = time.perf_counter() - start_time

        # ---- Build metrics ----
        algo_name = raw_metrics.get("algorithm", args.algorithm)
        metrics = RunMetrics(
            algorithm=algo_name,
            maze_name=args.maze_name,
            run_index=run_index,
            visited_cells=robot.unique_cells_visited(),
            total_cells=width * height,
            final_path_length=raw_metrics.get("path_length",
                maze.cell(robot.x, robot.y).distance
                if maze.in_bounds(robot.x, robot.y) else 0),
            total_moves=robot.move_count,
            total_turns=robot.turn_count,
            elapsed_seconds=round(elapsed, 4),
            replan_count=raw_metrics.get("replan_count", 0),
            new_walls_found=raw_metrics.get("new_walls_found", 0),
            reached_goal=reached_goal,
        )

        # ---- Print summary to stderr ----
        sys.stderr.write(metrics.summary_str())

        # ---- Save metrics ----
        if not args.no_save:
            try:
                save_metrics(metrics, LOGS_DIR)
            except Exception as e:
                api.log_error(f"Could not save metrics: {e}")

        # ---- Wait for reset or exit ----
        api.log_info("Run complete. Waiting for reset signal...")
        while True:
            if api.was_reset():
                api.ack_reset()
                run_index += 1
                api.log_info(f"Reset acknowledged. Starting run {run_index}...")
                break
            time.sleep(0.1)


if __name__ == "__main__":
    main()

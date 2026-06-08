"""
Micromouse Main Entry Point — 3-Phase State Machine
=====================================================
This is the script that the mms simulator invokes via stdin/stdout.

Execution Lifecycle (per run)
------------------------------
  Phase 1 — Exploration
      Robot starts at (0,0) and navigates to the goal centre (7,7).
      Full wall sensing and replanning occur.

  Phase 2 — Reverse Exploration
      Without a simulator reset, the robot drives itself back to (0,0),
      continuing to discover walls along a different route.

  Phase 3 — Speed Run
      Using the now-complete internal map, the robot executes the
      mathematically shortest path from (0,0) to (7,7) with zero
      sensing overhead.

Metrics are captured separately for each phase via RobotState.snapshot()
deltas and then consolidated into a single RunMetrics record.

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


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_ALGORITHM = "flood_fill"   # "flood_fill" | "astar"
SAVE_METRICS = True
LOGS_DIR = project_root / "logs"
MAZE_WIDTH = 16
MAZE_HEIGHT = 16

# State machine phase identifiers
_PHASE_EXPLORE  = "Phase1_Exploration"
_PHASE_REVERSE  = "Phase2_ReverseExploration"
_PHASE_SPEEDRUN = "Phase3_SpeedRun"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Micromouse solver for mms simulator (3-phase state machine)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --algorithm astar
  python main.py --algorithm flood_fill --maze-name custom_maze_1
  python main.py --maze-name open_arena --maze-typology multiple_paths
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
        "--maze-typology", "-t",
        default="unknown",
        help=(
            "Qualitative category for the maze being solved "
            "(e.g. 'long_corridors', 'dead_end_heavy', 'multiple_paths'). "
            "Stored in metrics for later grouped analysis (default: unknown)"
        ),
    )
    parser.add_argument(
        "--algorithm-version", "-v",
        default="v1",
        help=(
            "Version tag for the algorithm implementation being tested "
            "(e.g. 'v1', 'v2', 'weighted'). Allows comparing different revisions "
            "of the same algorithm in post-run analysis (default: v1)"
        ),
    )
    # Parse only known args to avoid issues with simulator injecting flags
    args, _ = parser.parse_known_args()
    return args


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def initialise_display(maze: MazeMap) -> None:
    """
    Set up the simulator display at the start of a run.
    Colors goal cells green and clears all text.
    """
    api.clear_all_color()
    api.clear_all_text()
    for gx, gy in maze.goal_cells:
        if maze.in_bounds(gx, gy):
            api.set_color(gx, gy, "G")
            api.set_text(gx, gy, "G")
    api.set_color(0, 0, "Y")
    api.set_text(0, 0, "S")


def update_phase_display(maze: MazeMap, phase_name: str) -> None:
    """
    Refresh the simulator display at the start of each phase.

    Colors the current goal cells and annotates the phase label.

    Args:
        maze:       The shared MazeMap (goal_cells already updated for this phase).
        phase_name: Human-readable phase label for the log.
    """
    api.clear_all_color()
    api.clear_all_text()
    # Highlight active goal cells
    for gx, gy in maze.goal_cells:
        if maze.in_bounds(gx, gy):
            api.set_color(gx, gy, "G")
            api.set_text(gx, gy, "TGT")
    api.log_info(f"[Display] Phase: {phase_name} | Targets: {maze.goal_cells}")


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
        metrics:  Completed run metrics.
        logs_dir: Directory for log files.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    safe_algo = metrics.algorithm.lower().replace(" ", "_")
    log_file = logs_dir / f"{safe_algo}_results.json"

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
# Phase helpers
# ---------------------------------------------------------------------------

def _make_solver(
    algorithm: str,
    maze: MazeMap,
    robot: RobotState,
    weight: float = 1.0,
) -> FloodFill | IncrementalAStar:
    """
    Instantiate a fresh solver for the given algorithm.

    A new instance is created per phase so that each phase's replan_count
    and new_walls_found counters start at zero.  The shared ``maze`` and
    ``robot`` objects carry over all state (wall map, position, heading).

    Args:
        algorithm: ``"flood_fill"`` or ``"astar"``.
        maze:      Shared MazeMap (goal_cells already set for this phase).
        robot:     Shared RobotState at the robot's current position.
        weight:    Heuristic weight for A* (ignored for FloodFill).

    Returns:
        A ready-to-run solver instance.
    """
    if algorithm == "flood_fill":
        return FloodFill(maze, robot)
    return IncrementalAStar(maze, robot, heuristic_weight=weight)


def _build_phase_metrics(
    phase_name: str,
    snap_before: dict,
    snap_after: dict,
    t_start: float,
    t_end: float,
    solver: FloodFill | IncrementalAStar,
    reached: bool,
) -> PhaseMetrics:
    """
    Compute a PhaseMetrics from before/after robot snapshots.

    Args:
        phase_name:   Label for the phase (e.g. 'Exploration').
        snap_before:  Robot snapshot taken immediately before the phase.
        snap_after:   Robot snapshot taken immediately after the phase.
        t_start:      perf_counter value at phase start.
        t_end:        perf_counter value at phase end.
        solver:       The solver that ran this phase (provides wall/replan counts).
        reached:      Whether the phase target was reached.

    Returns:
        Populated PhaseMetrics instance.
    """
    new_cells = len(snap_after["visited"] - snap_before["visited"])
    return PhaseMetrics(
        phase_name=phase_name,
        moves=snap_after["moves"] - snap_before["moves"],
        turns=snap_after["turns"] - snap_before["turns"],
        cells_visited=new_cells,
        time_seconds=round(t_end - t_start, 4),
        walls_found=getattr(solver, "new_walls_found", 0),
        replan_count=getattr(solver, "replan_count", 0),
        reached_target=reached,
    )


def _run_phase(
    phase_label: str,
    algorithm: str,
    maze: MazeMap,
    robot: RobotState,
    goal_cells: list[tuple[int, int]],
    weight: float,
) -> tuple[PhaseMetrics, FloodFill | IncrementalAStar]:
    """
    Execute a single exploration phase (Phase 1 or Phase 2).

    Updates ``maze.goal_cells``, creates a fresh solver, runs it, and
    returns a populated PhaseMetrics plus the solver instance (for
    downstream inspection).

    Args:
        phase_label: Human-readable name used in logs and PhaseMetrics.
        algorithm:   ``"flood_fill"`` or ``"astar"``.
        maze:        Shared MazeMap.
        robot:       Shared RobotState at current position.
        goal_cells:  Target cells for this phase.
        weight:      A* heuristic weight.

    Returns:
        (PhaseMetrics, solver) tuple.
    """
    maze.goal_cells = goal_cells
    update_phase_display(maze, phase_label)
    api.log_info(f"=== {phase_label} START | robot at ({robot.x},{robot.y}) "
                 f"| targets={goal_cells} ===")

    solver = _make_solver(algorithm, maze, robot, weight)
    snap_before = robot.snapshot()
    t0 = time.perf_counter()

    reached = False
    try:
        reached = solver.run()
    except Exception as exc:
        api.log_error(f"{phase_label} solver exception: {exc}")
        import traceback
        traceback.print_exc(file=sys.stderr)

    t1 = time.perf_counter()
    snap_after = robot.snapshot()

    phase_m = _build_phase_metrics(
        phase_name=phase_label,
        snap_before=snap_before,
        snap_after=snap_after,
        t_start=t0,
        t_end=t1,
        solver=solver,
        reached=reached,
    )
    api.log_info(
        f"=== {phase_label} END | reached={reached} | moves={phase_m.moves} "
        f"turns={phase_m.turns} time={phase_m.time_seconds:.3f}s ==="
    )
    return phase_m, solver


def _run_speed_phase(
    algorithm: str,
    maze: MazeMap,
    robot: RobotState,
    goal_cells: list[tuple[int, int]],
) -> tuple[PhaseMetrics, int]:
    """
    Execute Phase 3 — the speed run.

    Before running the fast path this function:
      1. Animates visited cells to show exploration coverage from Phases 1 & 2.
      2. Computes the shortest path (visited-only).
      3. Highlights the shortest path in bright green with step numbers.
      4. Executes the path without wall sensing.

    Args:
        algorithm:  ``"flood_fill"`` or ``"astar"``.
        maze:       Shared MazeMap (walls fully discovered by phases 1 & 2).
        robot:      Shared RobotState at the start cell (0,0).
        goal_cells: Original goal cells (the centre).

    Returns:
        (PhaseMetrics, path_length) tuple.
        path_length is 0 if no path could be found.
    """
    maze.goal_cells = goal_cells
    api.log_info(f"=== {_PHASE_SPEEDRUN} START | robot at ({robot.x},{robot.y}) ===")

    # ── Step 1: Animate visited cells (exploration coverage) ─────────
    _animate_visited_cells(maze)

    # ── Step 2: Compute shortest path (visited-only) ─────────────────
    if algorithm == "flood_fill":
        solver = FloodFill(maze, robot)
    else:
        solver = IncrementalAStar(maze, robot)

    path = solver.get_shortest_path(robot.x, robot.y, visited_only=True)
    path_length = max(0, len(path) - 1) if path else 0

    # ── Step 3: Highlight shortest path on the display ───────────────
    if path:
        _highlight_speed_path(maze, path)

    snap_before = robot.snapshot()
    t0 = time.perf_counter()
    reached = False

    if not path:
        api.log_error("Speed run: no path found — maze may be unsolvable!")
    else:
        api.log_info(f"Speed run path length: {path_length} steps")
        try:
            # Use the appropriate solver's run_fast method
            solver.run_fast(path)
            reached = maze.is_goal(robot.x, robot.y)
        except Exception as exc:
            api.log_error(f"Speed run exception: {exc}")
            import traceback
            traceback.print_exc(file=sys.stderr)

    t1 = time.perf_counter()
    snap_after = robot.snapshot()

    phase_m = PhaseMetrics(
        phase_name="SpeedRun",
        moves=snap_after["moves"] - snap_before["moves"],
        turns=snap_after["turns"] - snap_before["turns"],
        cells_visited=len(snap_after["visited"] - snap_before["visited"]),
        time_seconds=round(t1 - t0, 4),
        walls_found=0,   # no sensing in speed run
        replan_count=0,
        reached_target=reached,
    )
    api.log_info(
        f"=== {_PHASE_SPEEDRUN} END | reached={reached} | moves={phase_m.moves} "
        f"turns={phase_m.turns} time={phase_m.time_seconds:.3f}s ==="
    )
    return phase_m, path_length


# ---------------------------------------------------------------------------
# Phase 3 visualisation helpers
# ---------------------------------------------------------------------------

def _animate_visited_cells(maze: MazeMap) -> None:
    """
    Sweep through the maze and animate visited vs. unvisited cells.

    Visited cells are colored cyan row-by-row (bottom → top) with a
    brief delay between rows to create a visual "reveal" effect.
    Unvisited cells are dimmed to dark ash so the exploration coverage
    is immediately obvious at a glance.

    This runs at the Phase 2 → Phase 3 transition to give the user a
    clear picture of how much of the maze was explored before the
    speed run begins.

    Args:
        maze: The shared MazeMap after Phases 1 & 2.
    """
    api.log_info("Animating visited-cell coverage map...")
    api.clear_all_color()
    api.clear_all_text()

    visited_count = 0
    total_cells = maze.width * maze.height

    # Sweep bottom → top, left → right
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cells[x][y]
            if cell.visited:
                api.set_color(x, y, "C")   # cyan = visited
                api.set_text(x, y, "·")
                visited_count += 1
            else:
                api.clear_color(x, y)      # clear color = black background
                api.set_text(x, y, "?")
        # Brief delay between rows for animation effect
        time.sleep(0.02)

    # Highlight goal cells on top of the coverage map
    for gx, gy in maze.goal_cells:
        if maze.in_bounds(gx, gy):
            api.set_color(gx, gy, "G")
            api.set_text(gx, gy, "TGT")

    coverage_pct = (visited_count / total_cells * 100) if total_cells else 0
    api.log_info(
        f"Coverage: {visited_count}/{total_cells} cells visited "
        f"({coverage_pct:.1f}%)"
    )

    # Hold the coverage display briefly before showing the path
    time.sleep(0.3)


def _highlight_speed_path(
    maze: MazeMap,
    path: list[tuple[int, int]],
) -> None:
    """
    Highlight the computed shortest path on the simulator display.

    Each cell on the path is colored bright green with its step number
    annotated, creating a clear visual of the optimal route.
    The start cell is labeled "S" and the final cell is labeled "G".

    After highlighting, a brief pause lets the user inspect the path
    before the robot begins executing it.

    Args:
        maze: The shared MazeMap.
        path: Ordered list of (x, y) from start → goal.
    """
    api.log_info(f"Highlighting speed-run path ({len(path) - 1} steps)...")

    # First dim the background: keep visited=cyan, unvisited=black
    # but reduce visited to dark cyan so the path pops
    for col in maze.cells:
        for cell in col:
            if cell.visited:
                api.set_color(cell.x, cell.y, "c")  # dark cyan = visited bg
                api.set_text(cell.x, cell.y, "")
            else:
                api.clear_color(cell.x, cell.y)     # clear color = black background
                api.set_text(cell.x, cell.y, "")

    # Animate the path cell-by-cell
    for i, (x, y) in enumerate(path):
        api.set_color(x, y, "G")   # bright green = shortest path

        if i == 0:
            api.set_text(x, y, "S")
        elif i == len(path) - 1:
            api.set_text(x, y, "G")
        else:
            api.set_text(x, y, str(i))

        # Tiny delay per cell for a drawing animation
        time.sleep(0.015)

    # Hold so the user can see the full path before execution
    time.sleep(0.5)


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main entry point called by the mms simulator.

    Lifecycle per simulation run:
      1. Parse arguments & query maze dimensions.
      2. Initialise MazeMap and RobotState.
      3. Phase 1 — Exploration: (0,0) → goal centre.
      4. Phase 2 — Reverse:     goal centre → (0,0).
      5. Phase 3 — Speed Run:   (0,0) → goal centre (optimal, no sensing).
      6. Consolidate metrics across all phases.
      7. Save metrics to JSON log.
      8. Wait for simulator reset signal for the next run.
    """
    args = parse_args()
    api.log_info(
        f"Starting Micromouse solver (3-Phase) | Algorithm: {args.algorithm} "
        f"({args.algorithm_version}) | Maze: {args.maze_name} | "
        f"Typology: {args.maze_typology} | Run: {args.run_index}"
    )

    run_index = args.run_index

    while True:
        # ── Setup ────────────────────────────────────────────────────────
        width, height = query_maze_dimensions()

        if width == 16 and height == 16:
            original_goals = MazeMap.DEFAULT_GOALS_16
        else:
            original_goals = [(width // 2, height // 2)]

        origin_goals: list[tuple[int, int]] = [(0, 0)]

        maze  = MazeMap(width=width, height=height, goal_cells=list(original_goals))
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
                          final_path_length=0,
                          maze_typology=args.maze_typology,
                          algorithm_version=args.algorithm_version)
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
                          final_path_length=0,
                          maze_typology=args.maze_typology,
                          algorithm_version=args.algorithm_version)
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
            maze_typology=args.maze_typology,
            algorithm_version=args.algorithm_version,
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
    maze_typology: str = "unknown",
    algorithm_version: str = "v1",
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
        algorithm_version=algorithm_version,
        maze_name=args.maze_name,
        maze_typology=maze_typology,
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
    api.get_stat("score")
    # Save to JSON log
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


if __name__ == "__main__":
    main()

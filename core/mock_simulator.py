"""
Mock Simulator for Headless Batch Execution
=============================================
Provides a pure-Python replacement for the mms simulator's stdin/stdout
protocol.  Instead of communicating with an external C++ GUI application,
this module reads a maze from a standard ASCII ``.txt`` file and answers
wall/movement queries against an in-memory truth grid.

This enables fully automated, headless batch runs at near-instant CPU
speed — no GUI, no manual interaction, no process spawning.

Architecture
------------
``MockSimulator`` holds the *truth* wall grid (parsed from the file) and
a lightweight robot state (position + heading).  When activated as a
context manager, it monkey-patches every function in ``core.simulator_api``
so that the existing ``main.py`` orchestration, ``FloodFill``, and
``IncrementalAStar`` solvers work **unchanged**.

Simplifications vs mms
----------------------
While functionally perfect for our 90-degree pathfinding algorithms, this
mock simulator takes a few shortcuts compared to the real C++ mms engine:
1. **No Diagonal/Half-Step Physics**: Commands like ``turn_right_45()`` are
   acknowledged but ignored.
2. **No Long-Range Sensors**: ``wall_front(distance)`` ignores the distance
   parameter and only checks the immediately adjacent cell.
3. **No Display/GUI**: All ``set_color()`` and ``set_text()`` calls are
   completely ignored to maximize execution speed.
4. **Fatal Crash Handling**: Driving into a wall immediately returns
   ``"crash"`` rather than visually bumping and continuing.

Maze File Format
----------------
The mms ASCII format uses a 2W+1 × 2H+1 character grid::

    +---+---+
    |       |      ← row 1 (top)
    +   +---+
    |   |   |      ← row 0 (bottom)
    +---+---+

- ``+`` at every intersection
- ``---`` or ``   `` between horizontal posts  → north/south walls
- ``|`` or `` `` between vertical posts        → east/west walls

Coordinate convention (matching mms):
  - (0, 0) is the **bottom-left** cell
  - x increases rightward, y increases upward

Typology Parsing
-----------------
Filenames follow the pattern ``[number]_[typology].txt``.
``parse_typology("3_dead_end_heavy.txt")`` → ``"dead_end_heavy"``.
If the pattern doesn't match, ``"example"`` is returned.

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from core.maze import NORTH, SOUTH, EAST, WEST, DIR_DELTA, OPPOSITE
from core.robot import TURN_RIGHT, TURN_LEFT

# ---------------------------------------------------------------------------
# Typology parsing
# ---------------------------------------------------------------------------

_TYPOLOGY_RE = re.compile(r"^\d+_(.+)\.txt$", re.IGNORECASE)


def parse_typology(filename: str) -> str:
    """
    Extract the maze typology from a filename.

    Parsing rule: filenames formatted as ``[number]_[typology].txt``.
    The leading number and underscore are stripped to get the typology.

    Args:
        filename: The basename of the maze file (e.g. ``"3_dead_end_heavy.txt"``).

    Returns:
        The typology string (e.g. ``"dead_end_heavy"``), or ``"example"``
        if the filename doesn't match the expected pattern.
    """
    m = _TYPOLOGY_RE.match(filename)
    if m:
        return m.group(1)
    return "example"


# ---------------------------------------------------------------------------
# Maze file parser
# ---------------------------------------------------------------------------

def parse_maze_file(path: Path) -> tuple[int, int, list[list[int]]]:
    """
    Parse an mms ASCII maze file into a truth wall grid.

    The ASCII format uses a ``(2W+1) × (2H+1)`` character grid where
    ``+`` marks intersections, ``---`` or ``   `` marks horizontal
    segments, and ``|`` or `` `` marks vertical segments.

    Args:
        path: Path to the ``.txt`` maze file.

    Returns:
        ``(width, height, walls)`` where ``walls[x][y]`` is a bitmask
        (N=1, S=2, E=4, W=8) encoding the **true** wall configuration
        of cell ``(x, y)``.

    Raises:
        ValueError: If the file cannot be parsed (wrong dimensions, etc.).
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Empty maze file: {path}")

    # Determine maze dimensions from grid size
    # Grid has 2*H+1 rows and 2*W+1 columns (approximately)
    grid_rows = len(lines)
    height = (grid_rows - 1) // 2
    if height <= 0:
        raise ValueError(f"Cannot determine height from {grid_rows} lines in {path}")

    # Pad all lines to the same length
    max_len = max(len(line) for line in lines)
    grid = [line.ljust(max_len) for line in lines]

    grid_cols = max_len
    width = (grid_cols - 1) // 4  # each cell is 4 chars wide: "+---"

    if width <= 0:
        raise ValueError(f"Cannot determine width from {grid_cols} cols in {path}")

    # DIR_BIT mirrors core.maze
    DIR_BIT = {NORTH: 0b0001, SOUTH: 0b0010, EAST: 0b0100, WEST: 0b1000}

    # Initialize wall grid — walls[x][y] is a bitmask
    walls: list[list[int]] = [[0 for _ in range(height)] for _ in range(width)]

    for cy in range(height):
        for cx in range(width):
            # Map maze cell (cx, cy) to grid coordinates.
            # In the ASCII grid:
            #   - Row 0 is the TOP wall row (corresponds to maze row height-1)
            #   - The bottom-left cell (0, 0) is at grid row = 2*height, col = 0
            #
            # Grid row for cell's NORTH wall: 2*(height - cy) - 2  = 2*(height - 1 - cy)
            # Grid row for cell center:       2*(height - cy) - 1  = 2*(height - 1 - cy) + 1
            # Grid row for cell's SOUTH wall: 2*(height - cy)      = 2*(height - 1 - cy) + 2

            grid_row_center = 2 * (height - 1 - cy) + 1
            grid_col_center = 4 * cx + 2  # center of the cell in the grid

            # NORTH wall: horizontal segment above center
            north_row = grid_row_center - 1
            # Check the 3 chars of the horizontal segment: grid[north_row][4*cx+1 : 4*cx+4]
            if north_row >= 0:
                seg = grid[north_row][4 * cx + 1: 4 * cx + 4]
                if "---" in seg or seg.strip() == "---":
                    walls[cx][cy] |= DIR_BIT[NORTH]

            # SOUTH wall: horizontal segment below center
            south_row = grid_row_center + 1
            if south_row < grid_rows:
                seg = grid[south_row][4 * cx + 1: 4 * cx + 4]
                if "---" in seg or seg.strip() == "---":
                    walls[cx][cy] |= DIR_BIT[SOUTH]

            # WEST wall: vertical segment to the left of center
            west_col = 4 * cx
            if west_col < grid_cols:
                ch = grid[grid_row_center][west_col]
                if ch == "|":
                    walls[cx][cy] |= DIR_BIT[WEST]

            # EAST wall: vertical segment to the right of center
            east_col = 4 * (cx + 1)
            if east_col < grid_cols:
                ch = grid[grid_row_center][east_col]
                if ch == "|":
                    walls[cx][cy] |= DIR_BIT[EAST]

    return width, height, walls


# ---------------------------------------------------------------------------
# Mock Simulator
# ---------------------------------------------------------------------------

class MockSimulator:
    """
    In-memory replacement for the mms simulator.

    Holds the truth wall grid and a lightweight robot pose.  Provides
    methods that mirror the ``core.simulator_api`` public functions.

    Attributes:
        width:    Maze width (columns).
        height:   Maze height (rows).
        walls:    Truth wall grid — ``walls[x][y]`` bitmask.
        robot_x:  Current robot column.
        robot_y:  Current robot row.
        heading:  Current robot heading (``'N'``, ``'S'``, ``'E'``, ``'W'``).
    """

    DIR_BIT = {NORTH: 0b0001, SOUTH: 0b0010, EAST: 0b0100, WEST: 0b1000}

    def __init__(
        self,
        width: int,
        height: int,
        walls: list[list[int]],
    ) -> None:
        self.width = width
        self.height = height
        self.walls = walls
        self.robot_x = 0
        self.robot_y = 0
        self.heading: str = NORTH

    # ---- Maze queries ----

    def maze_width(self) -> int:
        return self.width

    def maze_height(self) -> int:
        return self.height

    # ---- Wall queries ----

    def _has_wall(self, x: int, y: int, direction: str) -> bool:
        """Return True if the *truth* grid has a wall at (x, y) in direction."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True  # Out-of-bounds counts as a wall
        return bool(self.walls[x][y] & self.DIR_BIT[direction])

    def _wall_relative(self, relative_dir: str) -> bool:
        """
        Check wall in a direction relative to the robot's heading.

        Args:
            relative_dir: ``'front'``, ``'right'``, ``'left'``, or ``'back'``.
        """
        abs_map = {
            "front": self.heading,
            "right": TURN_RIGHT[self.heading],
            "left": TURN_LEFT[self.heading],
            "back": OPPOSITE[self.heading],
        }
        abs_dir = abs_map[relative_dir]
        return self._has_wall(self.robot_x, self.robot_y, abs_dir)

    def wall_front(self, _num_half_steps: int = 1) -> bool:
        return self._wall_relative("front")

    def wall_right(self, _num_half_steps: int = 1) -> bool:
        return self._wall_relative("right")

    def wall_left(self, _num_half_steps: int = 1) -> bool:
        return self._wall_relative("left")

    def wall_back(self, _num_half_steps: int = 1) -> bool:
        return self._wall_relative("back")

    # ---- Movement ----

    def move_forward(self, distance: int = 1) -> str:
        """
        Move the robot forward.  Returns ``"ack"`` on success,
        ``"crash"`` if blocked by a wall (should not happen during
        correct operation).
        """
        for _ in range(distance):
            if self._has_wall(self.robot_x, self.robot_y, self.heading):
                return "crash"
            dx, dy = DIR_DELTA[self.heading]
            self.robot_x += dx
            self.robot_y += dy
        return "ack"

    def turn_right(self) -> str:
        self.heading = TURN_RIGHT[self.heading]
        return "ack"

    def turn_left(self) -> str:
        self.heading = TURN_LEFT[self.heading]
        return "ack"

    def turn_right_45(self) -> str:
        return "ack"

    def turn_left_45(self) -> str:
        return "ack"

    # ---- Display (no-ops) ----

    def set_wall(self, *_args) -> None:
        pass

    def clear_wall(self, *_args) -> None:
        pass

    def set_color(self, *_args) -> None:
        pass

    def clear_color(self, *_args) -> None:
        pass

    def clear_all_color(self) -> None:
        pass

    def set_text(self, *_args) -> None:
        pass

    def clear_text(self, *_args) -> None:
        pass

    def clear_all_text(self) -> None:
        pass

    # ---- Reset / stats (stubs) ----

    def was_reset(self) -> bool:
        return False

    def ack_reset(self) -> None:
        pass

    def get_stat(self, _stat: str) -> str:
        return "0"

    # ---- Logging ----

    @staticmethod
    def log_info(message: str) -> None:
        sys.stderr.write(f"[BATCH-INFO] {message}\n")

    @staticmethod
    def log_error(message: str) -> None:
        sys.stderr.write(f"[BATCH-ERROR] {message}\n")


# ---------------------------------------------------------------------------
# Context manager — patches core.simulator_api
# ---------------------------------------------------------------------------

@contextmanager
def mock_simulator_context(
    maze_path: Path,
) -> Generator[MockSimulator, None, None]:
    """
    Context manager that replaces ``core.simulator_api`` functions with
    a ``MockSimulator`` backed by a parsed maze file.

    On entry, every public function in the API module is replaced with
    the mock equivalent.  On exit, all originals are restored.

    Usage::

        with mock_simulator_context(Path("mazes/1_open_field.txt")) as sim:
            # All api.wall_front(), api.move_forward(), etc.
            # now route through `sim` instead of stdin/stdout.
            ...

    Args:
        maze_path: Path to the ASCII maze file to load.

    Yields:
        The ``MockSimulator`` instance (for inspection if needed).
    """
    import core.simulator_api as api_module

    width, height, walls = parse_maze_file(maze_path)
    sim = MockSimulator(width, height, walls)

    # Map of api function name → mock replacement
    patches = {
        "maze_width":      sim.maze_width,
        "maze_height":     sim.maze_height,
        "wall_front":      sim.wall_front,
        "wall_right":      sim.wall_right,
        "wall_left":       sim.wall_left,
        "wall_back":       sim.wall_back,
        "move_forward":    lambda distance=1: sim.move_forward(distance) != "crash",
        "turn_right":      lambda: sim.turn_right(),
        "turn_left":       lambda: sim.turn_left(),
        "turn_right_45":   lambda: sim.turn_right_45(),
        "turn_left_45":    lambda: sim.turn_left_45(),
        "set_wall":        sim.set_wall,
        "clear_wall":      sim.clear_wall,
        "set_color":       sim.set_color,
        "clear_color":     sim.clear_color,
        "clear_all_color": sim.clear_all_color,
        "set_text":        sim.set_text,
        "clear_text":      sim.clear_text,
        "clear_all_text":  sim.clear_all_text,
        "was_reset":       sim.was_reset,
        "ack_reset":       sim.ack_reset,
        "get_stat":        sim.get_stat,
        "log_info":        sim.log_info,
        "log_error":       sim.log_error,
    }

    # Save originals and apply patches
    originals: dict = {}
    for name, replacement in patches.items():
        originals[name] = getattr(api_module, name)
        setattr(api_module, name, replacement)

    try:
        yield sim
    finally:
        # Restore originals
        for name, original in originals.items():
            setattr(api_module, name, original)

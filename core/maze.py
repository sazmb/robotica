"""
Maze Representation Module
===========================
Provides an efficient internal representation of a 16×16 Micromouse maze.

Each cell stores:
  - Wall presence for all four cardinal directions (N, S, E, W)
  - Whether the cell has been visited
  - A flood-fill distance value
  - A generic cost field for A* g-values

Wall encoding uses a compact bitmask per cell (4 bits per cell).
Neighbour traversal and path reconstruction utilities are included.

Coordinate convention (matching mms simulator):
  - Origin (0, 0) is the BOTTOM-LEFT cell
  - x increases to the RIGHT
  - y increases UPWARD

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterator, Optional

# Cardinal direction constants
NORTH = "N"
SOUTH = "S"
EAST = "E"
WEST = "W"

# Direction → bitmask for compact wall encoding
DIR_BIT: dict[str, int] = {
    NORTH: 0b0001,
    SOUTH: 0b0010,
    EAST:  0b0100,
    WEST:  0b1000,
}

# Direction → coordinate delta (dx, dy)
DIR_DELTA: dict[str, tuple[int, int]] = {
    NORTH: (0,  1),
    SOUTH: (0, -1),
    EAST:  (1,  0),
    WEST:  (-1, 0),
}

# Opposite direction lookup
OPPOSITE: dict[str, str] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST:  WEST,
    WEST:  EAST,
}

# All four directions in order
ALL_DIRS = [NORTH, EAST, SOUTH, WEST]


@dataclass
class Cell:
    """
    Represents a single cell in the Micromouse maze.

    Attributes:
        x (int): Column index (0-based).
        y (int): Row index (0-based, bottom = 0).
        walls (int): Bitmask encoding known walls (N=1, S=2, E=4, W=8).
        visited (bool): True if the robot has entered this cell.
        distance (int): Flood-fill distance to the goal. INF = unset.
        g_cost (float): A* g-value (cost from start).
        f_cost (float): A* f-value (g + heuristic).
        parent (Optional[tuple]): Parent cell coordinates for path reconstruction.
    """
    x: int
    y: int
    walls: int = 0          # bitmask: N|S|E|W
    visited: bool = False
    distance: int = field(default_factory=lambda: math.inf)  # type: ignore
    g_cost: float = math.inf
    f_cost: float = math.inf
    parent: Optional[tuple[int, int]] = None

    def has_wall(self, direction: str) -> bool:
        """
        Check if this cell has a wall in the given direction.

        Args:
            direction: One of 'N', 'S', 'E', 'W'.

        Returns:
            True if the wall is present.
        """
        return bool(self.walls & DIR_BIT[direction])

    def set_wall(self, direction: str) -> None:
        """
        Mark a wall as present in the given direction.

        Args:
            direction: One of 'N', 'S', 'E', 'W'.
        """
        self.walls |= DIR_BIT[direction]

    def clear_wall(self, direction: str) -> None:
        """
        Remove a wall in the given direction (mark as open passage).

        Args:
            direction: One of 'N', 'S', 'E', 'W'.
        """
        self.walls &= ~DIR_BIT[direction]

    def is_open(self, direction: str) -> bool:
        """
        Return True if the passage in `direction` is open (no wall).

        Args:
            direction: One of 'N', 'S', 'E', 'W'.
        """
        return not self.has_wall(direction)

    def __repr__(self) -> str:
        walls_str = "".join(d for d in ALL_DIRS if self.has_wall(d))
        return (
            f"Cell({self.x},{self.y} walls={walls_str or 'none'} "
            f"visited={self.visited} dist={self.distance})"
        )


class MazeMap:
    """
    Internal representation of the entire Micromouse maze.

    The map starts completely unknown (no walls recorded except outer boundary).
    Walls are added incrementally as the robot discovers them.

    Attributes:
        width (int): Number of columns.
        height (int): Number of rows.
        cells (list[list[Cell]]): 2-D grid of Cell objects, indexed [x][y].
        goal_cells (list[tuple[int,int]]): Target cell coordinates.
    """

    # Default goal region for a standard 16×16 maze:
    # The centre 2×2 block at cells (7,7), (7,8), (8,7), (8,8)
    DEFAULT_GOALS_16 = [(7, 7), (7, 8), (8, 7), (8, 8)]

    def __init__(
        self,
        width: int = 16,
        height: int = 16,
        goal_cells: Optional[list[tuple[int, int]]] = None,
    ) -> None:
        """
        Initialise the maze map with unknown interior walls.

        Outer boundary walls are set automatically.

        Args:
            width: Number of columns (default 16).
            height: Number of rows (default 16).
            goal_cells: List of (x,y) goal coordinates.
                        Defaults to the standard 16×16 centre region.
        """
        self.width = width
        self.height = height
        self.goal_cells: list[tuple[int, int]] = (
            goal_cells if goal_cells is not None else self.DEFAULT_GOALS_16
        )

        # Build the 2-D grid
        self.cells: list[list[Cell]] = [
            [Cell(x=col, y=row) for row in range(height)]
            for col in range(width)
        ]

        # Set outer boundary walls
        self._init_boundary_walls()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_boundary_walls(self) -> None:
        """Mark the four outer edges of the maze as walled."""
        for x in range(self.width):
            self.cells[x][0].set_wall(SOUTH)            # Bottom row
            self.cells[x][self.height - 1].set_wall(NORTH)  # Top row
        for y in range(self.height):
            self.cells[0][y].set_wall(WEST)             # Left column
            self.cells[self.width - 1][y].set_wall(EAST)    # Right column

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def cell(self, x: int, y: int) -> Cell:
        """
        Return the Cell at position (x, y).

        Args:
            x: Column index.
            y: Row index.

        Returns:
            The Cell object.

        Raises:
            IndexError: If coordinates are out of bounds.
        """
        if not self.in_bounds(x, y):
            raise IndexError(f"Cell ({x}, {y}) is out of bounds for {self.width}×{self.height} maze.")
        return self.cells[x][y]

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if (x, y) lies within the maze grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_goal(self, x: int, y: int) -> bool:
        """Return True if (x, y) is one of the goal cells."""
        return (x, y) in self.goal_cells

    # ------------------------------------------------------------------
    # Wall management
    # ------------------------------------------------------------------

    def update_wall(self, x: int, y: int, direction: str, present: bool) -> bool:
        """
        Record a wall observation and propagate to the neighbouring cell.

        Walls are shared between adjacent cells (a wall on the NORTH side of
        cell (x,y) is also the SOUTH wall of cell (x, y+1)).

        Args:
            x: Column of the observing cell.
            y: Row of the observing cell.
            direction: Direction of the wall relative to (x, y).
            present: True if a wall is there, False if it is open.

        Returns:
            True if the wall information was *new* (changed the map),
            False if it was already known.
        """
        c = self.cell(x, y)
        already_set = c.has_wall(direction) == present

        # Update the current cell
        if present:
            c.set_wall(direction)
        else:
            c.clear_wall(direction)

        # Propagate to neighbour
        dx, dy = DIR_DELTA[direction]
        nx, ny = x + dx, y + dy
        if self.in_bounds(nx, ny):
            neighbour = self.cell(nx, ny)
            opp = OPPOSITE[direction]
            if present:
                neighbour.set_wall(opp)
            else:
                neighbour.clear_wall(opp)

        return not already_set  # True = new information

    def has_wall(self, x: int, y: int, direction: str) -> bool:
        """Convenience: check wall presence at cell (x, y)."""
        return self.cell(x, y).has_wall(direction)

    # ------------------------------------------------------------------
    # Traversal helpers
    # ------------------------------------------------------------------

    def open_neighbours(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Return the list of accessible neighbours of cell (x, y) —
        i.e., directions where no wall is recorded.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            List of (nx, ny) tuples for reachable neighbours.
        """
        neighbours: list[tuple[int, int]] = []
        c = self.cell(x, y)
        for d in ALL_DIRS:
            if c.is_open(d):
                dx, dy = DIR_DELTA[d]
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    neighbours.append((nx, ny))
        return neighbours

    def all_neighbours(self, x: int, y: int) -> list[tuple[int, int]]:
        """
        Return all in-bounds neighbours regardless of walls.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            List of (nx, ny) tuples.
        """
        result: list[tuple[int, int]] = []
        for d in ALL_DIRS:
            dx, dy = DIR_DELTA[d]
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                result.append((nx, ny))
        return result

    def direction_to(
        self, from_x: int, from_y: int, to_x: int, to_y: int
    ) -> Optional[str]:
        """
        Compute the cardinal direction from (from_x, from_y) to (to_x, to_y).

        Args:
            from_x, from_y: Source cell.
            to_x, to_y: Target cell (must be adjacent).

        Returns:
            One of 'N', 'S', 'E', 'W', or None if not adjacent.
        """
        dx = to_x - from_x
        dy = to_y - from_y
        for d, delta in DIR_DELTA.items():
            if delta == (dx, dy):
                return d
        return None

    # ------------------------------------------------------------------
    # Path utilities
    # ------------------------------------------------------------------

    def reconstruct_path(
        self, goal_x: int, goal_y: int
    ) -> list[tuple[int, int]]:
        """
        Reconstruct a path from the start to `goal` using parent pointers.

        Parent pointers must be set by the search algorithm (A*, etc.).

        Args:
            goal_x, goal_y: Destination cell.

        Returns:
            Ordered list of (x, y) from start → goal, or empty list if
            no path exists (parent chain is broken).
        """
        path: list[tuple[int, int]] = []
        cur = (goal_x, goal_y)
        while cur is not None:
            path.append(cur)
            cx, cy = cur
            cur = self.cell(cx, cy).parent  # type: ignore
        path.reverse()
        return path

    def manhattan_distance(self, x: int, y: int) -> int:
        """
        Compute the minimum Manhattan distance from (x, y) to the nearest
        goal cell.  Used as an admissible heuristic for A*.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            Minimum Manhattan distance to any goal cell.
        """
        if not self.goal_cells:
            return 0
        return min(
            abs(x - gx) + abs(y - gy)
            for gx, gy in self.goal_cells
        )

    # ------------------------------------------------------------------
    # Flood-fill distance initialisation
    # ------------------------------------------------------------------

    def reset_distances(self, infinity: int = 9999) -> None:
        """
        Reset all cell distances to `infinity` in preparation for a fresh
        flood-fill propagation.

        Args:
            infinity: The value used to represent an unknown/unreachable distance.
        """
        for col in self.cells:
            for cell in col:
                cell.distance = infinity
        # Goal cells start at distance 0
        for gx, gy in self.goal_cells:
            if self.in_bounds(gx, gy):
                self.cells[gx][gy].distance = 0

    # ------------------------------------------------------------------
    # Visited cell statistics
    # ------------------------------------------------------------------

    def visited_count(self) -> int:
        """Return the number of cells the robot has visited."""
        return sum(1 for col in self.cells for c in col if c.visited)

    def unvisited_cells(self) -> list[tuple[int, int]]:
        """Return all (x, y) coordinates that have never been visited."""
        return [
            (c.x, c.y)
            for col in self.cells
            for c in col
            if not c.visited
        ]

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"MazeMap({self.width}×{self.height}, goals={self.goal_cells})"

    def ascii_debug(self) -> str:
        """
        Return a rough ASCII representation of the known maze walls.
        Useful for offline debugging without the simulator.
        """
        lines: list[str] = []
        for y in range(self.height - 1, -1, -1):  # top row first
            # Top wall row
            top = ""
            for x in range(self.width):
                top += "+"
                top += "---" if self.cells[x][y].has_wall(NORTH) else "   "
            top += "+"
            lines.append(top)
            # Side wall row
            side = ""
            for x in range(self.width):
                side += "|" if self.cells[x][y].has_wall(WEST) else " "
                dist = self.cells[x][y].distance
                label = f"{dist:^3}" if dist < 9999 else " ? "
                side += label
            side += "|"
            lines.append(side)
        # Bottom boundary
        bottom = ""
        for x in range(self.width):
            bottom += "+---"
        bottom += "+"
        lines.append(bottom)
        return "\n".join(lines)

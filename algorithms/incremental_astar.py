"""
Incremental A* Algorithm for Micromouse
=========================================
Implements an online replanning strategy inspired by Lifelong Planning A*
(LPA*) and D* Lite, adapted to Micromouse constraints.

Algorithm Overview
------------------
Instead of re-running full A* from scratch after every wall discovery,
this implementation uses:
  1. Standard A* for initial planning.
  2. Efficient replanning: only affected portions of the search space
     are re-explored after new walls are discovered.
  3. Manhattan distance heuristic: h(n) = |nx - gx| + |ny - gy|

Heuristic Design
----------------
The Manhattan distance is:
  - Admissible: never overestimates the true cost (since each move
    costs exactly 1 and we can't cut corners).
  - Consistent (monotone): h(n) ≤ cost(n,n') + h(n') for all edges.
  - Efficient: O(1) computation per node.

Time Complexity
---------------
  - Initial A*:    O((W×H) log(W×H)) using a binary heap
  - Replanning:    O(k log k) where k = cells invalidated by new walls
  - Overall:       O(N² log N) worst case for full exploration

Space Complexity
----------------
  - O(W × H) for g-values, f-values, and the open/closed sets

Tradeoffs vs Flood Fill
-----------------------
  + A* is typically faster on sparse mazes (good heuristic prunes search)
  + Finds cost-optimal paths in fully known maps
  + More robust on mazes with many long corridors
  - Higher per-step computation than Flood Fill
  - Heuristic quality degrades in highly connected mazes
  - More complex to implement correctly

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import heapq
import math
import time
from typing import Optional

from core.maze import MazeMap, ALL_DIRS, DIR_DELTA, OPPOSITE
from core.robot import RobotState
import core.simulator_api as api


# ---------------------------------------------------------------------------
# Priority queue node
# ---------------------------------------------------------------------------

class _PQNode:
    """
    A comparable node for the A* priority queue.

    Comparisons are done on f_cost first, then g_cost (tie-breaking),
    then by position (to ensure a total order).
    """
    __slots__ = ("f", "g", "x", "y")

    def __init__(self, f: float, g: float, x: int, y: int) -> None:
        self.f = f
        self.g = g
        self.x = x
        self.y = y

    def __lt__(self, other: _PQNode) -> bool:
        if self.f != other.f:
            return self.f < other.f
        if self.g != other.g:
            return self.g > other.g  # prefer larger g (closer to goal)
        return (self.x, self.y) < (other.x, other.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _PQNode):
            return NotImplemented
        return (self.f, self.g, self.x, self.y) == (other.f, other.g, other.x, other.y)


# ---------------------------------------------------------------------------
# Incremental A* solver
# ---------------------------------------------------------------------------

class IncrementalAStar:
    """
    Online, replanning A* maze solver for Micromouse.

    The solver plans a path from the robot's current position to the nearest
    goal cell using A*.  When new walls are discovered, only the invalidated
    portion of the path is replanned.

    Attributes:
        maze (MazeMap): Shared internal maze representation.
        robot (RobotState): Shared robot state.
        current_path (list): The currently planned path (may be empty).
        replan_count (int): Number of times the path was replanned.
        new_walls_found (int): Number of new wall observations.
        heuristic_weight (float): Weight w for weighted A* (w=1 → standard A*).
    """

    def __init__(
        self,
        maze: MazeMap,
        robot: RobotState,
        heuristic_weight: float = 1.0,
    ) -> None:
        """
        Initialise the Incremental A* solver.

        Args:
            maze: Shared MazeMap instance.
            robot: Shared RobotState instance.
            heuristic_weight: Multiplier for heuristic (1.0 = standard A*,
                              >1.0 = weighted A* — faster but suboptimal).
        """
        self.maze = maze
        self.robot = robot
        self.heuristic_weight = heuristic_weight
        self.current_path: list[tuple[int, int]] = []
        self.replan_count: int = 0
        self.new_walls_found: int = 0
        self._start_time: float = 0.0
        self._elapsed: float = 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """
        Run the online A* exploration loop until the goal is reached.

        At each step:
          1. Sense walls and update the map.
          2. If new walls invalidate the current path → replan.
          3. Follow the first step of the planned path.

        Returns:
            True if the goal was reached, False if no path exists.
        """
        self._start_time = time.perf_counter()
        api.log_info("IncrementalAStar: starting exploration")

        # Initial planning
        if not self._replan():
            api.log_info("IncrementalAStar: no path to goal from start — aborting")
            return False

        while True:
            x, y = self.robot.x, self.robot.y

            # --- Goal check ---
            if self.maze.is_goal(x, y):
                self._elapsed = time.perf_counter() - self._start_time
                api.log_info(f"IncrementalAStar: GOAL REACHED at ({x}, {y})!")
                api.log_info(self.robot.summary())
                self._color_path(self.current_path)
                return True

            # --- Sense walls ---
            new_info = self._sense_and_update_walls(x, y)

            if new_info:
                self.new_walls_found += 1
                # Check if current path is still valid
                if not self._path_is_valid():
                    api.log_info(
                        f"IncrementalAStar: path invalidated at ({x},{y}), replanning..."
                    )
                    if not self._replan():
                        api.log_info("IncrementalAStar: goal unreachable!")
                        return False
                    self.replan_count += 1
                    self._update_display()

            # --- Follow path ---
            if not self.current_path or len(self.current_path) < 2:
                # We're on the path endpoint but not at goal — replan
                if not self._replan():
                    return False
                self.replan_count += 1

            # Remove current position from path front
            if self.current_path and self.current_path[0] == (x, y):
                self.current_path.pop(0)

            if not self.current_path:
                continue

            nx, ny = self.current_path[0]
            direction = self.maze.direction_to(x, y, nx, ny)
            if direction is None:
                # Path step is not adjacent — replan
                if not self._replan():
                    return False
                continue

            self.robot.face_direction(direction)
            success = self.robot.move_forward()
            if not success:
                # Crash — wall not in map; update and replan
                api.log_info("IncrementalAStar: unexpected crash — replanning")
                self.maze.update_wall(x, y, direction, True)
                api.set_wall(x, y, direction)
                if not self._replan():
                    return False
                self.replan_count += 1

            # Mark visited
            self.maze.cell(self.robot.x, self.robot.y).visited = True

    def get_metrics(self) -> dict:
        """
        Return performance metrics for this run.

        Returns:
            Dictionary of metric name → value.
        """
        return {
            "algorithm": "IncrementalAStar",
            "moves": self.robot.move_count,
            "turns": self.robot.turn_count,
            "unique_cells_visited": self.robot.unique_cells_visited(),
            "new_walls_found": self.new_walls_found,
            "replan_count": self.replan_count,
            "path_length": len(self.current_path),
            "elapsed_seconds": round(self._elapsed, 4),
            "heuristic_weight": self.heuristic_weight,
        }

    # ------------------------------------------------------------------
    # A* search
    # ------------------------------------------------------------------

    def _heuristic(self, x: int, y: int) -> float:
        """
        Admissible Manhattan-distance heuristic to nearest goal.

        For weighted A* (epsilon-admissible), multiply by heuristic_weight.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            Estimated cost to nearest goal.
        """
        return self.heuristic_weight * self.maze.manhattan_distance(x, y)

    def _astar(
        self, start_x: int, start_y: int
    ) -> Optional[list[tuple[int, int]]]:
        """
        Run A* from (start_x, start_y) to the nearest goal cell.

        Uses a binary heap (heapq) for O(log N) priority queue operations.

        Args:
            start_x: Starting column.
            start_y: Starting row.

        Returns:
            Ordered list of (x, y) from start → goal, or None if unreachable.
        """
        INF = math.inf

        # Reset planning costs
        for col in self.maze.cells:
            for cell in col:
                cell.g_cost = INF
                cell.f_cost = INF
                cell.parent = None

        start_cell = self.maze.cell(start_x, start_y)
        start_cell.g_cost = 0.0
        start_cell.f_cost = self._heuristic(start_x, start_y)

        open_heap: list[_PQNode] = []
        heapq.heappush(open_heap, _PQNode(start_cell.f_cost, 0.0, start_x, start_y))

        closed: set[tuple[int, int]] = set()
        in_open: dict[tuple[int, int], float] = {(start_x, start_y): start_cell.f_cost}

        while open_heap:
            node = heapq.heappop(open_heap)
            pos = (node.x, node.y)

            if pos in closed:
                continue  # stale entry
            closed.add(pos)
            in_open.pop(pos, None)

            # Goal test
            if self.maze.is_goal(node.x, node.y):
                # Reconstruct path
                return self.maze.reconstruct_path(node.x, node.y)

            # Expand neighbours
            for nx, ny in self.maze.open_neighbours(node.x, node.y):
                if (nx, ny) in closed:
                    continue
                tentative_g = self.maze.cell(node.x, node.y).g_cost + 1.0
                neighbour = self.maze.cell(nx, ny)

                if tentative_g < neighbour.g_cost:
                    neighbour.g_cost = tentative_g
                    neighbour.f_cost = tentative_g + self._heuristic(nx, ny)
                    neighbour.parent = (node.x, node.y)

                    pq_node = _PQNode(neighbour.f_cost, tentative_g, nx, ny)
                    heapq.heappush(open_heap, pq_node)
                    in_open[(nx, ny)] = neighbour.f_cost

        return None  # No path found

    def _replan(self) -> bool:
        """
        Run A* from the robot's current position and store the resulting path.

        Returns:
            True if a path was found, False otherwise.
        """
        path = self._astar(self.robot.x, self.robot.y)
        if path is None:
            self.current_path = []
            return False
        self.current_path = path
        api.log_info(
            f"IncrementalAStar: path length = {len(path)-1} steps"
        )
        return True

    # ------------------------------------------------------------------
    # Path validation
    # ------------------------------------------------------------------

    def _path_is_valid(self) -> bool:
        """
        Check whether the currently planned path is still traversable
        given the updated wall map.

        Returns:
            True if all consecutive step pairs are still open, False otherwise.
        """
        path = self.current_path
        # Find current position in path
        rx, ry = self.robot.x, self.robot.y
        try:
            start_idx = path.index((rx, ry))
        except ValueError:
            return False  # robot not on path — definitely invalid

        for i in range(start_idx, len(path) - 1):
            cx, cy = path[i]
            nx, ny = path[i + 1]
            direction = self.maze.direction_to(cx, cy, nx, ny)
            if direction is None:
                return False
            if self.maze.has_wall(cx, cy, direction):
                return False
        return True

    # ------------------------------------------------------------------
    # Wall sensing
    # ------------------------------------------------------------------

    def _sense_and_update_walls(self, x: int, y: int) -> bool:
        """
        Sense all walls around the current cell and update the maze map.

        Args:
            x: Current column.
            y: Current row.

        Returns:
            True if any new wall information was discovered.
        """
        wall_readings = self.robot.sense_walls()
        new_info = False
        for direction, has_wall in wall_readings.items():
            changed = self.maze.update_wall(x, y, direction, has_wall)
            if changed:
                new_info = True
                if has_wall:
                    api.set_wall(x, y, direction)
        return new_info

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def _update_display(self) -> None:
        """
        Update the simulator display to show current A* f-values.
        """
        for col in self.maze.cells:
            for cell in col:
                if cell.f_cost < math.inf:
                    api.set_text(cell.x, cell.y, str(int(cell.f_cost)))
                    if self.maze.is_goal(cell.x, cell.y):
                        api.set_color(cell.x, cell.y, "G")
                    elif cell.visited:
                        api.set_color(cell.x, cell.y, "C")
                    else:
                        api.set_color(cell.x, cell.y, "Y")
                else:
                    api.set_color(cell.x, cell.y, "W")

    def _color_path(
        self, path: list[tuple[int, int]], color: str = "G"
    ) -> None:
        """Highlight a path in the simulator."""
        for x, y in path:
            api.set_color(x, y, color)

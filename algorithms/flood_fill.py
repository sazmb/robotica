"""
Flood Fill Algorithm for Micromouse
=====================================
Implements the classic Flood Fill (FF) maze-solving strategy.

Algorithm Overview
------------------
Flood Fill maintains a distance map where each cell stores the minimum
number of steps to reach the goal under the *currently known* walls.

At every step:
  1. Sense walls in the current cell.
  2. If new walls discovered → propagate updated distances (re-flood).
  3. Move to the open neighbour with the smallest distance value.
  4. Repeat until the goal is reached.

Time Complexity
---------------
  - Wall sensing:      O(1) per cell
  - Re-flood (BFS):   O(W × H) worst case, where W, H = maze dimensions
  - Path selection:   O(4) per step (constant neighbours)
  - Overall:          O(N²) worst case for a full 16×16 exploration
    where N = 16 (256 cells)

Space Complexity
----------------
  - O(W × H) for the distance map (one integer per cell)

Strengths
---------
  + Guarantees reaching the goal if one exists
  + Very fast in practice (BFS is O(V+E))
  + Simple to implement and debug
  + Works online (no full map required upfront)

Weaknesses
----------
  - Can visit many cells before finding optimal path
  - May revisit cells during exploration
  - Does not exploit any geometric structure of the maze

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Optional

from core.maze import MazeMap, ALL_DIRS, OPPOSITE, DIR_DELTA
from core.robot import RobotState
import core.simulator_api as api


class FloodFill:
    """
    Flood Fill maze solver.

    Usage::

        maze  = MazeMap()
        robot = RobotState()
        ff    = FloodFill(maze, robot)
        ff.run()

    Attributes:
        maze (MazeMap): Internal map of the maze.
        robot (RobotState): Robot state tracker.
        new_walls_found (int): Count of newly discovered walls (for metrics).
        replan_count (int): Number of times distances were re-propagated.
    """

    def __init__(self, maze: MazeMap, robot: RobotState) -> None:
        """
        Initialise the Flood Fill solver.

        Args:
            maze:  Shared MazeMap instance.
            robot: Shared RobotState instance.
        """
        self.maze = maze
        self.robot = robot
        self.new_walls_found: int = 0
        self.replan_count: int = 0
        self._start_time: float = 0.0
        self._elapsed: float = 0.0

        # Initialise flood distances from goal
        self._flood_from_goal()

        self.exploration_mode = False # VERSIONE CON PENALITA' DI VISITA

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """
        Run the exploration loop until the goal is reached.

        Returns:
            True if the goal was successfully reached, False otherwise.
        """
        self._start_time = time.perf_counter()
        api.log_info("FloodFill: starting exploration")

        while True:
            x, y = self.robot.x, self.robot.y

            # --- Goal check ---
            if self.maze.is_goal(x, y):
                self._elapsed = time.perf_counter() - self._start_time
                api.log_info(f"FloodFill: GOAL REACHED at ({x}, {y})!")
                api.log_info(self.robot.summary())
                self._color_goal_path()
                return True

            # --- Sense walls around current cell ---
            new_info = self._sense_and_update_walls(x, y)

            # --- Re-flood if new information was gained ---
            if new_info:
                self.new_walls_found += 1
                self.replan_count += 1
                self._flood_from_goal()
                self._update_display()

            # --- Check for dead end (no reachable neighbours) ---
            next_cell = self._choose_next_cell(x, y)
            if next_cell is None:
                api.log_info(f"FloodFill: dead end detected at ({x}, {y})")
                # The flood fill should always find a way out unless maze
                # is disconnected — this indicates an impossible maze.
                return False

            # --- Navigate to next cell ---
            nx, ny = next_cell
            direction = self.maze.direction_to(x, y, nx, ny)
            if direction is None:
                continue  # should not happen

            self.robot.face_direction(direction)
            self.robot.move_forward()

            # Mark cell as visited in map
            self.maze.cell(self.robot.x, self.robot.y).visited = True

    def get_shortest_path(
        self, start_x: int, start_y: int, *, visited_only: bool = False,
    ) -> list[tuple[int, int]]:
        """
        Trace the flood-fill distance gradient from (start_x, start_y) to
        the current goal and return the ordered path.

        When ``visited_only=True`` (Phase 3 speed-run mode), the distance
        map is re-flooded using **only visited cells** before tracing.
        This guarantees the returned path never crosses a cell the robot
        has not physically entered.

        This method does NOT issue any simulator commands; it only reads
        ``self.maze.cells[x][y].distance`` values.

        Args:
            start_x: Starting column index.
            start_y: Starting row index.
            visited_only: If True, re-flood and trace through visited
                cells only — treating unvisited cells as impassable.

        Returns:
            Ordered list of (x, y) from start → goal.
            Returns ``[(start_x, start_y)]`` if already at the goal.
            Returns ``[]`` if the goal is unreachable.
        """
        # Re-flood with the appropriate constraint
        if visited_only:
            self._flood_visited_only()
        else:
            self._flood_from_goal()

        # Check start is reachable
        if not self.maze.in_bounds(start_x, start_y):
            api.log_info(f"FloodFill.get_shortest_path: ({start_x},{start_y}) out of bounds")
            return []

        if self.maze.cells[start_x][start_y].distance >= 9999:
            api.log_info(
                f"FloodFill.get_shortest_path: goal unreachable from ({start_x},{start_y})"
                f" (visited_only={visited_only})"
            )
            return []

        path: list[tuple[int, int]] = [(start_x, start_y)]
        visited: set[tuple[int, int]] = {(start_x, start_y)}
        x, y = start_x, start_y

        while not self.maze.is_goal(x, y):
            neighbours = self.maze.open_neighbours(
                x, y, visited_only=visited_only,
            )
            if not neighbours:
                break  # trapped — should not happen on a valid map
            nxt = min(neighbours, key=lambda p: self.maze.cells[p[0]][p[1]].distance)
            if nxt in visited:
                break  # loop guard for identical-distance ties
            x, y = nxt
            visited.add((x, y))
            path.append((x, y))

        return path

    def run_fast(self, path: list[tuple[int, int]]) -> None:

        """
        Execute a known path as fast as possible (no sensing).

        Used for the final optimised run after the maze is fully explored.

        Args:
            path: Ordered list of (x, y) cells from current position to goal.
        """
        api.log_info("FloodFill: starting fast run")
        for nx, ny in path[1:]:  # Skip the starting cell
            cx, cy = self.robot.x, self.robot.y
            direction = self.maze.direction_to(cx, cy, nx, ny)
            if direction:
                self.robot.face_direction(direction)
                self.robot.move_forward()

    def get_metrics(self) -> dict:
        """
        Return performance metrics for this run.

        Returns:
            Dictionary of metric name → value.
        """
        return {
            "algorithm": "FloodFill",
            "moves": self.robot.move_count,
            "turns": self.robot.turn_count,
            "unique_cells_visited": self.robot.unique_cells_visited(),
            "new_walls_found": self.new_walls_found,
            "replan_count": self.replan_count,
            "elapsed_seconds": round(self._elapsed, 4),
            "goal_distance": self.maze.cell(
                self.robot.x, self.robot.y
            ).distance
            if self.maze.in_bounds(self.robot.x, self.robot.y)
            else -1,
        }

    # ------------------------------------------------------------------
    # Flood Fill core
    # ------------------------------------------------------------------

    def _flood_from_goal(self) -> None:
        """
        BFS-based flood propagation from goal cells outward.

        After this call, every reachable cell has its `distance` set to
        the minimum number of moves to reach the goal *under known walls*.

        Time complexity: O(W × H)
        """
        INF = 9999
        self.maze.reset_distances(infinity=INF)

        queue: deque[tuple[int, int]] = deque()
        for gx, gy in self.maze.goal_cells:
            if self.maze.in_bounds(gx, gy):
                self.maze.cells[gx][gy].distance = 0
                queue.append((gx, gy))

        while queue:
            x, y = queue.popleft()
            current_dist = self.maze.cells[x][y].distance

            for nx, ny in self.maze.open_neighbours(x, y):
                neighbour = self.maze.cells[nx][ny]
                if neighbour.distance > current_dist + 1:
                    neighbour.distance = current_dist + 1
                    queue.append((nx, ny))

    def _flood_visited_only(self) -> None:
        """
        BFS-based flood propagation restricted to **visited cells only**.

        Identical to ``_flood_from_goal`` except that ``open_neighbours``
        is called with ``visited_only=True``.  Any cell the robot has
        never entered is treated as an impassable wall — its distance
        remains at INF and it will never appear in a traced path.

        Used exclusively by Phase 3 (speed run) to ensure the route
        only passes through physically explored territory.

        Time complexity: O(V) where V = number of visited cells.
        """
        INF = 9999
        self.maze.reset_distances(infinity=INF)

        queue: deque[tuple[int, int]] = deque()
        for gx, gy in self.maze.goal_cells:
            if self.maze.in_bounds(gx, gy) and self.maze.cells[gx][gy].visited:
                self.maze.cells[gx][gy].distance = 0
                queue.append((gx, gy))

        if not queue:
            api.log_info(
                "FloodFill._flood_visited_only: no goal cell has been visited — "
                "speed-run path will be empty"
            )
            return

        while queue:
            x, y = queue.popleft()
            current_dist = self.maze.cells[x][y].distance

            for nx, ny in self.maze.open_neighbours(
                x, y, visited_only=True,
            ):
                neighbour = self.maze.cells[nx][ny]
                if neighbour.distance > current_dist + 1:
                    neighbour.distance = current_dist + 1
                    queue.append((nx, ny))

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
            True if any *new* wall information was discovered.
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
    # Next-cell selection
    # ------------------------------------------------------------------

    def _choose_next_cell(self, x: int, y: int) -> Optional[tuple[int, int]]:
        """
        Select the next cell to move to using minimum-distance policy.

        Among open neighbours, choose the one with the smallest
        flood-fill distance value.

        Tie-breaking: prefer previously unvisited cells.

        Args:
            x: Current column.
            y: Current row.

        Returns:
            (nx, ny) of the chosen next cell, or None if stuck.
        """
        neighbours = self.maze.open_neighbours(x, y)
        if not neighbours:
            return None

        # VERSIONE SENZA PENALITA' DI VISITA
        def score(pos: tuple[int, int]) -> tuple[int, int]:
            nx, ny = pos
            cell = self.maze.cells[nx][ny]
            visit_penalty = self.robot.visit_count(nx, ny)  # prefer unvisited
            return (cell.distance, visit_penalty)
        
        # VERSIONE CON PENALITA' DI VISITA (da testare)
        # def score(pos):
        #     nx, ny = pos
        #     cell = self.maze.cells[nx][ny]
        #     if self.exploration_mode:
        #         return (
        #             cell.distance + min(6, 2 * self.robot.visit_count(nx, ny))
        #         )
        #     return (
        #         cell.distance,
        #         self.robot.visit_count(nx, ny)
        #     )

        best = min(neighbours, key=score)
        best_dist = self.maze.cells[best[0]][best[1]].distance

        # If best reachable distance is INF, we're trapped (disconnected)
        if best_dist >= 9999:
            return None

        return best

    # ------------------------------------------------------------------
    # Visualisation helpers
    # ------------------------------------------------------------------

    def _update_display(self) -> None:
        """
        Update the mms simulator display with current flood-fill distances.
        """
        for col in self.maze.cells:
            for cell in col:
                dist = cell.distance
                if dist < 9999:
                    api.set_text(cell.x, cell.y, str(dist))
                    # Color gradient: goal=green, close=yellow, far=red
                    if dist == 0:
                        api.set_color(cell.x, cell.y, "G")
                    elif dist < 5:
                        api.set_color(cell.x, cell.y, "Y")
                    elif dist < 15:
                        api.set_color(cell.x, cell.y, "C")
                    else:
                        api.set_color(cell.x, cell.y, "B")
                else:
                    api.set_text(cell.x, cell.y, "?")
                    api.set_color(cell.x, cell.y, "r")

    def _color_goal_path(self) -> None:
        """
        Highlight the shortest path from start to goal in green.
        Uses BFS path tracing following minimum distance gradient.
        """
        # Trace back from current (goal) position toward origin
        x, y = self.robot.x, self.robot.y
        visited_trace: set[tuple[int, int]] = set()

        while self.maze.cells[x][y].distance > 0:
            api.set_color(x, y, "G")
            visited_trace.add((x, y))
            neighbours = self.maze.open_neighbours(x, y)
            if not neighbours:
                break
            # Move to neighbour with smallest distance
            nxt = min(neighbours, key=lambda p: self.maze.cells[p[0]][p[1]].distance)
            nx, ny = nxt
            if (nx, ny) in visited_trace:
                break  # avoid loops in case of distance ties
            x, y = nx, ny

        api.set_color(x, y, "G")  # Color the start

    # VERSIONE CON PENALITA' DI VISITA (da testare)
    def set_exploration_mode(self, enabled: bool):
        self.exploration_mode = enabled
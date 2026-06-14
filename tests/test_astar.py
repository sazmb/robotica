"""
Unit Tests — Incremental A* Algorithm
Tests for the A* planning logic in isolation.
Run with pytest tests/ -v
"""

from __future__ import annotations

import math
import pytest
from unittest.mock import patch

from core.maze import MazeMap, NORTH, EAST, SOUTH, WEST
from core.robot import RobotState


class TestAStarPlanning:
    """
    Test A* path planning in isolation (no simulator I/O).
    """

    def _make_solver(self, maze: MazeMap, robot: RobotState, weight: float = 1.0):
        with patch("core.simulator_api.log_info"), \
             patch("core.simulator_api.set_color"), \
             patch("core.simulator_api.set_text"), \
             patch("core.simulator_api.set_wall"), \
             patch("core.simulator_api.clear_all_color"), \
             patch("core.simulator_api.clear_all_text"):
            from algorithms.incremental_astar import IncrementalAStar
            solver = IncrementalAStar(maze, robot, heuristic_weight=weight)
        return solver

    def test_finds_path_in_open_maze(self):
        """A* should find a path in a fully open 4x4 maze."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)

        path = solver._astar(0, 0)
        assert path is not None, "A* should find a path in an open maze"
        assert path[0] == (0, 0), "Path should start at (0, 0)"
        assert path[-1] == (3, 3), "Path should end at goal (3, 3)"

    def test_path_length_in_open_maze(self):
        """Manhattan distance gives minimum path length in open maze."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)

        path = solver._astar(0, 0)
        assert path is not None
        # Minimum steps from (0,0) to (3,3) in open 4x4 maze = 6 (3 right + 3 up)
        assert len(path) - 1 == 6, f"Expected 6 steps, got {len(path)-1}"

    def test_no_path_fully_blocked(self):
        """A* should return None if goal is unreachable."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        # Build a wall ring around (3,3)
        maze.update_wall(3, 3, SOUTH, True)  # (3,3) <-> (3,2)
        maze.update_wall(3, 2, NORTH, True)  # same wall from other side
        maze.update_wall(2, 3, EAST, True)   # (2,3) <-> (3,3)
        maze.update_wall(3, 3, WEST, True)   # confirm west is blocked
        # (3,3) also has EAST and NORTH from boundary
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)
        path = solver._astar(0, 0)
        assert path is None, "Should return None when goal is unreachable"

    def test_path_avoids_walls(self):
        """A* path should not cross known walls."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        # Block the direct top path
        maze.update_wall(0, 0, NORTH, True)
        maze.update_wall(0, 1, SOUTH, True)
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)

        path = solver._astar(0, 0)
        assert path is not None
        # Verify no step crosses the blocked wall
        for i in range(len(path) - 1):
            cx, cy = path[i]
            nx, ny = path[i + 1]
            direction = maze.direction_to(cx, cy, nx, ny)
            assert direction is not None, "Path steps must be adjacent"
            assert not maze.has_wall(cx, cy, direction), \
                f"Path crosses wall at ({cx},{cy}) direction {direction}"

    def test_heuristic_is_admissible(self):
        """Heuristic must never overestimate actual cost."""
        maze = MazeMap(width=8, height=8, goal_cells=[(7, 7)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)

        for x in range(8):
            for y in range(8):
                h = solver._heuristic(x, y)
                # In an open maze, actual cost >= Manhattan distance
                # So h (= Manhattan) is admissible
                assert h >= 0, "Heuristic must be non-negative"
                assert h == abs(x - 7) + abs(y - 7), \
                    f"Heuristic mismatch at ({x},{y})"

    def test_weighted_astar_finds_path(self):
        """Weighted A* (w > 1) should still find a path."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot, weight=1.5)

        path = solver._astar(0, 0)
        assert path is not None
        assert path[-1] == (3, 3)

    def test_path_validation_valid(self):
        """A fresh path through an open maze should be valid."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)
        solver.current_path = solver._astar(0, 0) or []
        assert solver._path_is_valid()

    def test_path_validation_invalid_after_wall(self):
        """Path should be invalid after a wall is added on the path."""
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=0, y=0)
        solver = self._make_solver(maze, robot)
        solver.current_path = solver._astar(0, 0) or []

        # Add a wall that blocks the path
        if len(solver.current_path) >= 2:
            cx, cy = solver.current_path[0]
            nx, ny = solver.current_path[1]
            d = maze.direction_to(cx, cy, nx, ny)
            if d:
                maze.update_wall(cx, cy, d, True)
                assert not solver._path_is_valid()

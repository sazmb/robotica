"""
Unit Tests — Flood Fill Algorithm
Tests for the Flood Fill distance propagation logic.
Run with pytest tests/ -v
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from core.maze import MazeMap, NORTH, SOUTH, EAST, WEST
from core.robot import RobotState


class TestFloodFillDistancePropagation:
    """
    Test the flood-fill BFS distance computation in isolation.
    We patch out simulator I/O so no mms process is needed.
    """

    def _make_solver(self, maze: MazeMap, robot: RobotState):
        """Create a FloodFill solver with all simulator calls patched."""
        with patch("core.simulator_api.set_color"), \
             patch("core.simulator_api.set_text"), \
             patch("core.simulator_api.set_wall"), \
             patch("core.simulator_api.clear_all_color"), \
             patch("core.simulator_api.clear_all_text"), \
             patch("core.simulator_api.log_info"):
            from algorithms.flood_fill import FloodFill
            solver = FloodFill(maze, robot)
        return solver

    def test_goal_cell_distance_zero(self):
        maze = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        robot = RobotState()
        solver = self._make_solver(maze, robot)
        assert maze.cell(2, 2).distance == 0

    def test_adjacent_to_goal_distance_one(self):
        maze = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        robot = RobotState()
        solver = self._make_solver(maze, robot)
        # (2,1) is directly south of (2,2) and should be distance 1
        assert maze.cell(2, 1).distance == 1
        # (1,2) is directly west of (2,2)
        assert maze.cell(1, 2).distance == 1

    def test_start_cell_has_positive_distance(self):
        maze = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        robot = RobotState()
        solver = self._make_solver(maze, robot)
        start_dist = maze.cell(0, 0).distance
        assert start_dist > 0
        assert start_dist < 9999  # Should be reachable

    def test_wall_blocks_distance_propagation(self):
        """Adding a wall should increase distances on the blocked side."""
        maze_open = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        robot1 = RobotState()
        solver_open = self._make_solver(maze_open, robot1)
        dist_open = maze_open.cell(0, 2).distance

        maze_walled = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        # Add a wall that forces longer path
        maze_walled.update_wall(1, 2, EAST, True)
        robot2 = RobotState()
        solver_walled = self._make_solver(maze_walled, robot2)
        dist_walled = maze_walled.cell(0, 2).distance

        assert dist_walled >= dist_open


class TestFloodFillCellSelection:
    def test_choose_next_cell_picks_lowest_distance(self):
        maze = MazeMap(width=4, height=4, goal_cells=[(3, 3)])
        robot = RobotState(x=1, y=1)

        with patch("core.simulator_api.set_color"), \
             patch("core.simulator_api.set_text"), \
             patch("core.simulator_api.set_wall"), \
             patch("core.simulator_api.clear_all_color"), \
             patch("core.simulator_api.clear_all_text"), \
             patch("core.simulator_api.log_info"):
            from algorithms.flood_fill import FloodFill
            solver = FloodFill(maze, robot)

        next_cell = solver._choose_next_cell(1, 1)
        assert next_cell is not None
        # The chosen cell should have a smaller or equal distance than current
        chosen_dist = maze.cell(next_cell[0], next_cell[1]).distance
        current_dist = maze.cell(1, 1).distance
        assert chosen_dist <= current_dist

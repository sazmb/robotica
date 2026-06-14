"""
Unit Tests — MazeMap
Tests for the core maze representation module.
Run with pytest tests/ -v
"""

from __future__ import annotations

import pytest
import math
from core.maze import MazeMap, Cell, NORTH, SOUTH, EAST, WEST


# ---------------------------------------------------------------------------
# Cell tests
# ---------------------------------------------------------------------------

class TestCell:
    def test_initial_no_walls(self):
        c = Cell(x=0, y=0)
        for d in [NORTH, SOUTH, EAST, WEST]:
            assert not c.has_wall(d), f"Expected no wall on {d}"

    def test_set_and_has_wall(self):
        c = Cell(x=0, y=0)
        c.set_wall(NORTH)
        assert c.has_wall(NORTH)
        assert not c.has_wall(SOUTH)

    def test_clear_wall(self):
        c = Cell(x=2, y=3)
        c.set_wall(EAST)
        c.clear_wall(EAST)
        assert not c.has_wall(EAST)

    def test_is_open(self):
        c = Cell(x=1, y=1)
        c.set_wall(WEST)
        assert not c.is_open(WEST)
        assert c.is_open(EAST)

    def test_multiple_walls(self):
        c = Cell(x=0, y=0)
        c.set_wall(NORTH)
        c.set_wall(EAST)
        assert c.has_wall(NORTH)
        assert c.has_wall(EAST)
        assert not c.has_wall(SOUTH)
        assert not c.has_wall(WEST)


# ---------------------------------------------------------------------------
# MazeMap construction tests
# ---------------------------------------------------------------------------

class TestMazeMapConstruction:
    def test_default_dimensions(self):
        m = MazeMap()
        assert m.width == 16
        assert m.height == 16

    def test_custom_dimensions(self):
        m = MazeMap(width=8, height=8)
        assert m.width == 8
        assert m.height == 8

    def test_all_cells_created(self):
        m = MazeMap(width=4, height=4)
        for x in range(4):
            for y in range(4):
                c = m.cell(x, y)
                assert c.x == x
                assert c.y == y

    def test_boundary_walls_south(self):
        m = MazeMap(width=4, height=4)
        for x in range(4):
            assert m.cell(x, 0).has_wall(SOUTH), f"Missing south boundary at ({x}, 0)"

    def test_boundary_walls_north(self):
        m = MazeMap(width=4, height=4)
        for x in range(4):
            assert m.cell(x, 3).has_wall(NORTH), f"Missing north boundary at ({x}, 3)"

    def test_boundary_walls_west(self):
        m = MazeMap(width=4, height=4)
        for y in range(4):
            assert m.cell(0, y).has_wall(WEST), f"Missing west boundary at (0, {y})"

    def test_boundary_walls_east(self):
        m = MazeMap(width=4, height=4)
        for y in range(4):
            assert m.cell(3, y).has_wall(EAST), f"Missing east boundary at (3, {y})"

    def test_out_of_bounds_raises(self):
        m = MazeMap(width=4, height=4)
        with pytest.raises(IndexError):
            m.cell(4, 0)
        with pytest.raises(IndexError):
            m.cell(-1, 0)


# ---------------------------------------------------------------------------
# Wall update and propagation tests
# ---------------------------------------------------------------------------

class TestWallUpdates:
    def test_update_wall_propagates(self):
        m = MazeMap(width=4, height=4)
        m.update_wall(1, 1, NORTH, True)
        # Cell (1,1) should have NORTH wall
        assert m.cell(1, 1).has_wall(NORTH)
        # Cell (1,2) should have SOUTH wall (propagated)
        assert m.cell(1, 2).has_wall(SOUTH)

    def test_update_wall_returns_new_info(self):
        m = MazeMap(width=4, height=4)
        changed = m.update_wall(2, 2, EAST, True)
        assert changed  # First time → new information
        changed_again = m.update_wall(2, 2, EAST, True)
        assert not changed_again  # Same info → not new

    def test_clear_wall_propagates(self):
        m = MazeMap(width=4, height=4)
        m.update_wall(1, 1, EAST, True)
        assert m.cell(1, 1).has_wall(EAST)
        assert m.cell(2, 1).has_wall(WEST)
        m.update_wall(1, 1, EAST, False)
        assert not m.cell(1, 1).has_wall(EAST)
        assert not m.cell(2, 1).has_wall(WEST)


# ---------------------------------------------------------------------------
# Neighbour traversal tests
# ---------------------------------------------------------------------------

class TestNeighbours:
    def test_open_neighbours_no_walls(self):
        m = MazeMap(width=3, height=3)
        # Cell (1,1) is interior — no interior walls set
        neighbours = m.open_neighbours(1, 1)
        # Should have 4 neighbours: (1,2), (1,0), (2,1), (0,1)
        assert len(neighbours) == 4

    def test_open_neighbours_with_wall(self):
        m = MazeMap(width=3, height=3)
        m.update_wall(1, 1, NORTH, True)
        neighbours = m.open_neighbours(1, 1)
        assert (1, 2) not in neighbours
        assert len(neighbours) == 3

    def test_open_neighbours_corner(self):
        """Corner cells (0,0) should have at most 2 open neighbours (boundary walls)."""
        m = MazeMap(width=4, height=4)
        neighbours = m.open_neighbours(0, 0)
        # Boundary walls block SOUTH and WEST; NORTH and EAST are open
        assert (0, -1) not in neighbours
        assert (-1, 0) not in neighbours


# ---------------------------------------------------------------------------
# Distance and heuristic tests
# ---------------------------------------------------------------------------

class TestDistances:
    def test_reset_distances_goal_zero(self):
        m = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        m.reset_distances()
        assert m.cell(2, 2).distance == 0

    def test_reset_distances_non_goal_inf(self):
        m = MazeMap(width=4, height=4, goal_cells=[(2, 2)])
        m.reset_distances()
        assert m.cell(0, 0).distance == 9999

    def test_manhattan_distance(self):
        m = MazeMap(width=8, height=8, goal_cells=[(4, 4)])
        assert m.manhattan_distance(4, 4) == 0
        assert m.manhattan_distance(0, 0) == 8
        assert m.manhattan_distance(4, 0) == 4
        assert m.manhattan_distance(0, 4) == 4

    def test_manhattan_distance_multiple_goals(self):
        m = MazeMap(width=8, height=8, goal_cells=[(3, 3), (4, 4)])
        # Nearest goal from (3, 3) is (3,3) itself
        assert m.manhattan_distance(3, 3) == 0
        # Nearest goal from (5, 5): min(|5-3|+|5-3|, |5-4|+|5-4|) = min(4, 2) = 2
        assert m.manhattan_distance(5, 5) == 2

    def test_is_goal(self):
        m = MazeMap(width=8, height=8, goal_cells=[(3, 3), (4, 4)])
        assert m.is_goal(3, 3)
        assert m.is_goal(4, 4)
        assert not m.is_goal(0, 0)


# ---------------------------------------------------------------------------
# In-bounds test
# ---------------------------------------------------------------------------

class TestInBounds:
    def test_in_bounds(self):
        m = MazeMap(width=4, height=4)
        assert m.in_bounds(0, 0)
        assert m.in_bounds(3, 3)
        assert not m.in_bounds(-1, 0)
        assert not m.in_bounds(0, 4)
        assert not m.in_bounds(4, 0)

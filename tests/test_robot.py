"""
Unit Tests — RobotState
========================
Tests for the robot state representation module.

Note: Tests that involve simulator I/O (move_forward, turn_right, etc.)
are integration tests and require the mms simulator to be running.
Only pure-logic unit tests are included here.

Run with:
    pytest tests/ -v
"""

from __future__ import annotations

import pytest
from core.robot import RobotState, TURN_RIGHT, TURN_LEFT, TURNS_TO_FACE
from core.maze import NORTH, SOUTH, EAST, WEST


class TestHeadingTables:
    """Verify rotation lookup tables are self-consistent."""

    def test_turn_right_cycle(self):
        heading = NORTH
        for expected in [EAST, SOUTH, WEST, NORTH]:
            heading = TURN_RIGHT[heading]
            assert heading == expected

    def test_turn_left_cycle(self):
        heading = NORTH
        for expected in [WEST, SOUTH, EAST, NORTH]:
            heading = TURN_LEFT[heading]
            assert heading == expected

    def test_turns_to_face_diagonal(self):
        """Facing yourself requires 0 turns."""
        for d in [NORTH, EAST, SOUTH, WEST]:
            assert TURNS_TO_FACE[d][d] == 0

    def test_turns_to_face_opposite_is_2(self):
        assert TURNS_TO_FACE[NORTH][SOUTH] == 2
        assert TURNS_TO_FACE[EAST][WEST] == 2
        assert TURNS_TO_FACE[SOUTH][NORTH] == 2
        assert TURNS_TO_FACE[WEST][EAST] == 2

    def test_turns_to_face_right_is_1(self):
        assert TURNS_TO_FACE[NORTH][EAST] == 1
        assert TURNS_TO_FACE[EAST][SOUTH] == 1
        assert TURNS_TO_FACE[SOUTH][WEST] == 1
        assert TURNS_TO_FACE[WEST][NORTH] == 1

    def test_turns_to_face_left_is_3(self):
        assert TURNS_TO_FACE[NORTH][WEST] == 3
        assert TURNS_TO_FACE[EAST][NORTH] == 3
        assert TURNS_TO_FACE[SOUTH][EAST] == 3
        assert TURNS_TO_FACE[WEST][SOUTH] == 3


class TestRobotStateInit:
    def test_default_position(self):
        robot = RobotState()
        assert robot.x == 0
        assert robot.y == 0
        assert robot.heading == NORTH

    def test_custom_position(self):
        robot = RobotState(x=3, y=5, heading=EAST)
        assert robot.x == 3
        assert robot.y == 5
        assert robot.heading == EAST

    def test_initial_visit_recorded(self):
        robot = RobotState(x=2, y=2)
        assert robot.visit_count(2, 2) == 1

    def test_initial_counters_zero(self):
        robot = RobotState()
        assert robot.move_count == 0
        assert robot.turn_count == 0


class TestRobotStateLogic:
    def test_position_property(self):
        robot = RobotState(x=4, y=7)
        assert robot.position == (4, 7)

    def test_facing(self):
        robot = RobotState(heading=EAST)
        assert robot.facing(EAST)
        assert not robot.facing(NORTH)

    def test_unique_cells_visited(self):
        robot = RobotState(x=0, y=0)
        robot._record_visit(1, 0)
        robot._record_visit(2, 0)
        assert robot.unique_cells_visited() == 3

    def test_total_cost(self):
        robot = RobotState()
        robot.move_count = 5
        robot.turn_count = 3
        assert robot.total_cost() == 8

    def test_relative_direction_front(self):
        robot = RobotState(heading=NORTH)
        assert robot.relative_direction(NORTH) == "front"

    def test_relative_direction_right(self):
        robot = RobotState(heading=NORTH)
        assert robot.relative_direction(EAST) == "right"

    def test_relative_direction_back(self):
        robot = RobotState(heading=NORTH)
        assert robot.relative_direction(SOUTH) == "back"

    def test_relative_direction_left(self):
        robot = RobotState(heading=NORTH)
        assert robot.relative_direction(WEST) == "left"

    def test_absolute_direction_front(self):
        robot = RobotState(heading=EAST)
        assert robot.absolute_direction("front") == EAST

    def test_absolute_direction_right_from_east(self):
        robot = RobotState(heading=EAST)
        assert robot.absolute_direction("right") == SOUTH

    def test_update_after_turn_right(self):
        robot = RobotState(heading=NORTH)
        robot.update_after_turn_right()
        assert robot.heading == EAST
        assert robot.turn_count == 1

    def test_update_after_turn_left(self):
        robot = RobotState(heading=NORTH)
        robot.update_after_turn_left()
        assert robot.heading == WEST
        assert robot.turn_count == 1

    def test_reset(self):
        robot = RobotState(x=5, y=5, heading=EAST)
        robot.move_count = 10
        robot.turn_count = 5
        robot.reset(start_x=0, start_y=0, heading=NORTH)
        assert robot.x == 0
        assert robot.y == 0
        assert robot.heading == NORTH
        assert robot.move_count == 0
        assert robot.turn_count == 0

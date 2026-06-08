"""
Robot State Representation
===========================
Tracks the robot's position, heading, and exploration history within
the Micromouse maze.  Provides utilities for coordinate updates,
orientation transformations, and move execution.

Coordinate convention (mms simulator):
  - Origin (0, 0) at bottom-left
  - x increases rightward, y increases upward

Heading convention:
  - NORTH (N): +y direction
  - EAST  (E): +x direction
  - SOUTH (S): -y direction
  - WEST  (W): -x direction

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Optional

from core.maze import NORTH, SOUTH, EAST, WEST, ALL_DIRS, DIR_DELTA, OPPOSITE
import core.simulator_api as api


# ---------------------------------------------------------------------------
# Heading rotation tables
# ---------------------------------------------------------------------------

# Result of turning RIGHT from each heading
TURN_RIGHT: dict[str, str] = {
    NORTH: EAST,
    EAST:  SOUTH,
    SOUTH: WEST,
    WEST:  NORTH,
}

# Result of turning LEFT from each heading
TURN_LEFT: dict[str, str] = {
    NORTH: WEST,
    WEST:  SOUTH,
    SOUTH: EAST,
    EAST:  NORTH,
}

# Number of right-turns needed to go from heading A to heading B
TURNS_TO_FACE: dict[str, dict[str, int]] = {
    NORTH: {NORTH: 0, EAST: 1, SOUTH: 2, WEST: 3},
    EAST:  {NORTH: 3, EAST: 0, SOUTH: 1, WEST: 2},
    SOUTH: {NORTH: 2, EAST: 3, SOUTH: 0, WEST: 1},
    WEST:  {NORTH: 1, EAST: 2, SOUTH: 3, WEST: 0},
}


@dataclass
class RobotState:
    """
    Complete state of the Micromouse robot.

    Attributes:
        x (int): Current column position.
        y (int): Current row position.
        heading (str): Current cardinal direction the robot faces.
        move_count (int): Total number of forward moves performed.
        turn_count (int): Total number of 90° turns performed.
        cell_visits (dict): Maps (x,y) → number of times visited.
        path_history (list): Ordered sequence of all cells visited.
        exploration_complete (bool): Set when the algorithm declares
            exploration done.
    """
    x: int = 0
    y: int = 0
    heading: str = NORTH
    move_count: int = 0
    turn_count: int = 0
    cell_visits: dict[tuple[int, int], int] = field(default_factory=dict)
    path_history: list[tuple[int, int]] = field(default_factory=list)
    exploration_complete: bool = False

    def __post_init__(self) -> None:
        # Record the starting cell
        self._record_visit(self.x, self.y)

    # ------------------------------------------------------------------
    # Visit tracking
    # ------------------------------------------------------------------

    def _record_visit(self, x: int, y: int) -> None:
        """Update internal visit records for (x, y)."""
        key = (x, y)
        self.cell_visits[key] = self.cell_visits.get(key, 0) + 1
        self.path_history.append(key)

    def visit_count(self, x: int, y: int) -> int:
        """Return how many times the robot has visited cell (x, y)."""
        return self.cell_visits.get((x, y), 0)

    # ------------------------------------------------------------------
    # Orientation queries
    # ------------------------------------------------------------------

    @property
    def position(self) -> tuple[int, int]:
        """Current (x, y) position as a tuple."""
        return (self.x, self.y)

    def facing(self, direction: str) -> bool:
        """Return True if the robot currently faces `direction`."""
        return self.heading == direction

    def relative_direction(self, absolute_dir: str) -> str:
        """
        Convert an absolute direction to a direction relative to the robot.

        Args:
            absolute_dir: One of 'N', 'S', 'E', 'W'.

        Returns:
            'front', 'right', 'back', or 'left' relative to current heading.
        """
        heading_to_index = {NORTH: 0, EAST: 1, SOUTH: 2, WEST: 3}
        diff = (heading_to_index[absolute_dir] - heading_to_index[self.heading]) % 4
        return ["front", "right", "back", "left"][diff]

    def absolute_direction(self, relative: str) -> str:
        """
        Convert a relative direction to an absolute cardinal direction.

        Args:
            relative: One of 'front', 'right', 'back', 'left'.

        Returns:
            Absolute direction 'N', 'S', 'E', or 'W'.
        """
        heading_index = {NORTH: 0, EAST: 1, SOUTH: 2, WEST: 3}
        rel_offset = {"front": 0, "right": 1, "back": 2, "left": 3}
        idx = (heading_index[self.heading] + rel_offset[relative]) % 4
        return [NORTH, EAST, SOUTH, WEST][idx]

    # ------------------------------------------------------------------
    # Movement — coordinates update ONLY (no simulator I/O here)
    # ------------------------------------------------------------------

    def update_after_move(self) -> None:
        """
        Update internal coordinates after a successful forward move.
        The simulator has already physically moved the robot.
        """
        dx, dy = DIR_DELTA[self.heading]
        self.x += dx
        self.y += dy
        self.move_count += 1
        self._record_visit(self.x, self.y)
        api.log_info(f"Robot moved to ({self.x}, {self.y}) facing {self.heading}")

    def update_after_turn_right(self) -> None:
        """Update heading after a right turn."""
        self.heading = TURN_RIGHT[self.heading]
        self.turn_count += 1

    def update_after_turn_left(self) -> None:
        """Update heading after a left turn."""
        self.heading = TURN_LEFT[self.heading]
        self.turn_count += 1

    # ------------------------------------------------------------------
    # High-level movement — simulator I/O + state update
    # ------------------------------------------------------------------

    def move_forward(self) -> bool:
        """
        Command the simulator to move forward one cell and update state.

        Returns:
            True on success, False on crash.
        """
        success = api.move_forward()
        if success:
            self.update_after_move()
        return success

    def turn_right(self) -> None:
        """Command simulator to turn right and update heading."""
        api.turn_right()
        self.update_after_turn_right()

    def turn_left(self) -> None:
        """Command simulator to turn left and update heading."""
        api.turn_left()
        self.update_after_turn_left()

    def face_direction(self, target: str) -> None:
        """
        Rotate the robot to face `target` using the fewest turns.

        Args:
            target: Desired absolute heading ('N', 'S', 'E', 'W').
        """
        n_right = TURNS_TO_FACE[self.heading][target]
        if n_right == 0:
            return
        if n_right == 1:
            self.turn_right()
        elif n_right == 2:
            # 180° — two rights
            self.turn_right()
            self.turn_right()
        elif n_right == 3:
            # Faster to turn left once
            self.turn_left()

    # ------------------------------------------------------------------
    # Sensing — returns absolute directions of walls using robot sensors
    # ------------------------------------------------------------------

    def sense_walls(self) -> dict[str, bool]:
        """
        Read the three proximity sensors and return wall presence for
        all four absolute directions around the current cell.

        Note: The robot can sense front, left, and right. The back
        wall is inferred (cannot be directly sensed by standard sensors;
        we assume a wall behind only if it was previously recorded).

        Returns:
            Dict mapping absolute direction -> bool (True = wall present).
        """
        front_abs = self.heading
        right_abs = TURN_RIGHT[self.heading]
        left_abs  = TURN_LEFT[self.heading]
        back_abs  = OPPOSITE[self.heading]

        return {
            front_abs: api.wall_front(),
            right_abs: api.wall_right(),
            left_abs:  api.wall_left(),
            # Back wall cannot be directly sensed; caller should rely on map
            back_abs:  False,
        }

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def total_cost(self) -> int:
        """Approximate total navigation cost = moves + turns."""
        return self.move_count + self.turn_count

    def unique_cells_visited(self) -> int:
        """Number of distinct cells the robot has entered."""
        return len(self.cell_visits)

    def summary(self) -> str:
        """Return a human-readable summary of the robot state."""
        return (
            f"Position: ({self.x}, {self.y})  Heading: {self.heading}  "
            f"Moves: {self.move_count}  Turns: {self.turn_count}  "
            f"Unique cells: {self.unique_cells_visited()}"
        )

    def snapshot(self) -> dict:
        """
        Capture a point-in-time copy of the robot's performance counters.

        Used by the orchestrator to compute per-phase metric deltas without
        resetting the shared robot state between phases.

        Returns:
            Dict with keys:
              'moves'   – current move_count
              'turns'   – current turn_count
              'visited' – frozenset of (x, y) cells visited so far
        """
        return {
            "moves": self.move_count,
            "turns": self.turn_count,
            "visited": frozenset(self.cell_visits.keys()),
        }

    def reset(self, start_x: int = 0, start_y: int = 0, heading: str = NORTH) -> None:
        """
        Reset the robot state for a fresh run (after simulator reset).

        Args:
            start_x: Starting column (default 0).
            start_y: Starting row (default 0).
            heading: Starting orientation (default NORTH).
        """
        self.x = start_x
        self.y = start_y
        self.heading = heading
        self.move_count = 0
        self.turn_count = 0
        self.cell_visits = {}
        self.path_history = []
        self.exploration_complete = False
        self._record_visit(self.x, self.y)

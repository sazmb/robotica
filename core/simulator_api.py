"""
Simulator API Interface Layer
==============================
This module provides a clean, isolated interface to the mms (Mackorone Micromouse
Simulator) via stdin/stdout communication protocol.

The mms simulator communicates with the algorithm process via:
  - stdout: Commands sent FROM the algorithm TO the simulator
  - stdin:  Responses sent FROM the simulator TO the algorithm
  - stderr: Logging (does not interfere with simulator communication)

All simulator-specific I/O is encapsulated here so that algorithmic modules
never directly interact with sys.stdin / sys.stdout.

API Reference:
  https://github.com/mackorone/mms#mouse-api

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import sys
import logging
from typing import Optional

# ---------------------------------------------------------------------------
# Logger — all debug output goes to stderr so stdout stays clean for the sim
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)
if not log.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_handler)
    log.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Low-level communication helpers
# ---------------------------------------------------------------------------

def _send(command: str) -> None:
    """
    Send a command string to the mms simulator via stdout.

    Args:
        command: The raw command string (without trailing newline).
    """
    sys.stdout.write(command + "\n")
    sys.stdout.flush()
    log.debug("SEND: %s", command)


def _recv() -> str:
    """
    Read a single response line from the mms simulator via stdin.

    Returns:
        The response string, stripped of whitespace.

    Raises:
        EOFError: If the simulator closes the connection unexpectedly.
    """
    response = sys.stdin.readline().strip()
    log.debug("RECV: %s", response)
    if response == "":
        raise EOFError("Simulator connection closed unexpectedly.")
    return response


def _command_int(cmd: str) -> int:
    """Send command and return integer response."""
    _send(cmd)
    return int(_recv())


def _command_bool(cmd: str) -> bool:
    """Send command and return boolean response."""
    _send(cmd)
    return _recv() == "true"


def _command_str(cmd: str) -> str:
    """Send command and return raw string response."""
    _send(cmd)
    return _recv()


# ---------------------------------------------------------------------------
# Maze dimension queries
# ---------------------------------------------------------------------------

def maze_width() -> int:
    """
    Query the maze width from the simulator.

    Returns:
        Number of columns in the maze (typically 16).
    """
    return _command_int("mazeWidth")


def maze_height() -> int:
    """
    Query the maze height from the simulator.

    Returns:
        Number of rows in the maze (typically 16).
    """
    return _command_int("mazeHeight")


# ---------------------------------------------------------------------------
# Wall sensing
# ---------------------------------------------------------------------------

def wall_front(num_half_steps: int = 1) -> bool:
    """
    Check whether there is a wall directly in front of the robot.

    Args:
        num_half_steps: How many half-steps ahead to check (default 1).

    Returns:
        True if a wall exists at that position, False otherwise.
    """
    return _command_bool(f"wallFront {num_half_steps}")


def wall_right(num_half_steps: int = 1) -> bool:
    """
    Check whether there is a wall to the right of the robot.

    Args:
        num_half_steps: How many half-steps to the right to check (default 1).

    Returns:
        True if a wall exists, False otherwise.
    """
    return _command_bool(f"wallRight {num_half_steps}")


def wall_left(num_half_steps: int = 1) -> bool:
    """
    Check whether there is a wall to the left of the robot.

    Args:
        num_half_steps: How many half-steps to the left to check (default 1).

    Returns:
        True if a wall exists, False otherwise.
    """
    return _command_bool(f"wallLeft {num_half_steps}")


def wall_back(num_half_steps: int = 1) -> bool:
    """
    Check whether there is a wall behind the robot.

    Args:
        num_half_steps: How many half-steps behind to check (default 1).

    Returns:
        True if a wall exists, False otherwise.
    """
    return _command_bool(f"wallBack {num_half_steps}")


# ---------------------------------------------------------------------------
# Movement commands
# ---------------------------------------------------------------------------

def move_forward(distance: int = 1) -> bool:
    """
    Move the robot forward by `distance` full steps.

    Args:
        distance: Number of cells to advance (default 1).

    Returns:
        True if move succeeded (simulator replied 'ack'),
        False if the robot crashed (simulator replied 'crash').
    """
    # move_forward was already correct, as it consumes the string to check for a crash!
    response = _command_str(f"moveForward {distance}")
    if response == "crash":
        log.warning("moveForward resulted in CRASH! distance=%d", distance)
        return False
    return True  # "ack"


def turn_right() -> None:
    """
    Rotate the robot 90° clockwise (to the right).
    Consumes the 'ack' response from the simulator to prevent buffer desync.
    """
    _command_str("turnRight")


def turn_left() -> None:
    """
    Rotate the robot 90° counter-clockwise (to the left).
    Consumes the 'ack' response from the simulator to prevent buffer desync.
    """
    _command_str("turnLeft")


def turn_right_45() -> None:
    """
    Rotate the robot 45° clockwise.
    Consumes the 'ack' response from the simulator to prevent buffer desync.
    """
    _command_str("turnRight45")


def turn_left_45() -> None:
    """
    Rotate the robot 45° counter-clockwise.
    Consumes the 'ack' response from the simulator to prevent buffer desync.
    """
    _command_str("turnLeft45")




# ---------------------------------------------------------------------------
# Wall display commands (for visualization only — does not affect logic)
# ---------------------------------------------------------------------------

def set_wall(x: int, y: int, direction: str) -> None:
    """
    Display a wall on the simulator UI at cell (x, y) in the given direction.

    Args:
        x: Column index (0-based, left = 0).
        y: Row index (0-based, bottom = 0).
        direction: One of 'n', 's', 'e', 'w' (case-insensitive).
    """
    _send(f"setWall {x} {y} {direction.lower()}")


def clear_wall(x: int, y: int, direction: str) -> None:
    """Remove a displayed wall from the simulator UI."""
    _send(f"clearWall {x} {y} {direction.lower()}")


# ---------------------------------------------------------------------------
# Cell colour commands
# ---------------------------------------------------------------------------

# Supported colour characters (per mms documentation)
# R=red, G=green, B=blue, Y=yellow, W=white, C=cyan, M=magenta,
# O=orange, P=pink (rose), T=tan, s=slate, A=ash, a=dark_ash,
# r=dark_red, g=dark_green, b=dark_blue, y=dark_yellow, c=dark_cyan, m=dark_magenta

def set_color(x: int, y: int, color: str) -> None:
    """
    Set the background color of cell (x, y) in the simulator.

    Args:
        x: Column index.
        y: Row index.
        color: Single character color code (e.g. 'G', 'R', 'B', 'Y', 'C').
    """
    _send(f"setColor {x} {y} {color}")


def clear_color(x: int, y: int) -> None:
    """Clear the color of a specific cell."""
    _send(f"clearColor {x} {y}")


def clear_all_color() -> None:
    """Clear the color of all cells in the maze."""
    _send("clearAllColor")


# ---------------------------------------------------------------------------
# Cell text commands
# ---------------------------------------------------------------------------

def set_text(x: int, y: int, text: str) -> None:
    """
    Display ASCII text on cell (x, y) in the simulator.

    Args:
        x: Column index.
        y: Row index.
        text: Text string to display (short strings recommended).
    """
    _send(f"setText {x} {y} {text}")


def clear_text(x: int, y: int) -> None:
    """Clear the text on a specific cell."""
    _send(f"clearText {x} {y}")


def clear_all_text() -> None:
    """Clear text from all cells."""
    _send("clearAllText")


# ---------------------------------------------------------------------------
# Reset handling
# ---------------------------------------------------------------------------

def was_reset() -> bool:
    """
    Check whether the simulator reset button was pressed.

    Returns:
        True if a reset event is pending.
    """
    return _command_bool("wasReset")


def ack_reset() -> None:
    """
    Acknowledge a reset event so the robot can restart exploration.
    Must be called after was_reset() returns True.
    Consumes the 'ack' response from the simulator to prevent buffer desync.
    """
    _command_str("ackReset")

# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_stat(stat: str) -> str:
    """
    Retrieve a simulator statistic.

    Args:
        stat: Name of the stat (e.g. 'total-distance', 'total-turns').

    Returns:
        The stat value as a string (caller parses to int/float as needed).
    """
    return _command_str(f"getStat {stat}")


# ---------------------------------------------------------------------------
# Convenience logging helper
# ---------------------------------------------------------------------------

def log_info(message: str) -> None:
    """
    Write an informational message to stderr (safe during simulation).

    Args:
        message: The log message.
    """
    sys.stderr.write(f"[INFO] {message}\n")
    sys.stderr.flush()


def log_error(message: str) -> None:
    """
    Write an error message to stderr.

    Args:
        message: The error message.
    """
    sys.stderr.write(f"[ERROR] {message}\n")
    sys.stderr.flush()

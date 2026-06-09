# Maze Files

Place custom `.maz`or `.txt` maze files in this directory.

## Format

The mms simulator uses a simple text-based maze format.
Each cell is described by its wall configuration.

See the [mms documentation](https://github.com/mackorone/mms#maze-files)
for the exact format specification.

## Example Mazes

This directory contains various `.txt` files representing mazes of different typologies:
- `competition` — Sample competition-style mazes
- `dead_end` — Heavy dead-end mazes to stress-test backtracking
- `multiple_path` — Mazes with multiple paths to the goal
- `open_area` — Sparse walls to test heuristic efficiency
- `symmetric` — Symmetric mazes

Refer to `names.txt` for a complete list of all maze files and their corresponding typologies.

To use a custom maze in the simulator:
1. Launch the mms simulator
2. Go to **File → Open Maze**
3. Select your maze file
4. Click **Run** to start the algorithm

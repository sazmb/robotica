# Maze Files

Place custom `.maz` maze files in this directory.

## Format

The mms simulator uses a simple text-based maze format.
Each cell is described by its wall configuration.

See the [mms documentation](https://github.com/mackorone/mms#maze-files)
for the exact format specification.

## Example Mazes

- `simple.maz` — A basic 16×16 maze for initial testing
- `dead_ends.maz` — Heavy dead-end maze to stress-test backtracking
- `open_field.maz` — Sparse walls to test heuristic efficiency
- `competition.maz` — Sample competition-style maze

To use a custom maze in the simulator:
1. Launch the mms simulator
2. Go to **File → Open Maze**
3. Select your `.maz` file
4. Click **Run** to start the algorithm

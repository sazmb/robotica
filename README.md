# 🐭 Micromouse Maze Solver

> A research-grade implementation of two maze-solving algorithms for the [mms Micromouse Simulator](https://github.com/mackorone/mms) by Mackorone.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Simulator](https://img.shields.io/badge/Simulator-mms-orange?style=flat)

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture](#-architecture)
3. [Installation](#-installation)
4. [Simulator Setup](#-simulator-setup)
5. [Running the Algorithms](#-running-the-algorithms)
6. [Running Benchmarks](#-running-benchmarks)
7. [Metrics Explained](#-metrics-explained)
8. [Experimental Analysis](#-experimental-analysis)
9. [Project Structure](#-project-structure)
10. [Future Improvements](#-future-improvements)

---

## 🎯 Project Overview

This project implements a complete **Micromouse maze-solving system** consisting of:

| Component | Description |
|-----------|-------------|
| **Flood Fill** | Classic BFS-distance propagation strategy — fast, reliable, widely used in competitions |
| **Incremental A\*** | Online replanning strategy inspired by LPA* and D* Lite — heuristic-guided, adaptive |
| **Maze Map** | Efficient bitmask-based internal representation of a 16×16 maze |
| **Robot State** | Full robot pose tracker (position, heading, move/turn history) |
| **Simulator API** | Clean stdin/stdout interface to the mms simulator |
| **Evaluation Framework** | Metrics collection, CSV/JSON export, statistical analysis |
| **Visualisation** | Publication-quality matplotlib plots (bar charts, heatmaps, scatter plots) |
| **Unit Tests** | pytest-based test suite covering all core modules |

The robot operates in a **partially observable** 16×16 maze: it starts with no prior map knowledge and builds an internal representation incrementally through wall sensors.

### Key Constraints
- ✅ No prior maze knowledge assumed
- ✅ Walls discovered incrementally via sensors
- ✅ Online replanning when new walls are found
- ✅ Compatible with the mms simulator protocol (stdin/stdout)
- ✅ Reproducible and scientifically evaluable

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   mms Simulator                     │
│                (external process)                   │
└────────────────┬────────────────────────────────────┘
                 │ stdin / stdout
┌────────────────▼────────────────────────────────────┐
│              simulator_api.py                       │
│     (isolated I/O layer — no algo logic here)       │
└─────┬──────────────────────────────────┬────────────┘
      │                                  │
┌─────▼──────┐                  ┌────────▼───────────┐
│  maze.py   │                  │     robot.py        │
│ (MazeMap)  │◄─────────────────│  (RobotState)       │
│ bitmask    │                  │  pose + history     │
│ walls      │                  └────────┬────────────┘
│ distances  │                           │
└─────┬──────┘                           │
      │                                  │
┌─────▼──────────────────────────────────▼────────────┐
│            Algorithms Layer                         │
│   ┌──────────────────┐  ┌──────────────────────┐   │
│   │  flood_fill.py   │  │ incremental_astar.py  │   │
│   │  BFS distance    │  │  A* + replanning      │   │
│   │  propagation     │  │  heapq priority queue │   │
│   └──────────────────┘  └──────────────────────┘   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│            Evaluation Layer                         │
│   metrics.py   benchmark.py   plotting.py           │
│   (RunMetrics) (BenchmarkRunner) (MazePlotter)      │
└─────────────────────────────────────────────────────┘
```

---

## 💻 Installation

### Prerequisites

- Python 3.11 or higher
- [mms simulator](https://github.com/mackorone/mms/releases) (Windows/macOS/Linux binary)

### Steps

```bash
# 1. Clone or download this repository
git clone <your-repo-url>
cd robotica_proposta_1

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

**Core runtime has ZERO external dependencies** — only the Python 3.11+ standard library is required to run the algorithms with the mms simulator. `matplotlib` and `numpy` are only needed for offline plot generation.

---

## 🖥️ Simulator Setup

### Download mms

1. Go to the [mms releases page](https://github.com/mackorone/mms/releases)
2. Download the binary for your platform:
   - **Windows**: `windows.zip` → extract → run `mms/mms.exe`
   - **macOS**: `macos.zip` → extract → run `mms.app`
   - **Linux**: `linux.zip` → run `mms-x86_64.AppImage`

> ⚠️ **Windows**: If you see a SmartScreen warning, click "More info" → "Run anyway".

### Configure the Simulator

1. Launch `mms.exe` (or equivalent)
2. Click the **"+"** button to add a new algorithm
3. Fill in the configuration:
   - **Name**: `FloodFill` (or `IncrementalAStar`)
   - **Directory**: the full path to `robotica`
   - **Build command**: *(leave empty for Python)*
   - **Run command**: `python main.py --algorithm flood_fill`

4. Click **Build** (skip for Python), then **Run**

---

## 🚀 Running the Algorithms

### Flood Fill

```bash
# In the mms simulator Run command:
python main.py --algorithm flood_fill

# Or directly (for testing argument parsing):
python main.py --algorithm flood_fill --maze-name test_maze_1 --run-index 0
```

### Incremental A*

```bash
# Standard A* (heuristic weight = 1.0)
python main.py --algorithm astar

# Weighted A* (faster, slightly suboptimal paths)
python main.py --algorithm astar --weight 1.5
```

### Command-Line Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--algorithm` | `-a` | `flood_fill` | Algorithm to use (`flood_fill` \| `astar`) |
| `--maze-name` | `-m` | `default` | Label for the maze (logged in metrics) |
| `--run-index` | `-r` | `0` | Run number for repeated experiments |
| `--no-save` | — | off | Disable metrics persistence |
| `--weight` | — | `1.0` | A* heuristic weight (≥1.0) |

### Simulator Colour Legend

| Colour | Meaning |
|--------|----------|
| 🟩 Green | Goal cell / optimal path |
| 🟡 Yellow | Low distance / close to goal |
| 🔵 Blue | Higher distance value |
| ⬜ White | Unreachable / unknown |
| 🔵 Cyan | Visited cell (A* display) |

---

## 📊 Running Benchmarks

### Collecting Data

Run both algorithms multiple times in the simulator (press the **Reset** button between runs). Metrics are auto-saved to `logs/` after each run:

```
logs/
├── floodfill_results.json
└── incrementalastar_results.json
```

### Offline Analysis

You can run the included `analyse_results.py` script to automatically load JSON results, perform statistical analysis, and generate a markdown report.

```bash
# Run analysis on logs/ directory (default)
python analyse_results.py

# Run analysis on a specific logs directory and output to another directory
python analyse_results.py --logs-dir custom_logs --output-dir my_results
```

### Generating Plots

```python
from evaluation.plotting import plot_from_json

plot_from_json(
    "logs/floodfill_results.json",
    "logs/incrementalastar_results.json",
    output_dir="logs/plots",
)
```

Plots are saved as high-resolution PNG files in `logs/plots/`.

---

## 📈 Metrics Explained

| Metric | Description | Units |
|--------|-------------|-------|
| `visited_cells` | Distinct cells entered by the robot | cells |
| `exploration_ratio` | `visited_cells / total_cells` | fraction |
| `final_path_length` | Shortest known path from start to goal | steps |
| `total_moves` | Total forward movement commands | count |
| `total_turns` | Total 90° turn commands | count |
| `elapsed_seconds` | Wall-clock runtime | seconds |
| `replan_count` | Number of path replanning events | count |
| `new_walls_found` | New wall discoveries during run | count |
| `turn_ratio` | `turns / (moves + turns)` | fraction |
| `moves_per_cell` | Average moves per unique cell visited | ratio |

---

## 🔬 Experimental Analysis

### Flood Fill

**Strengths:**
- Guaranteed to find the goal if one exists (complete)
- Very fast BFS propagation — O(W×H) per re-flood
- Simple, highly debuggable
- Excellent for competition use (battle-tested)
- Low memory footprint (one integer per cell)

**Weaknesses:**
- May visit many cells before finding the shortest path
- Uniform cost assumption (all moves equal weight)
- No geometric bias — doesn't exploit maze structure
- Re-floods entire maze on every wall discovery

**Behaviour by maze type:**

| Maze Type | Flood Fill Behaviour |
|-----------|---------------------|
| Long corridors | Efficient — distances propagate cleanly along corridor |
| Dead-end heavy | May backtrack repeatedly before finding exits |
| Multiple paths | Always finds minimum-distance route through BFS |
| High complexity | Robust — performance degrades gracefully |

### Incremental A*

**Strengths:**
- Heuristic guidance reduces cells expanded vs Flood Fill
- Only replans affected portion of search on wall discovery
- Optimal paths in fully known environments (w=1.0)
- Supports weighted A* for speed/quality tradeoff
- More efficient on large open mazes

**Weaknesses:**
- Higher per-step computation overhead (heap operations)
- Heuristic quality degrades in mazes that require detours
- More complex to implement and debug
- Path validation adds overhead after each wall discovery

**Behaviour by maze type:**

| Maze Type | Incremental A* Behaviour |
|-----------|-------------------------|
| Long corridors | Excellent — heuristic points directly to goal |
| Dead-end heavy | More replanning events; can be slower than FF here |
| Multiple paths | Finds optimal path efficiently |
| High complexity | Replanning overhead grows; weighted A* helps |

### Computational Complexity Summary

| Algorithm | Time (per step) | Time (full run) | Space |
|-----------|-----------------|-----------------|-------|
| Flood Fill | O(W×H) re-flood | O(N×W×H) | O(W×H) |
| Incremental A* | O(k log k) | O(N×k log k) | O(W×H) |

Where:
- W, H = maze dimensions (16×16 → 256 cells)
- N = steps taken during exploration
- k = cells in the invalidated search region (<<256 typically)

---

## 📁 Project Structure

```
robotica_proposta_1/
│
├── algorithms/
│   ├── __init__.py
│   ├── flood_fill.py          # Flood Fill solver
│   └── incremental_astar.py   # Incremental A* solver
│
├── core/
│   ├── __init__.py
│   ├── maze.py                # MazeMap & Cell (bitmask walls, distances)
│   ├── robot.py               # RobotState (position, heading, history)
│   └── simulator_api.py       # mms stdin/stdout interface
│
├── evaluation/
│   ├── __init__.py
│   ├── benchmark.py           # BenchmarkRunner (load, analyse, report)
│   ├── metrics.py             # RunMetrics dataclass & MetricsCollector
│   └── plotting.py            # MazePlotter (bar charts, heatmaps, scatter)
│
├── mazes/                     # Custom .maz maze files
├── logs/                      # Auto-generated metric logs (JSON/CSV)
│   └── plots/                 # Generated plot images
│
├── tests/
│   ├── __init__.py
│   ├── test_maze.py           # MazeMap & Cell unit tests
│   ├── test_robot.py          # RobotState unit tests
│   ├── test_flood_fill.py     # FloodFill logic tests (mocked sim)
│   └── test_astar.py          # IncrementalAStar logic tests (mocked sim)
│
├── main.py                    # Simulator entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔮 Future Improvements

### Algorithmic
- [ ] **D* Lite**: Full incremental replanning with reverse search
- [ ] **Dijkstra + Turn Penalty**: Account for turn cost in path planning
- [ ] **Multi-goal planning**: Simultaneous exploration toward multiple targets
- [ ] **Fast-run optimisation**: Straight-line acceleration after maze is known
- [ ] **Diagonal movement**: Support for 45° moves (mms API supports this)

### Engineering
- [ ] **Maze generator**: Random perfect maze generation for automated testing
- [ ] **Multi-maze batch runner**: Automated benchmark across hundreds of mazes
- [ ] **Memory-efficient wall encoding**: Pack two cells per byte
- [ ] **Configuration file support**: YAML/TOML config instead of CLI flags
- [ ] **CI/CD pipeline**: Automated testing on push

### Analysis
- [ ] **Statistical significance testing**: Mann-Whitney U test for metric comparisons
- [ ] **Complexity class visualisation**: Plot cells-expanded vs maze complexity
- [ ] **Wall density analysis**: Correlation between wall density and algorithm performance

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [mackorone/mms](https://github.com/mackorone/mms) — Excellent open-source Micromouse simulator
- Micromouse Wikipedia — Background on the competition
- Classic literature on Flood Fill: P. Szymański et al. (2009)
- LPA* / D* Lite: Koenig & Likhachev (2002)



# Simulator Colour Legend

The simulator display updates in real time and reflects the algorithm's internal reasoning at each step.

**Common to both algorithms:**

| Phase | Colour | Meaning |
|-------|--------|---------|
| Start | 🟡 Yellow | Starting cell (0,0), labeled "S" |
| Start | 🟢 Green | Goal cells at the centre, labeled "G" |
| Pre-Phase 3 | 🔵 Cyan | Cells visited during Phases 1 & 2 |
| Pre-Phase 3 | ⬛ Black | Unexplored cells, labeled "?" |
| Phase 3 | 🟢 Bright Green | Optimal path with step numbers |
| Phase 3 | 🔵 Dark Cyan | Visited cells (background) |

**Flood Fill (Phases 1 & 2):**

The number displayed in each cell is the BFS distance value $d(x,y)$ — the estimated steps to goal under the current known map.

| Colour | Distance $d$ | Meaning |
|--------|-------------|---------|
| 🟢 Green | $d = 0$ | Goal cells |
| 🟡 Yellow | $1 \leq d \leq 4$ | Close to goal |
| 🔵 Cyan | $5 \leq d \leq 14$ | Medium distance |
| 🔵 Blue | $d \geq 15$ | Far from goal |
| ⬜ White | $d = \infty$ | Unreachable under current map |

**Incremental A* (Phases 1 & 2):**

The number displayed in each cell is the $f$-value $f = g + h$ from the A* search.

| Colour | Meaning |
|--------|---------|
| 🟢 Green | Goal cells |
| 🔵 Cyan | Cells physically visited by the robot |
| 🟡 Yellow | Cells in the search frontier (evaluated, not yet visited) |
| ⬛ Black | Cells with $f = \infty$ (not yet reached by search) |
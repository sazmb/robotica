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
6. [Batch / Auto-run Mode](#-batch--auto-run-mode)
7. [Running Benchmarks](#-running-benchmarks)
8. [Metrics Explained](#-metrics-explained)
9. [Experimental Analysis](#-experimental-analysis)
10. [Project Structure](#-project-structure)
11. [Future Improvements](#-future-improvements)

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
│   ┌──────────────────┐  ┌────────────────────── ┐   │
│   │  flood_fill.py   │  │ incremental_astar.py  │   │
│   │  BFS distance    │  │  A* + replanning      │   │
│   │  propagation     │  │  heapq priority queue │   │
│   └──────────────────┘  └────────────────────── ┘    │
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
| `--batch-dir` | — | *(none)* | Path to directory of `.txt` maze files for headless batch execution |

### Simulator Colour Legend

| Colour | Meaning |
|--------|----------|
| 🟩 Green | Goal cell / optimal path |
| 🟡 Yellow | Low distance / close to goal |
| 🔵 Blue | Higher distance value |
| ⬜ White | Unreachable / unknown |
| 🔵 Cyan | Visited cell (A* display) |

---

## 🤖 Batch / Auto-run Mode

The batch mode allows you to run the solver **automatically and sequentially** across every maze file in a directory — no mms GUI, no manual interaction, no key presses between runs.

### How It Works

Instead of communicating with the mms C++ simulator via stdin/stdout, batch mode uses a **pure-Python mock simulator** (`core/mock_simulator.py`) that:

1. **Parses** the ASCII `.txt` maze file into an in-memory truth wall grid.
2. **Replaces** all `simulator_api` functions (wall queries, movement, display) with mock equivalents.
3. **Runs** the existing 3-phase state machine (Exploration → Reverse → Speed Run) at near-instant CPU speed.

The existing FloodFill and IncrementalAStar solvers work **completely unchanged** — only the I/O layer underneath is swapped.

### Usage

```bash
# Run FloodFill on all maze files in mazes/
python main.py --algorithm flood_fill --batch-dir mazes

# Run A* on all maze files in mazes/
python main.py --algorithm astar --batch-dir mazes

# Run without saving results
python main.py --algorithm flood_fill --batch-dir mazes --no-save
```

### Output Files

```
logs/
├── live/
│   ├── floodfill_results.json       # mms GUI live-run results
│   └── incrementalastar_results.json
├── batch/
│   ├── floodfill_results.json       # headless batch-run results
│   └── incrementalastar_results.json
└── plots/                           # generated plot images
```

Batch results go to `logs/batch/` and live mms-GUI results go to `logs/live/`. They are never mixed, but `analyse_results.py` loads from both automatically.

### Maze Typology Parsing

Each run automatically extracts a **maze typology** from the filename. Filenames are expected to follow the pattern `[number]_[typology].txt`:

| Filename | Extracted Typology |
|---|---|
| `0_common_maze.txt` | `common_maze` |
| `3_dead_end_heavy.txt` | `dead_end_heavy` |
| `5_spiral.txt` | `spiral` |
| `my_maze.txt` | `example` *(fallback default)* |

The typology is stored in the `maze_typology` field of `RunMetrics` and included in all JSON/CSV output.

### Sample Batch Output

```
############################################################
  BATCH MODE — 8 maze(s)  |  Algorithm: flood_fill
############################################################

  ...runs each maze through all 3 phases...

############################################################
  BATCH COMPLETE — 8/8 mazes solved
############################################################
  0_common_maze             typology=common_maze          goal=YES  moves=  274  path= 58
  1_open_field              typology=open_field           goal=YES  moves=   49  path= 15
  2_long_corridor           typology=long_corridor        goal=YES  moves=  189  path= 63
  3_dead_end_heavy          typology=dead_end_heavy       goal=YES  moves=  129  path= 43
  ...
```

---

## 📊 Running Benchmarks

### Collecting Data

Run both algorithms multiple times in the simulator (press the **Reset** button between runs). Metrics are auto-saved to `logs/live/` after each run:

```
logs/
└── live/
    ├── floodfill_results.json
    └── incrementalastar_results.json
```

### Offline Analysis

Run the analysis script after collecting data. It automatically loads all JSON files from **both** `logs/live/` and `logs/batch/`, prints a comparison table, generates a Markdown report, and plots the data.

```bash
# Analyze all results (live + batch) in the logs/ directory
python analyse_results.py

# Specify a custom directory
python analyse_results.py --logs-dir my_custom_logs --output-dir my_reports
```

Sample output:
```
============================================================
 Micromouse Benchmark Analysis
============================================================

[Live runs]  logs/live
  Loaded    3 run(s) from: floodfill_results.json
  Loaded    2 run(s) from: incrementalastar_results.json

[Batch runs] logs/batch
  Loaded    8 run(s) from: floodfill_results.json
  Loaded    8 run(s) from: incrementalastar_results.json

  Total runs loaded: 21
```

> **Note on Batch vs. Live runs**: The `RunMetrics` JSON format is identical between both sources. The analysis script aggregates them all automatically. Batch mode gives you a larger, more statistically significant dataset collected without any manual effort.

### Output Files

After running the script, you will find:
1. `logs/benchmark_report.md` — A detailed Markdown summary
2. `logs/plots/` — High-resolution PNG plots (bar charts, heatmaps) comparing the algorithms.

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
| `maze_typology` | Typology parsed from maze filename (e.g. `spiral`) | string |

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
│   ├── mock_simulator.py      # Pure-Python mock simulator for batch mode
│   ├── robot.py               # RobotState (position, heading, history)
│   └── simulator_api.py       # mms stdin/stdout interface
│
├── evaluation/
│   ├── __init__.py
│   ├── benchmark.py           # BenchmarkRunner (load, analyse, report)
│   ├── metrics.py             # RunMetrics dataclass & MetricsCollector
│   └── plotting.py            # MazePlotter (bar charts, heatmaps, scatter)
│
├── mazes/                     # Maze files (.txt ASCII format)
├── logs/                      # Auto-generated metric logs
│   ├── live/                  # mms GUI live-run results
│   │   └── *_results.json
│   ├── batch/                 # Headless batch-run results
│   │   └── *_results.json
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
- [x] **Multi-maze batch runner**: Automated benchmark across all mazes (`--batch-dir`)
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

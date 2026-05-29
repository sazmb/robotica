"""
Visualization and Plotting Module
==================================
Generates publication-quality comparison plots and heatmaps from
benchmark results using matplotlib.

Plots generated:
  1. Comparison bar charts (moves, turns, visited cells, path length)
  2. Runtime comparison (elapsed seconds)
  3. Exploration ratio comparison
  4. Replan events comparison
  5. Exploration heatmaps (visit frequency per cell)
  6. Moves vs Path Length scatter plot

Author: Micromouse Research Project
Python: 3.11+
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend for file output
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[Plotting] WARNING: matplotlib not installed. Run: pip install matplotlib numpy")

from evaluation.metrics import RunMetrics, MetricsCollector


# ---------------------------------------------------------------------------
# Plot style configuration
# ---------------------------------------------------------------------------

ALGO_COLORS = {
    "FloodFill": "#4A90D9",
    "IncrementalAStar": "#E87040",
}

DEFAULT_STYLE = {
    "figure.facecolor": "#1A1A2E",
    "axes.facecolor": "#16213E",
    "axes.edgecolor": "#E0E0E0",
    "axes.labelcolor": "#E0E0E0",
    "text.color": "#E0E0E0",
    "xtick.color": "#E0E0E0",
    "ytick.color": "#E0E0E0",
    "grid.color": "#2A2A4A",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
}


def _apply_style() -> None:
    """Apply the dark theme to matplotlib."""
    if MATPLOTLIB_AVAILABLE:
        for k, v in DEFAULT_STYLE.items():
            plt.rcParams[k] = v
        plt.rcParams["font.family"] = "DejaVu Sans"


# ---------------------------------------------------------------------------
# Main plotting class
# ---------------------------------------------------------------------------

class MazePlotter:
    """
    Generates all visualisation plots for Micromouse benchmark results.

    Attributes:
        collector (MetricsCollector): Source of benchmark data.
        output_dir (Path): Directory where plots are saved.
        dpi (int): Resolution of output images (default 150).
    """

    def __init__(
        self,
        collector: MetricsCollector,
        output_dir: str | Path = "logs/plots",
        dpi: int = 150,
    ) -> None:
        """
        Initialise the plotter.

        Args:
            collector: MetricsCollector with benchmark data.
            output_dir: Where to save generated plots.
            dpi: Image resolution in dots per inch.
        """
        self.collector = collector
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
        _apply_style()

    # ------------------------------------------------------------------
    # Comparison bar charts
    # ------------------------------------------------------------------

    def plot_comparison_bars(
        self,
        metrics: Optional[list[str]] = None,
        filename: str = "comparison_bars.png",
    ) -> Path:
        """
        Generate side-by-side bar charts comparing algorithms on key metrics.

        Args:
            metrics: List of metric names to plot. Defaults to standard set.
            filename: Output file name.

        Returns:
            Path to saved plot.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("matplotlib is required for plotting.")

        if metrics is None:
            metrics = [
                "total_moves", "total_turns",
                "visited_cells", "final_path_length",
                "replan_count",
            ]

        algos = self.collector.algorithms()
        n_metrics = len(metrics)
        n_algos = len(algos)

        fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 6))
        fig.suptitle(
            "Algorithm Performance Comparison",
            fontsize=16, fontweight="bold", y=1.02,
        )

        if n_metrics == 1:
            axes = [axes]

        for ax, metric in zip(axes, metrics):
            means, stds, colors, labels = [], [], [], []
            for algo in algos:
                stats = self.collector.statistics(algo)
                if metric in stats:
                    means.append(stats[metric]["mean"])
                    stds.append(stats[metric]["stdev"])
                else:
                    means.append(0)
                    stds.append(0)
                colors.append(ALGO_COLORS.get(algo, "#AAAAAA"))
                labels.append(algo)

            x = np.arange(n_algos)
            bars = ax.bar(x, means, yerr=stds, capsize=5,
                          color=colors, alpha=0.85, edgecolor="white", linewidth=0.8)

            ax.set_title(metric.replace("_", " ").title(), fontsize=11, pad=10)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
            ax.set_ylabel("Value", fontsize=10)
            ax.grid(axis="y", alpha=0.4)
            ax.set_axisbelow(True)

            # Value labels on bars
            for bar, mean, std in zip(bars, means, stds):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + std + 0.5,
                    f"{mean:.1f}",
                    ha="center", va="bottom", fontsize=8, color="white"
                )

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Plotter] Saved: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Runtime comparison
    # ------------------------------------------------------------------

    def plot_runtime_comparison(
        self,
        filename: str = "runtime_comparison.png",
    ) -> Path:
        """
        Generate a box plot comparing algorithm runtime distributions.

        Args:
            filename: Output file name.

        Returns:
            Path to saved plot.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("matplotlib is required for plotting.")

        algos = self.collector.algorithms()
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.suptitle("Runtime Comparison (Wall-Clock)", fontsize=14, fontweight="bold")

        data = []
        labels = []
        colors = []
        for algo in algos:
            times = [
                r.elapsed_seconds for r in self.collector.runs_for(algo)
                if r.reached_goal
            ]
            data.append(times)
            labels.append(algo)
            colors.append(ALGO_COLORS.get(algo, "#AAAAAA"))

        bp = ax.boxplot(
            data, labels=labels, patch_artist=True,
            medianprops={"color": "white", "linewidth": 2},
        )
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)

        ax.set_ylabel("Elapsed Time (seconds)", fontsize=11)
        ax.grid(axis="y", alpha=0.4)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Plotter] Saved: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Exploration heatmap
    # ------------------------------------------------------------------

    def plot_exploration_heatmap(
        self,
        visit_counts: dict[tuple[int, int], int],
        maze_width: int = 16,
        maze_height: int = 16,
        title: str = "Exploration Heatmap",
        filename: str = "exploration_heatmap.png",
    ) -> Path:
        """
        Generate a heatmap showing visit frequency per maze cell.

        Args:
            visit_counts: Dict mapping (x, y) → visit count.
            maze_width: Maze columns.
            maze_height: Maze rows.
            title: Plot title.
            filename: Output file name.

        Returns:
            Path to saved plot.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("matplotlib is required for plotting.")

        grid = np.zeros((maze_height, maze_width), dtype=float)
        for (x, y), count in visit_counts.items():
            if 0 <= x < maze_width and 0 <= y < maze_height:
                grid[maze_height - 1 - y][x] = count  # flip y for display

        fig, ax = plt.subplots(figsize=(8, 8))
        fig.suptitle(title, fontsize=14, fontweight="bold")

        im = ax.imshow(grid, cmap="plasma", interpolation="nearest", aspect="equal")
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Visit Count", color="#E0E0E0")
        cbar.ax.yaxis.set_tick_params(color="#E0E0E0")
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#E0E0E0")

        ax.set_xlabel("X (column)", fontsize=10)
        ax.set_ylabel("Y (row, flipped)", fontsize=10)
        ax.set_xticks(range(maze_width))
        ax.set_yticks(range(maze_height))
        ax.set_xticklabels(range(maze_width), fontsize=7)
        ax.set_yticklabels(range(maze_height - 1, -1, -1), fontsize=7)
        ax.grid(False)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Plotter] Saved: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Moves vs Path Length scatter
    # ------------------------------------------------------------------

    def plot_efficiency_scatter(
        self,
        filename: str = "efficiency_scatter.png",
    ) -> Path:
        """
        Scatter plot of total moves vs. final path length for each run.

        Points closer to the diagonal y=x are more efficient (fewer
        wasted moves during exploration).

        Args:
            filename: Output file name.

        Returns:
            Path to saved plot.
        """
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("matplotlib is required for plotting.")

        fig, ax = plt.subplots(figsize=(8, 6))
        fig.suptitle(
            "Exploration Efficiency: Total Moves vs. Path Length",
            fontsize=13, fontweight="bold"
        )

        all_moves, all_paths = [], []
        legend_patches = []

        for algo in self.collector.algorithms():
            runs = [r for r in self.collector.runs_for(algo) if r.reached_goal]
            moves = [r.total_moves for r in runs]
            paths = [r.final_path_length for r in runs]
            color = ALGO_COLORS.get(algo, "#AAAAAA")
            ax.scatter(paths, moves, c=color, alpha=0.7, s=60,
                       edgecolors="white", linewidths=0.5, label=algo)
            all_moves.extend(moves)
            all_paths.extend(paths)
            legend_patches.append(
                mpatches.Patch(color=color, label=algo)
            )

        # Reference line y = x (perfect efficiency)
        if all_paths and all_moves:
            ref = range(0, max(max(all_paths), max(all_moves)) + 5)
            ax.plot(ref, ref, "--", color="#AAAAAA", alpha=0.5, label="y = x (ideal)")

        ax.set_xlabel("Final Path Length (cells)", fontsize=11)
        ax.set_ylabel("Total Moves During Exploration", fontsize=11)
        ax.legend(handles=legend_patches + [
            plt.Line2D([0], [0], linestyle="--", color="#AAAAAA", label="Ideal")
        ], fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        print(f"[Plotter] Saved: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Generate all plots
    # ------------------------------------------------------------------

    def generate_all(
        self,
        visit_counts_by_algo: Optional[
            dict[str, dict[tuple[int, int], int]]
        ] = None,
    ) -> list[Path]:
        """
        Generate all available plots in one call.

        Args:
            visit_counts_by_algo: Optional dict mapping algorithm name
                to visit count dict for heatmaps.

        Returns:
            List of paths to generated plot files.
        """
        paths: list[Path] = []
        paths.append(self.plot_comparison_bars())
        paths.append(self.plot_runtime_comparison())
        paths.append(self.plot_efficiency_scatter())

        if visit_counts_by_algo:
            for algo, counts in visit_counts_by_algo.items():
                safe_name = algo.lower().replace(" ", "_")
                paths.append(
                    self.plot_exploration_heatmap(
                        visit_counts=counts,
                        title=f"Exploration Heatmap — {algo}",
                        filename=f"heatmap_{safe_name}.png",
                    )
                )

        print(f"\n[Plotter] Generated {len(paths)} plots in {self.output_dir}")
        return paths


# ---------------------------------------------------------------------------
# Standalone convenience function
# ---------------------------------------------------------------------------

def plot_from_json(
    *json_paths: str | Path,
    output_dir: str | Path = "logs/plots",
) -> None:
    """
    Load JSON benchmark files and generate all plots.

    Example usage::

        plot_from_json(
            "logs/benchmark_20240101_120000.json",
            output_dir="logs/plots",
        )

    Args:
        *json_paths: One or more paths to JSON benchmark result files.
        output_dir: Directory for output plots.
    """
    collector = MetricsCollector()
    for p in json_paths:
        p = Path(p)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                m = RunMetrics(**{k: v for k, v in entry.items()
                                  if k in RunMetrics.__dataclass_fields__})
                collector.add(m)

    if len(collector) == 0:
        print("[Plotter] No data found in provided JSON files.")
        return

    plotter = MazePlotter(collector, output_dir=output_dir)
    plotter.generate_all()

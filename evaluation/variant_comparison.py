from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from evaluation.metrics import RunMetrics


ALGO_COLORS = {
    "FloodFill": "#4A90D9",
    "FloodFill+": "#7BB6F0",
    "IncrementalAStar": "#E87040",
    "IncrementalAStar+": "#F4A07A",
}


def load_runs(path):
    import json
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [RunMetrics.from_dict(d) for d in data]


def metric_mean(runs, metric):
    values = [
        getattr(r, metric)
        for r in runs
        if hasattr(r, metric) and getattr(r, metric) is not None
    ]
    return float(np.mean(values)) if values else np.nan


def plot_variant_comparison(
    floodfill_base,
    floodfill_penalized,
    astar_base,
    astar_penalized,
    output_dir="logs/variant_plots",
):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    datasets = {
        "FloodFill": load_runs(floodfill_base),
        "FloodFill+": load_runs(floodfill_penalized),
        "IncrementalAStar": load_runs(astar_base),
        "IncrementalAStar+": load_runs(astar_penalized),
    }

    metrics = {
        "total_moves": "Moves",
        "visited_cells": "Visited Cells",
        "elapsed_seconds": "Time (s)",
    }

    label_map = {
        "FloodFill": "Flood Fill",
        "FloodFill+": "Flood Fill+",
        "IncrementalAStar": "Incremental A*",
        "IncrementalAStar+": "Incremental A*+",
    }

    algos = list(datasets.keys())
    x = np.arange(len(metrics))
    width = 0.18

    fig, ax = plt.subplots(figsize=(11, 5))

    fig.suptitle(
        "Effect of Revisit Penalty — Absolute Values + Relative Change",
        fontsize=15,
        fontweight="bold"
    )

    # =========================
    # BAR PLOT (ASSOLUTO)
    # =========================
    for i, algo in enumerate(algos):
        values = [
            metric_mean(datasets[algo], m)
            for m in metrics.keys()
        ]

        bars = ax.bar(
            x + i * width,
            values,
            width=width,
            label=label_map[algo],
            color=ALGO_COLORS[algo],
            alpha=0.9
        )

        # =========================
        # ANNOTAZIONE Δ% (solo su penalizzati)
        # =========================
        if "+" in algo:
            base_algo = algo.replace("+", "")

            for j, metric in enumerate(metrics.keys()):

                base = metric_mean(datasets[base_algo], metric)
                pen = metric_mean(datasets[algo], metric)

                if base == 0 or np.isnan(base):
                    delta = 0
                else:
                    if metric == "visited_cells":
                        delta = 100 * (pen - base) / base
                    else:
                        delta = 100 * (base - pen) / base

                ax.text(
                    x[j] + i * width,
                    values[j],
                    f"{delta:+.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=0
                )

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([metrics[m] for m in metrics.keys()])

    ax.set_ylabel("Value")
    ax.grid(axis="y", alpha=0.25)

    ax.legend(framealpha=0.9)

    plt.tight_layout()

    plt.savefig(
        output_dir / "variant_combined.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"[OK] Saved combined plot in {output_dir}")
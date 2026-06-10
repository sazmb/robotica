from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from evaluation.metrics import RunMetrics
from matplotlib.lines import Line2D


ALGO_COLORS = {
    "FloodFill": "#4A90D9",
    "FloodFill+": "#7BB6F0",
    "IncrementalAStar": "#E87040",
    "IncrementalAStar+": "#F4A07A",
}

ALG_PALETTE = {
    'FloodFill': '#4A90D9',
    'IncrementalAStar': '#E87040',
}


def load_runs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return [RunMetrics.from_dict(d) for d in data]


def metric_mean(runs, metric):

    values = []

    for r in runs:
        if hasattr(r, metric):

            v = getattr(r, metric)

            if v is not None:
                values.append(v)

    if not values:
        return np.nan

    return float(np.mean(values))


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
        "total_moves": "Total Moves",
        "visited_cells": "Visited Cells",
        "elapsed_seconds": "Elapsed Time (s)",
        "replan_count": "Replan Count",
    }

    # =====================================================
    # FIGURA 1
    # =====================================================

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(12, 8)
    )

    axes = axes.flatten()

    fig.suptitle(
        "Effect of Revisit Penalty — Absolute Performance",
        fontsize=16,
        fontweight="bold"
    )

    for ax, (metric, title) in zip(axes, metrics.items()):

        label_map = {
            "FloodFill": "Flood Fill",
            "FloodFill+": "Flood Fill+",
            "IncrementalAStar": "Incremental A*",
            "IncrementalAStar+": "Incremental A*+",
        }

        labels = [label_map[k] for k in datasets.keys()]

        values = [
            metric_mean(runs, metric)
            for runs in datasets.values()
        ]

        bars = ax.bar(
            labels,
            values,
            color=[ALGO_COLORS[x] for x in datasets.keys()],
            alpha=0.9
        )

        ax.set_title(title, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        for b, v in zip(bars, values):

            if np.isnan(v):
                continue

            ax.annotate(
                f"{v:.1f}",
                xy=(
                    b.get_x() + b.get_width() / 2,
                    b.get_height()
                ),
                xytext=(0, 2),  # più vicino ma non attaccato
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="black"
            )

    plt.tight_layout()

    plt.savefig(
        output_dir / "variant_absolute_comparison.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    # =====================================================
    # FIGURA 2
    # =====================================================

    comparison_metrics = [
        "total_moves",
        "visited_cells",
        "elapsed_seconds",
    ]

    labels = [
        "Moves ↓",
        "Visited Cells ↑",
        "Elapsed Time ↓",
    ]

    ff_delta = []
    astar_delta = []

    for metric in comparison_metrics:

        ff_base = metric_mean(
            datasets["FloodFill"],
            metric
        )

        ff_pen = metric_mean(
            datasets["FloodFill+"],
            metric
        )

        ast_base = metric_mean(
            datasets["IncrementalAStar"],
            metric
        )

        ast_pen = metric_mean(
            datasets["IncrementalAStar+"],
            metric
        )

        if metric == "visited_cells":

            # più = meglio

            ff_change = (
                100 * (ff_pen - ff_base) / ff_base
            )

            ast_change = (
                100 * (ast_pen - ast_base) / ast_base
            )

        else:

            # meno = meglio

            ff_change = (
                100 * (ff_base - ff_pen) / ff_base
            )

            ast_change = (
                100 * (ast_base - ast_pen) / ast_base
            )

        ff_delta.append(ff_change)
        astar_delta.append(ast_change)

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    y = np.arange(len(labels))
    h = 0.35

    ax.barh(
        y - h/2,
        ff_delta,
        height=h,
        color="#4A90D9",
        label="FloodFill"
    )

    ax.barh(
        y + h/2,
        astar_delta,
        height=h,
        color="#E87040",
        label="IncrementalAStar"
    )

    ax.axvline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)

    ax.set_xlabel(
        "Penalty Effect (%)"
    )

    ax.set_title(
        "Effect of Revisit Penalty",
        fontsize=15,
        fontweight="bold"
    )

    ax.margins(x=0.20)

    legend_elements = [
        Line2D(
            [0], [0],
            marker='o',
            color='w',
            markerfacecolor=ALG_PALETTE['FloodFill'],
            markeredgecolor='None',
            markersize=9,
            label='Flood Fill'
        ),
        Line2D(
            [0], [0],
            marker='o',
            color='w',
            markerfacecolor=ALG_PALETTE['IncrementalAStar'],
            markeredgecolor='None',
            markersize=9,
            label='Incremental A*'
        )
    ]

    ax.legend(
        handles=legend_elements,
        framealpha=0.9,
        loc='upper left'
    )

    for vals, ypos in [
        (ff_delta, y - h/2),
        (astar_delta, y + h/2),
    ]:

        for v, yy in zip(vals, ypos):

            offset = 0.6 if v >= 0 else -0.6

            ax.text(
                v + offset,
                yy,
                f"{v:+.1f}%",
                va="center",
                ha="left" if v >= 0 else "right",
                fontsize=8
            )

    plt.tight_layout()

    plt.savefig(
        output_dir / "variant_effect_percent.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"[VariantComparison] Saved plots in {output_dir}"
    )
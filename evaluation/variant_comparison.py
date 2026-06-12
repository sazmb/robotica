from pathlib import Path
import json

import numpy as np
import matplotlib.pyplot as plt

from evaluation.metrics import RunMetrics


ALGO_COLORS = {
    "FloodFill": "#4A90D9",
    "FloodFill+": "#7BB6F0",
    "IncrementalAStar": "#E87040",
    "IncrementalAStar+": "#F4A07A",
}


def load_runs(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return [RunMetrics.from_dict(d) for d in data]


def phase_metric_mean(runs, phase_name, metric_name):
    values = []

    for r in runs:

        phase = getattr(r, phase_name, None)

        if phase is None:
            continue

        value = getattr(phase, metric_name, None)

        if value is not None:
            values.append(value)

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

    label_map = {
        "FloodFill": "Flood Fill",
        "FloodFill+": "Flood Fill+",
        "IncrementalAStar": "Incremental A*",
        "IncrementalAStar+": "Incremental A*+",
    }

    phase_metrics = {
        "Phase 1": ("phase1", "moves"),
        "Phase 2": ("phase2", "moves"),
        "Phase 3": ("phase3", "moves"),
    }

    phase_labels = list(phase_metrics.keys())
    algos = list(datasets.keys())

    x = np.arange(len(phase_labels))
    width = 0.18

    fig, ax = plt.subplots(
        figsize=(11, 5.5)
    )

    fig.suptitle(
        "Moves Across Phases",
        fontsize=15,
        fontweight="bold"
    )

    for i, algo in enumerate(algos):

        values = []

        for phase_label in phase_labels:

            phase_name, metric_name = phase_metrics[phase_label]

            values.append(
                phase_metric_mean(
                    datasets[algo],
                    phase_name,
                    metric_name
                )
            )

        bars = ax.bar(
            x + i * width,
            values,
            width=width,
            label=label_map[algo],
            color=ALGO_COLORS[algo],
            alpha=0.9
        )

        # valori assoluti sopra ogni barra
        for b, v in zip(bars, values):

            if np.isnan(v):
                continue

            ax.annotate(
                f"{v:.1f}",
                xy=(
                    b.get_x() + b.get_width() / 2,
                    b.get_height()
                ),
                xytext=(0, 2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8
            )

        # delta % per le versioni penalizzate
        if "+" in algo:

            base_algo = algo.replace("+", "")

            for j, phase_label in enumerate(phase_labels):

                phase_name, metric_name = phase_metrics[phase_label]

                base = phase_metric_mean(
                    datasets[base_algo],
                    phase_name,
                    metric_name
                )

                pen = phase_metric_mean(
                    datasets[algo],
                    phase_name,
                    metric_name
                )

                if (
                    np.isnan(base)
                    or np.isnan(pen)
                    or base == 0
                ):
                    continue

                delta = 100 * (pen - base) / base

                ax.annotate(
                    f"{delta:+.1f}%",
                    xy=(
                        x[j] + i * width,
                        pen
                    ),
                    xytext=(0, 16),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold"
                )

    ax.set_xticks(
        x + width * 1.5
    )

    ax.set_xticklabels(
        phase_labels
    )

    ax.set_ylabel(
        "Moves"
    )

    ax.set_xlabel(
        "Phase"
    )

    ax.grid(
        axis="y",
        alpha=0.25
    )

    ax.legend(
        framealpha=0.9
    )

    ax.margins(y=0.1)

    plt.tight_layout()

    plt.savefig(
        output_dir / "variant_moves.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"[OK] Saved plot in {output_dir}"
    )
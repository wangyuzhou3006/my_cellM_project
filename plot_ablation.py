import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


RESULTS_FILE = "ablation_summary.csv"
OUTPUT_FILE = "ablation_absolute.png"
GROUP_ORDER = [
    "baseline",
    "no_recommend",
    "weak_social",
    "no_heat_feedback",
    "no_heterogeneity",
    "no_dropout",
    "no_stage_gating",
    "slow_seed",
]
METRICS = [
    ("final_reached", "最终触达人数"),
    ("peak_heat", "热度峰值"),
    ("peak_sharing", "传播人数峰值"),
    ("peak_heat_step", "热度峰值出现步数"),
]
BASELINE_COLOR = "#1f4e79"
OTHER_COLOR = "#9fb7cf"
ERROR_BAR_COLOR = "#4a4a4a"


def load_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    numeric_fields = {
        key
        for key in rows[0].keys()
        if key not in {"group", "description"}
    }
    for row in rows:
        for key in numeric_fields:
            row[key] = float(row[key])
    order_index = {name: idx for idx, name in enumerate(GROUP_ORDER)}
    rows.sort(key=lambda row: order_index.get(row["group"], len(GROUP_ORDER)))
    return rows


def configure_fonts():
    plt.rcParams["font.sans-serif"] = [
        "PingFang SC",
        "Hiragino Sans GB",
        "Arial Unicode MS",
        "SimHei",
        "Noto Sans CJK SC",
        "sans-serif",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def plot_absolute_metrics(rows, output_path):
    configure_fonts()
    labels = [row["description"] for row in rows]
    colors = [
        BASELINE_COLOR if row["group"] == "baseline" else OTHER_COLOR
        for row in rows
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    for ax, (metric_key, title) in zip(axes, METRICS):
        mean_key = f"mean_{metric_key}"
        std_key = f"std_{metric_key}"
        values = [row[mean_key] for row in rows]
        std_values = [row[std_key] for row in rows]
        ax.bar(
            labels,
            values,
            yerr=std_values,
            capsize=4,
            color=colors,
            edgecolor="white",
            linewidth=0.8,
            ecolor=ERROR_BAR_COLOR,
        )
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", linestyle="--", alpha=0.25)

        if metric_key.endswith("_step"):
            text_values = [f"{value:.1f}" for value in values]
        elif metric_key == "peak_heat":
            text_values = [f"{value:.1f}" for value in values]
        else:
            text_values = [f"{value:.1f}" if any(std_values) else f"{int(value)}" for value in values]

        ymax = max((value + std) for value, std in zip(values, std_values)) if values else 0
        offset = ymax * 0.02 if ymax else 1
        for idx, (value, std_value, text_value) in enumerate(zip(values, std_values, text_values)):
            ax.text(idx, value + offset, text_value, ha="center", va="bottom", fontsize=9)
            if std_value > 0:
                ax.text(
                    idx,
                    value + offset * 3.2,
                    f"±{std_value:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=ERROR_BAR_COLOR,
                )

    legend_items = [
        Patch(facecolor=BASELINE_COLOR, label="基准组"),
        Patch(facecolor=OTHER_COLOR, label="消融组"),
        Patch(facecolor=ERROR_BAR_COLOR, label="标准差误差棒"),
    ]
    fig.suptitle("分组消融实验绝对值对比", fontsize=16, y=0.99)
    fig.legend(
        handles=legend_items,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.965),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    base_dir = Path(__file__).resolve().parent
    rows = load_rows(base_dir / RESULTS_FILE)
    plot_absolute_metrics(rows, base_dir / OUTPUT_FILE)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

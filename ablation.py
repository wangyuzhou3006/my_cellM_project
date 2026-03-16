import csv
from pathlib import Path
from statistics import mean, stdev
from types import SimpleNamespace

import config
from model import run_simulation


EXPERIMENT_GROUPS = [
    {
        "name": "baseline",
        "description": "当前配置",
        "overrides": {},
    },
    {
        "name": "no_recommend",
        "description": "关闭平台推荐链路",
        "overrides": {
            "P_RECOMMEND": 0.0,
            "HEAT_BOOST_RECOMMEND": 0.0,
        },
    },
    {
        "name": "weak_social",
        "description": "削弱社交传播影响",
        "overrides": {
            "P_EXPOSE": 0.03,
            "NEIGHBOR_VIEW_BOOST": 0.0,
            "NEIGHBOR_ENGAGE_BOOST": 0.0,
            "NEIGHBOR_SHARE_BOOST": 0.0,
        },
    },
    {
        "name": "no_heat_feedback",
        "description": "关闭热度对行为的反向影响",
        "overrides": {
            "HEAT_BOOST_EXPOSE": 0.0,
            "HEAT_BOOST_VIEW": 0.0,
            "HEAT_BOOST_ENGAGE": 0.0,
            "HEAT_BOOST_SHARE": 0.0,
            "HEAT_BOOST_RECOMMEND": 0.0,
        },
    },
    {
        "name": "no_heterogeneity",
        "description": "关闭用户个体差异",
        "overrides": {
            "ACTIVITY_STD": 0.0,
            "INTEREST_STD": 0.0,
            "INFLUENCE_STD": 0.0,
            "FATIGUE_THRESHOLD_MIN": 8,
            "FATIGUE_THRESHOLD_MAX": 8,
        },
    },
    {
        "name": "no_dropout",
        "description": "关闭中间阶段流失",
        "overrides": {
            "P_SKIP": 0.0,
            "P_DROP_VIEW": 0.0,
            "P_DROP_ENGAGE": 0.0,
            "INTEREST_DROP_WEIGHT": 0.0,
            "ACTIVITY_DROP_WEIGHT": 0.0,
        },
    },
    {
        "name": "no_stage_gating",
        "description": "关闭最短停留步数限制",
        "overrides": {
            "MIN_EXPOSED_STEPS": 1,
            "MIN_VIEWED_STEPS": 1,
            "MIN_ENGAGED_STEPS": 1,
        },
    },
    {
        "name": "slow_seed",
        "description": "降低初始传播源数量",
        "overrides": {
            "INITIAL_SHARERS": 1,
        },
    },
]

SEEDS = [config.RANDOM_SEED + offset for offset in range(5)]
CORE_METRICS = [
    "final_reached",
    "peak_heat",
    "peak_heat_step",
    "heat_center_step",
    "peak_sharing",
    "overall_view_conversion",
    "overall_engagement_conversion",
    "overall_share_conversion",
    "recommended_reach",
    "max_social_depth",
]
STEP_KEYS = {
    "peak_heat_step",
    "heat_center_step",
    "peak_sharing_step",
    "steps_to_half_reach",
    "steps_to_half_peak_heat",
}


def build_experiment_config(base_config, overrides, seed=None):
    values = {
        name: getattr(base_config, name)
        for name in dir(base_config)
        if name.isupper()
    }
    values.update(overrides)
    if seed is not None:
        values["RANDOM_SEED"] = seed
    return SimpleNamespace(**values)


def first_step_at_or_above(values, target):
    for idx, value in enumerate(values):
        if value >= target:
            return idx
    return len(values) - 1


def compute_heat_center_step(heat_history):
    total_heat = sum(heat_history)
    if total_heat <= 0:
        return 0.0
    weighted_sum = sum(step * heat for step, heat in enumerate(heat_history))
    return weighted_sum / total_heat


def summarize_history(history, exp_config):
    peak_heat = max(history["heat"])
    peak_heat_step = history["heat"].index(peak_heat)
    heat_center_step = compute_heat_center_step(history["heat"])
    peak_sharing = max(history["sharing"])
    peak_sharing_step = history["sharing"].index(peak_sharing)
    final_reached = history["cumulative_exposures"][-1]
    exposure_volume = final_reached - exp_config.INITIAL_SHARERS
    cumulative_views = history["cumulative_views"][-1]
    cumulative_engagements = history["cumulative_engagements"][-1]
    cumulative_shares = history["cumulative_shares"][-1]
    peak_exposed = max(history["exposed"])
    peak_viewed = max(history["viewed"])
    peak_engaged = max(history["engaged"])
    recommended_reach = history["current_recommended_reach"][-1]
    max_social_depth = max(history["max_social_depth"])
    overall_view_conversion = cumulative_views / max(exposure_volume, 1)
    overall_engagement_conversion = cumulative_engagements / max(cumulative_views, 1)
    overall_share_conversion = cumulative_shares / max(cumulative_engagements, 1)
    overall_skip_rate = sum(history["new_skips"]) / max(exposure_volume, 1)
    overall_view_drop_rate = sum(history["new_drop_view"]) / max(cumulative_views, 1)
    overall_engage_drop_rate = sum(history["new_drop_engage"]) / max(cumulative_engagements, 1)
    steps_to_half_reach = first_step_at_or_above(history["cumulative_exposures"], final_reached / 2.0)
    steps_to_half_peak_heat = first_step_at_or_above(history["heat"], peak_heat / 2.0)

    return {
        "final_reached": final_reached,
        "exposure_volume": exposure_volume,
        "cumulative_views": cumulative_views,
        "cumulative_engagements": cumulative_engagements,
        "cumulative_shares": cumulative_shares,
        "peak_heat": round(peak_heat, 4),
        "peak_heat_step": peak_heat_step,
        "heat_center_step": round(heat_center_step, 6),
        "peak_sharing": peak_sharing,
        "peak_sharing_step": peak_sharing_step,
        "peak_exposed": peak_exposed,
        "peak_viewed": peak_viewed,
        "peak_engaged": peak_engaged,
        "overall_view_conversion": round(overall_view_conversion, 6),
        "overall_engagement_conversion": round(overall_engagement_conversion, 6),
        "overall_share_conversion": round(overall_share_conversion, 6),
        "overall_skip_rate": round(overall_skip_rate, 6),
        "overall_view_drop_rate": round(overall_view_drop_rate, 6),
        "overall_engage_drop_rate": round(overall_engage_drop_rate, 6),
        "recommended_reach": recommended_reach,
        "max_social_depth": max_social_depth,
        "steps_to_half_reach": steps_to_half_reach,
        "steps_to_half_peak_heat": steps_to_half_peak_heat,
    }


def compare_with_baseline(rows):
    baseline = next(row for row in rows if row["group"] == "baseline")
    delta_rows = []

    for row in rows:
        delta_row = {
            "group": row["group"],
            "description": row["description"],
        }
        for key, value in row.items():
            if key in {"group", "description"}:
                continue
            baseline_value = baseline[key]
            if key in STEP_KEYS:
                delta_row[f"delta_{key}"] = value - baseline_value
            elif isinstance(value, (int, float)) and baseline_value != 0:
                delta_row[f"delta_{key}_pct"] = round((value - baseline_value) / baseline_value, 6)
            else:
                delta_row[f"delta_{key}"] = ""
        delta_rows.append(delta_row)

    return delta_rows


def run_single_experiment(group, seed):
    exp_config = build_experiment_config(config, group["overrides"], seed=seed)
    history, _ = run_simulation(exp_config)
    row = summarize_history(history, exp_config)
    row["group"] = group["name"]
    row["description"] = group["description"]
    row["seed"] = seed
    ordered_keys = ["group", "description", "seed"]
    return {key: row[key] for key in ordered_keys + [name for name in row if name not in ordered_keys]}


def aggregate_runs(run_rows):
    summary_rows = []
    grouped_rows = {}
    for row in run_rows:
        grouped_rows.setdefault(row["group"], []).append(row)

    for group in EXPERIMENT_GROUPS:
        rows = grouped_rows[group["name"]]
        summary_row = {
            "group": group["name"],
            "description": group["description"],
            "num_seeds": len(rows),
        }
        for metric in CORE_METRICS:
            values = [row[metric] for row in rows]
            summary_row[f"mean_{metric}"] = round(mean(values), 6)
            summary_row[f"std_{metric}"] = round(stdev(values), 6) if len(values) > 1 else 0.0
        summary_rows.append(summary_row)
    return summary_rows


def compare_summary_with_baseline(summary_rows):
    baseline = next(row for row in summary_rows if row["group"] == "baseline")
    delta_rows = []

    for row in summary_rows:
        delta_row = {
            "group": row["group"],
            "description": row["description"],
            "num_seeds": row["num_seeds"],
        }
        for metric in CORE_METRICS:
            metric_key = f"mean_{metric}"
            value = row[metric_key]
            baseline_value = baseline[metric_key]
            if metric in STEP_KEYS:
                delta_row[f"delta_{metric_key}"] = round(value - baseline_value, 6)
            elif baseline_value != 0:
                delta_row[f"delta_{metric_key}_pct"] = round((value - baseline_value) / baseline_value, 6)
            else:
                delta_row[f"delta_{metric_key}"] = ""
        delta_rows.append(delta_row)
    return delta_rows


def write_csv(path, rows):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_legacy_results(base_dir, rows, delta_rows):
    write_csv(base_dir / "ablation_results.csv", rows)
    write_csv(base_dir / "ablation_delta.csv", delta_rows)


def save_multi_seed_results(base_dir, run_rows, summary_rows, delta_rows):
    write_csv(base_dir / "ablation_runs.csv", run_rows)
    write_csv(base_dir / "ablation_summary.csv", summary_rows)
    write_csv(base_dir / "ablation_delta_summary.csv", delta_rows)


def run_single_seed_suite(seed):
    rows = []
    for group in EXPERIMENT_GROUPS:
        row = run_single_experiment(group, seed)
        row_without_seed = {
            key: value
            for key, value in row.items()
            if key != "seed"
        }
        rows.append(row_without_seed)
    delta_rows = compare_with_baseline(rows)
    return rows, delta_rows


def run_multi_seed_suite():
    run_rows = []
    for group in EXPERIMENT_GROUPS:
        for seed in SEEDS:
            run_rows.append(run_single_experiment(group, seed))
    summary_rows = aggregate_runs(run_rows)
    delta_rows = compare_summary_with_baseline(summary_rows)
    return run_rows, summary_rows, delta_rows


def main():
    base_dir = Path(__file__).resolve().parent

    single_seed_rows, single_seed_delta = run_single_seed_suite(config.RANDOM_SEED)
    save_legacy_results(base_dir, single_seed_rows, single_seed_delta)

    run_rows, summary_rows, delta_summary = run_multi_seed_suite()
    save_multi_seed_results(base_dir, run_rows, summary_rows, delta_summary)

    baseline_summary = next(row for row in summary_rows if row["group"] == "baseline")
    total_runs = len(run_rows)
    print("Ablation Summary")
    print(f"Experiments: {len(EXPERIMENT_GROUPS)}")
    print(f"Seeds per group: {len(SEEDS)}")
    print(f"Total runs: {total_runs}")
    print(
        "Baseline mean:"
        f" reached={baseline_summary['mean_final_reached']},"
        f" peak_heat={baseline_summary['mean_peak_heat']},"
        f" peak_sharing={baseline_summary['mean_peak_sharing']},"
        f" peak_heat_step={baseline_summary['mean_peak_heat_step']}"
    )
    print(
        "Saved:"
        " ablation_results.csv,"
        " ablation_delta.csv,"
        " ablation_runs.csv,"
        " ablation_summary.csv,"
        " ablation_delta_summary.csv"
    )


if __name__ == "__main__":
    main()

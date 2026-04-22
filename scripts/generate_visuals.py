"""
Generate publication-quality charts for capstone final report and presentation.

Reads scoring results from data/evaluation/results/ and produces charts
saved to docs/visuals/ in both PNG (300 dpi) and SVG formats.
"""

import json
import os
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import seaborn as sns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "evaluation" / "results"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "visuals"

SCORE_FILES = {
    "base": RESULTS_DIR / "scores_base.jsonl",
    "v1": RESULTS_DIR / "scores_v1.jsonl",
    "v2": RESULTS_DIR / "scores_v2.jsonl",
    "v2_rag": RESULTS_DIR / "scores_v2_rag.jsonl",
    "claude": RESULTS_DIR / "scores_claude.jsonl",
}

CONFIG_DISPLAY = {
    "base": "Base (Gemma 2)",
    "v1": "v1 (95 examples)",
    "v2": "v2 (363 examples)",
    "v2_rag": "v2 + RAG",
    "claude": "Claude (Reference)",
}

CONFIG_ORDER = ["base", "v1", "v2", "v2_rag", "claude"]

CRITERIA = [
    "empathy",
    "mi_technique_score",
    "resistance_handling",
    "autonomy_support",
    "appropriateness",
]

CRITERIA_DISPLAY = {
    "empathy": "Empathy",
    "mi_technique_score": "MI Technique",
    "resistance_handling": "Resistance\nHandling",
    "autonomy_support": "Autonomy\nSupport",
    "appropriateness": "Appropriateness",
}

TECHNIQUE_CATEGORIES = [
    "reflection",
    "open_question",
    "affirmation",
    "summary",
    "therapist_input",
    "other",
]

# ---------------------------------------------------------------------------
# Style setup
# ---------------------------------------------------------------------------
PALETTE = {
    "base": "#6C757D",      # grey
    "v1": "#0D6EFD",        # blue
    "v2": "#198754",        # green
    "v2_rag": "#FFC107",    # amber
    "claude": "#DC3545",    # red
}


def setup_style():
    """Set global matplotlib / seaborn style."""
    sns.set_theme(style="whitegrid", font_scale=1.15)
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
        "axes.titlesize": 16,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 11,
        "figure.titlesize": 18,
    })


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_scores():
    """Return dict[config] -> list[record]."""
    data = {}
    for config, path in SCORE_FILES.items():
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        data[config] = records
        print(f"  Loaded {len(records):>4d} records from {path.name}")
    return data


def compute_means(data):
    """Return dict[config][criterion] -> mean score."""
    means = {}
    for config in CONFIG_ORDER:
        records = data[config]
        means[config] = {}
        for c in CRITERIA:
            vals = [r["scores"][c] for r in records if c in r["scores"]]
            means[config][c] = np.mean(vals) if vals else 0.0
    return means


def compute_overall_means(means):
    """Return dict[config] -> overall mean across criteria."""
    return {
        config: np.mean([means[config][c] for c in CRITERIA])
        for config in CONFIG_ORDER
    }


def get_technique_counts(data):
    """Return dict[config] -> Counter of detected_technique values."""
    counts = {}
    for config in CONFIG_ORDER:
        counter = Counter()
        for r in data[config]:
            tech = r["scores"].get("detected_technique", "other")
            if tech not in TECHNIQUE_CATEGORIES:
                tech = "other"
            counter[tech] += 1
        counts[config] = counter
    return counts


# ---------------------------------------------------------------------------
# Saving helper
# ---------------------------------------------------------------------------
saved_files: list[str] = []


def save(fig, name):
    """Save figure as PNG and SVG, close it, and record paths."""
    for ext in ("png", "svg"):
        p = OUTPUT_DIR / f"{name}.{ext}"
        fig.savefig(p, bbox_inches="tight", dpi=300)
        saved_files.append(str(p))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 1 -- Overall Model Comparison Bar Chart
# ---------------------------------------------------------------------------
def chart_model_comparison(means):
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(CRITERIA))
    width = 0.15
    offsets = np.linspace(
        -width * (len(CONFIG_ORDER) - 1) / 2,
        width * (len(CONFIG_ORDER) - 1) / 2,
        len(CONFIG_ORDER),
    )

    for i, config in enumerate(CONFIG_ORDER):
        vals = [means[config][c] for c in CRITERIA]
        bars = ax.bar(
            x + offsets[i],
            vals,
            width,
            label=CONFIG_DISPLAY[config],
            color=PALETTE[config],
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_ylabel("Mean Score (1-5)")
    ax.set_title("Model Performance Comparison Across MI Evaluation Criteria")
    ax.set_xticks(x)
    ax.set_xticklabels([CRITERIA_DISPLAY[c] for c in CRITERIA])
    ax.set_ylim(0, 5.5)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    save(fig, "01_model_comparison")
    print("  [1/6] Model comparison bar chart")


# ---------------------------------------------------------------------------
# Chart 2 -- Radar / Spider Chart
# ---------------------------------------------------------------------------
def chart_radar(means):
    labels = [CRITERIA_DISPLAY[c].replace("\n", " ") for c in CRITERIA]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for config in CONFIG_ORDER:
        vals = [means[config][c] for c in CRITERIA]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", linewidth=2, label=CONFIG_DISPLAY[config],
                color=PALETTE[config], markersize=5)
        ax.fill(angles, vals, alpha=0.08, color=PALETTE[config])

    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=9, color="grey")
    ax.set_title("MI Skills Radar: All Configurations", y=1.08, fontsize=16)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), framealpha=0.9)

    save(fig, "02_radar_chart")
    print("  [2/6] Radar chart")


# ---------------------------------------------------------------------------
# Chart 3 -- Improvement Over Base
# ---------------------------------------------------------------------------
def chart_improvement(means):
    fig, ax = plt.subplots(figsize=(10, 6))

    compare_configs = ["v1", "v2", "v2_rag", "claude"]
    y_positions = np.arange(len(CRITERIA))
    bar_height = 0.18

    for i, config in enumerate(compare_configs):
        improvements = []
        for c in CRITERIA:
            base_val = means["base"][c]
            if base_val > 0:
                pct = ((means[config][c] - base_val) / base_val) * 100
            else:
                pct = 0.0
            improvements.append(pct)
        offset = (i - (len(compare_configs) - 1) / 2) * bar_height
        bars = ax.barh(
            y_positions + offset,
            improvements,
            bar_height,
            label=CONFIG_DISPLAY[config],
            color=PALETTE[config],
            edgecolor="white",
            linewidth=0.5,
        )
        # value labels
        for bar, val in zip(bars, improvements):
            x_pos = bar.get_width()
            ha = "left" if x_pos >= 0 else "right"
            ax.text(
                x_pos + (1 if x_pos >= 0 else -1),
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%",
                va="center",
                ha=ha,
                fontsize=8,
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels([CRITERIA_DISPLAY[c].replace("\n", " ") for c in CRITERIA])
    ax.set_xlabel("% Improvement Over Base")
    ax.set_title("Improvement Over Base Model by Criterion")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.legend(loc="lower right", framealpha=0.9)
    ax.grid(axis="x", alpha=0.3)

    save(fig, "03_improvement_over_base")
    print("  [3/6] Improvement over base chart")


# ---------------------------------------------------------------------------
# Chart 4 -- MI Technique Distribution (stacked bar)
# ---------------------------------------------------------------------------
def chart_technique_distribution(technique_counts):
    fig, ax = plt.subplots(figsize=(11, 6))

    tech_palette = {
        "reflection": "#4C72B0",
        "open_question": "#55A868",
        "affirmation": "#C44E52",
        "summary": "#8172B2",
        "therapist_input": "#CCB974",
        "other": "#999999",
    }

    tech_display = {
        "reflection": "Reflection",
        "open_question": "Open Question",
        "affirmation": "Affirmation",
        "summary": "Summary",
        "therapist_input": "Therapist Input",
        "other": "Other",
    }

    x = np.arange(len(CONFIG_ORDER))
    bottoms = np.zeros(len(CONFIG_ORDER))

    for tech in TECHNIQUE_CATEGORIES:
        vals = [technique_counts[config].get(tech, 0) for config in CONFIG_ORDER]
        ax.bar(
            x,
            vals,
            bottom=bottoms,
            label=tech_display[tech],
            color=tech_palette[tech],
            edgecolor="white",
            linewidth=0.5,
        )
        bottoms += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([CONFIG_DISPLAY[c] for c in CONFIG_ORDER], fontsize=10)
    ax.set_ylabel("Count")
    ax.set_title("MI Technique Distribution by Configuration")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    save(fig, "04_technique_distribution")
    print("  [4/6] Technique distribution chart")


# ---------------------------------------------------------------------------
# Chart 5 -- Overall Average Score Comparison
# ---------------------------------------------------------------------------
def chart_overall_average(overall_means):
    fig, ax = plt.subplots(figsize=(9, 5.5))

    x = np.arange(len(CONFIG_ORDER))
    vals = [overall_means[c] for c in CONFIG_ORDER]
    colors = [PALETTE[c] for c in CONFIG_ORDER]

    bars = ax.bar(x, vals, color=colors, edgecolor="white", linewidth=0.8, width=0.6)

    # value labels on bars
    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=13,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([CONFIG_DISPLAY[c] for c in CONFIG_ORDER], fontsize=10)
    ax.set_ylabel("Overall Mean Score (1-5)")
    ax.set_title("Overall Average Score by Configuration")
    ax.set_ylim(0, 5.5)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.grid(axis="y", alpha=0.3)

    # annotation arrow showing gap bridging
    base_val = overall_means["base"]
    claude_val = overall_means["claude"]
    rag_val = overall_means["v2_rag"]
    if rag_val > base_val and claude_val > base_val:
        gap_bridged = (rag_val - base_val) / (claude_val - base_val) * 100
        ax.annotate(
            f"v2+RAG bridges {gap_bridged:.0f}%\nof Base-to-Claude gap",
            xy=(3, rag_val),
            xytext=(3.6, rag_val + 0.6),
            fontsize=10,
            ha="center",
            arrowprops=dict(arrowstyle="->", color="#333"),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFFDE7", edgecolor="#FFC107"),
        )

    save(fig, "05_overall_average")
    print("  [5/6] Overall average chart")


# ---------------------------------------------------------------------------
# Chart 6 -- Heatmap
# ---------------------------------------------------------------------------
def chart_heatmap(means):
    fig, ax = plt.subplots(figsize=(9, 5))

    matrix = np.array([
        [means[config][c] for c in CRITERIA]
        for config in CONFIG_ORDER
    ])

    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        vmin=1,
        vmax=5,
        linewidths=0.8,
        linecolor="white",
        xticklabels=[CRITERIA_DISPLAY[c].replace("\n", " ") for c in CRITERIA],
        yticklabels=[CONFIG_DISPLAY[c] for c in CONFIG_ORDER],
        cbar_kws={"label": "Mean Score"},
        ax=ax,
    )

    ax.set_title("Score Heatmap: Configuration x Criterion")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    save(fig, "06_heatmap")
    print("  [6/6] Heatmap")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    setup_style()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading scoring data...")
    data = load_scores()

    print("\nComputing statistics...")
    means = compute_means(data)
    overall_means = compute_overall_means(means)
    technique_counts = get_technique_counts(data)

    # Print a quick summary table
    print("\n  Config                 | Overall Mean")
    print("  " + "-" * 42)
    for config in CONFIG_ORDER:
        print(f"  {CONFIG_DISPLAY[config]:<24s}| {overall_means[config]:.3f}")

    print("\nGenerating charts...")
    chart_model_comparison(means)
    chart_radar(means)
    chart_improvement(means)
    chart_technique_distribution(technique_counts)
    chart_overall_average(overall_means)
    chart_heatmap(means)

    print(f"\n{'=' * 50}")
    print(f"Generated {len(saved_files)} files in {OUTPUT_DIR}")
    print(f"{'=' * 50}")
    for f in saved_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()

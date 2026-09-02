#!/usr/bin/env python3
"""Combine validation results and draw a unified correlation summary."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


CORE_COLUMNS = ["analysis", "position", "method", "n", "coefficient", "p_value"]
ANALYSIS_LABELS = {
    "qwen_vs_human": "Qwen vs. human",
    "word2vec_vs_human": "Tencent embedding vs. human",
    "human_split_half": "Human split-half",
}


def combine(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        frame = pd.read_csv(path)
        missing = set(CORE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"{path} lacks columns: {sorted(missing)}")
        frames.append(frame[CORE_COLUMNS])
    result = pd.concat(frames, ignore_index=True)
    order = {name: index for index, name in enumerate(ANALYSIS_LABELS)}
    result["_analysis_order"] = result["analysis"].map(order)
    result["_position_order"] = result["position"].map({"C1": 0, "C2": 1})
    result["_method_order"] = result["method"].map({"Pearson": 0, "Spearman": 1})
    if result[["_analysis_order", "_position_order", "_method_order"]].isna().any().any():
        raise ValueError("unexpected analysis, position, or method label")
    return result.sort_values(
        ["_analysis_order", "_position_order", "_method_order"]
    ).drop(columns=["_analysis_order", "_position_order", "_method_order"])


def plot_summary(data: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True, constrained_layout=True)
    colors = {"C1": "#4c78a8", "C2": "#f58518"}
    for ax, method in zip(axes, ("Pearson", "Spearman")):
        subset = data[data["method"] == method].copy()
        pivot = subset.pivot(index="analysis", columns="position", values="coefficient")
        pivot = pivot.reindex(ANALYSIS_LABELS).rename(index=ANALYSIS_LABELS)
        pivot.plot.bar(ax=ax, color=[colors["C1"], colors["C2"]], rot=18, width=0.72)
        ax.set(xlabel="", ylabel="Correlation" if method == "Pearson" else "", title=method, ylim=(0, 0.9))
        ax.grid(axis="y", alpha=0.25)
        ax.legend(title="Position", frameon=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen", type=Path, required=True)
    parser.add_argument("--word2vec", type=Path, required=True)
    parser.add_argument("--split-half", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()
    result = combine([args.qwen, args.word2vec, args.split_half])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    plot_summary(result, args.figure)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

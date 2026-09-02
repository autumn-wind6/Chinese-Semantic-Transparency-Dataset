#!/usr/bin/env python3
"""Calculate Qwen-human convergent-validity correlations and scatter plots."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import pearsonr, spearmanr


PAIRS = (
    ("C1", "C1_ST_qwen", "C1.ST"),
    ("C2", "C2_ST_qwen", "C2.ST"),
)


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for position, machine_col, human_col in PAIRS:
        data = frame[[machine_col, human_col]].apply(pd.to_numeric, errors="coerce").dropna()
        pearson = pearsonr(data[machine_col], data[human_col])
        spearman = spearmanr(data[machine_col], data[human_col])
        rows.extend(
            [
                {"analysis": "qwen_vs_human", "position": position, "method": "Pearson", "n": len(data), "coefficient": pearson.statistic, "p_value": pearson.pvalue},
                {"analysis": "qwen_vs_human", "position": position, "method": "Spearman", "n": len(data), "coefficient": spearman.statistic, "p_value": spearman.pvalue},
            ]
        )
    return pd.DataFrame(rows)


def plot(frame: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    for ax, (position, machine_col, human_col) in zip(axes, PAIRS):
        data = frame[[machine_col, human_col]].apply(pd.to_numeric, errors="coerce").dropna()
        ax.hexbin(data[machine_col], data[human_col], gridsize=35, mincnt=1, cmap="Blues")
        ax.set(xlabel=f"Qwen {position} score", ylabel=f"Human {position} ST (z)", title=f"{position}: Qwen vs. human")
        ax.grid(alpha=0.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_excel(args.input) if args.input.suffix.lower() == ".xlsx" else pd.read_csv(args.input)
    result = analyze(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    plot(frame, args.figure)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()


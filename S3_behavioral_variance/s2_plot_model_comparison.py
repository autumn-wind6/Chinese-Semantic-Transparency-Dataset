#!/usr/bin/env python3
"""Plot adjusted R-squared gains for human and Qwen ST models."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = pd.read_csv(args.input)
    data = data[data["model"].isin(["human_st", "qwen_st"])].copy()
    pivot = data.pivot(index="outcome", columns="model", values="delta_adjusted_r2").loc[["zRT", "ERR"]]
    ax = pivot.rename(columns={"human_st": "Human ST", "qwen_st": "Qwen ST"}).plot.bar(
        figsize=(7.2, 4.5), color=["#999999", "#377eb8"], rot=0
    )
    ax.set(xlabel="Outcome", ylabel="Δ adjusted R²", title="Incremental behavioral validity")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    ax.figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ax.figure.savefig(args.output, dpi=220)
    plt.close(ax.figure)


if __name__ == "__main__":
    main()


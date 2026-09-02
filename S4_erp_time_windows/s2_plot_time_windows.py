#!/usr/bin/env python3
"""Plot archived Qwen ERP coefficients across the ten time windows."""

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
    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    x = range(1, len(data) + 1)
    for label, color in (("ST_C1_qwen", "#1f77b4"), ("ST_C2_qwen", "#d95f02")):
        coefficients = data[f"{label}_coef"]
        significant = data[f"{label}_p_fdr"] < 0.05
        ax.plot(x, coefficients, marker="o", color=color, label=label.replace("_qwen", " Qwen"))
        ax.scatter(data.index[significant] + 1, coefficients[significant], s=90, facecolors="none", edgecolors=color, linewidths=2)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(list(x), data["TW"])
    ax.set(xlabel="ERP time window", ylabel="LME coefficient", title="Qwen semantic transparency across ERP windows")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()


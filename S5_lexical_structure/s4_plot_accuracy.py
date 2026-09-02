#!/usr/bin/env python3
"""Plot accuracy for the 12-class lexical-structure benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


LABELS = {
    "偏正": "modifier-head",
    "联合": "coordinate",
    "主谓": "subject-predicate",
    "补充v": "verbal-complement",
    "补充n": "nominal-complement",
    "动宾": "verb-object",
    "前缀": "prefix",
    "后缀": "suffix",
    "音译外来词": "transliteration",
    "叠音": "reduplicative syllable",
    "重叠": "reduplication",
    "连绵词": "lianmian",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = pd.read_csv(args.input).query("structure != 'Overall'").sort_values("accuracy")
    data["display_label"] = data["structure"].map(LABELS)
    fig, ax = plt.subplots(figsize=(8, 5.5), constrained_layout=True)
    ax.barh(data["display_label"], data["accuracy"] * 100, color="#4c78a8")
    ax.axvline(89.064, color="#e45756", linestyle="--", label="Overall: 89.06%")
    ax.set(xlabel="Accuracy (%)", ylabel="Lexical structure", title="Qwen lexical-structure classification accuracy", xlim=(0, 100))
    ax.grid(axis="x", alpha=0.25)
    ax.legend(frameon=False, loc="lower right")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()

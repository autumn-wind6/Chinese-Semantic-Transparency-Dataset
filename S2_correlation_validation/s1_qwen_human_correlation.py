#!/usr/bin/env python3
"""Calculate Qwen-human convergent-validity correlations."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "final" / "Qwen_ST.xlsx"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "qwen_human_correlation.csv"

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    frame = pd.read_excel(args.input) if args.input.suffix.lower() == ".xlsx" else pd.read_csv(args.input)
    result = analyze(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

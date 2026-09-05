#!/usr/bin/env python3
"""Validate human-rating means and calculate deterministic split-half correlations."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "input" / "human_rating_validation.xlsx"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "human_split_half_correlation.csv"

def parse_ratings(value: object) -> list[float]:
    if pd.isna(value):
        return []
    text = str(value).strip().replace("－", "-").replace("—", "-").replace("–", "-").replace("~", "-")
    text = re.sub(r"[^0-9.\-]", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    values = []
    for part in text.split("-") if text else []:
        try:
            values.append(float(part))
        except ValueError:
            continue
    return values


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for position in ("C1", "C2"):
        rating_col, mean_col = f"{position}RATINGS", f"{position}CST"
        parsed = frame[rating_col].map(parse_ratings)
        means = parsed.map(lambda x: np.mean(x) if x else np.nan)
        reported = pd.to_numeric(frame[mean_col], errors="coerce")
        comparable = means.notna() & reported.notna()
        matched = np.isclose(means[comparable], reported[comparable], atol=1e-8)
        halves = parsed.map(lambda x: (x[: len(x) // 2], x[len(x) // 2 :]))
        split = pd.DataFrame(
            {
                "first": halves.map(lambda x: np.mean(x[0]) if x[0] else np.nan),
                "second": halves.map(lambda x: np.mean(x[1]) if x[1] else np.nan),
            }
        ).dropna()
        pearson = pearsonr(split["first"], split["second"])
        spearman = spearmanr(split["first"], split["second"])
        rows.extend(
            [
                {"analysis": "human_split_half", "position": position, "method": "Pearson", "n": len(split), "coefficient": pearson.statistic, "p_value": pearson.pvalue, "reported_mean_matches": int(matched.sum()), "reported_mean_mismatches": int((~matched).sum())},
                {"analysis": "human_split_half", "position": position, "method": "Spearman", "n": len(split), "coefficient": spearman.statistic, "p_value": spearman.pvalue, "reported_mean_matches": int(matched.sum()), "reported_mean_mismatches": int((~matched).sum())},
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

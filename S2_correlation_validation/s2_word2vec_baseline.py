#!/usr/bin/env python3
"""Evaluate Tencent Chinese embeddings as a static semantic baseline.

The large embedding binary is an external dependency and is not distributed.
Only cosine similarities are retained; raw 200-dimensional vectors are not
written into release workbooks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator > 0 else float("nan")


def analyze_existing(frame: pd.DataFrame) -> pd.DataFrame:
    pairs = (("C1", "cos_C1_Word", "C1.ST"), ("C2", "cos_C2_Word", "C2.ST"))
    # Match the published analysis: both positions share one complete-case set.
    common = frame[["cos_C1_Word", "cos_C2_Word", "C1.ST", "C2.ST"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()
    rows = []
    for position, cosine_col, human_col in pairs:
        data = common[[cosine_col, human_col]]
        pearson = pearsonr(data[cosine_col], data[human_col])
        spearman = spearmanr(data[cosine_col], data[human_col])
        rows.extend(
            [
                {"analysis": "word2vec_vs_human", "position": position, "method": "Pearson", "n": len(data), "coefficient": pearson.statistic, "p_value": pearson.pvalue},
                {"analysis": "word2vec_vs_human", "position": position, "method": "Spearman", "n": len(data), "coefficient": spearman.statistic, "p_value": spearman.pvalue},
            ]
        )
    return pd.DataFrame(rows)


def add_cosines(frame: pd.DataFrame, binary: Path) -> pd.DataFrame:
    from gensim.models import KeyedVectors  # lazy: large optional dependency

    model = KeyedVectors.load_word2vec_format(str(binary), binary=True)
    out = frame.copy()
    for position, char_col in (("C1", "C1"), ("C2", "C2")):
        values = []
        for word, char in zip(out["Word"].astype(str), out[char_col].astype(str)):
            values.append(cosine(model[word], model[char]) if word in model and char in model else float("nan"))
        out[f"cos_{position}_Word"] = values
    return out


def draw(frame: pd.DataFrame, output: Path) -> None:
    common = frame[["cos_C1_Word", "cos_C2_Word", "C1.ST", "C2.ST"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    for ax, (position, x, y) in zip(axes, (("C1", "cos_C1_Word", "C1.ST"), ("C2", "cos_C2_Word", "C2.ST"))):
        data = common[[x, y]]
        ax.hexbin(data[x], data[y], gridsize=35, mincnt=1, cmap="Greens")
        ax.set(xlabel=f"{position}-word cosine", ylabel=f"Human {position} ST (z)", title=f"{position}: static embedding baseline")
        ax.grid(alpha=0.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--embedding-binary", type=Path)
    parser.add_argument("--augmented-output", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_excel(args.input) if args.input.suffix.lower() == ".xlsx" else pd.read_csv(args.input)
    if not {"cos_C1_Word", "cos_C2_Word"}.issubset(frame.columns):
        if not args.embedding_binary:
            raise SystemExit("input has no cosine columns; provide --embedding-binary")
        frame = add_cosines(frame, args.embedding_binary)
        if args.augmented_output:
            args.augmented_output.parent.mkdir(parents=True, exist_ok=True)
            frame.drop(columns=[c for c in frame if c.startswith("vec_")], errors="ignore").to_csv(args.augmented_output, index=False)
    result = analyze_existing(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    draw(frame, args.figure)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

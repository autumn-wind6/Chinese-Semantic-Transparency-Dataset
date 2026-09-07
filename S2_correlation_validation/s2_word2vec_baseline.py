#!/usr/bin/env python3
"""Correlate Tencent Word2Vec morpheme-word cosine similarity with human ST.

The Tencent embedding binary is an external model dependency and is not stored
in this repository. Pass its path with ``--embedding-binary`` or set
``TENCENT_W2V_BIN`` in ``.env``. No figures or raw embedding vectors are saved.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "final" / "Qwen_ST.xlsx"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "word2vec_human_correlation.xlsx"


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries without printing or overwriting secrets."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key.isidentifier():
            os.environ.setdefault(key, value.strip("\"'"))


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_excel(path) if path.suffix.lower() == ".xlsx" else pd.read_csv(path)


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".xlsx":
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False, encoding="utf-8-sig")


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator > 0 else float("nan")


def add_cosines(frame: pd.DataFrame, binary: Path) -> pd.DataFrame:
    """Add cosine and vocabulary-coverage columns without retaining raw vectors."""
    required = {"Word", "C1", "C2"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"input lacks columns: {', '.join(missing)}")
    if not binary.is_file():
        raise FileNotFoundError(f"embedding binary not found: {binary}")

    from gensim.models import KeyedVectors

    print(f"loading embeddings: {binary}")
    model = KeyedVectors.load_word2vec_format(str(binary), binary=True)
    out = frame.copy()
    cosine_c1: list[float] = []
    cosine_c2: list[float] = []
    in_vocab_word: list[bool] = []
    in_vocab_c1: list[bool] = []
    in_vocab_c2: list[bool] = []

    for word, c1, c2 in zip(out["Word"], out["C1"], out["C2"]):
        word, c1, c2 = str(word).strip(), str(c1).strip(), str(c2).strip()
        has_word, has_c1, has_c2 = word in model, c1 in model, c2 in model
        in_vocab_word.append(has_word)
        in_vocab_c1.append(has_c1)
        in_vocab_c2.append(has_c2)
        cosine_c1.append(cosine(model[c1], model[word]) if has_word and has_c1 else float("nan"))
        cosine_c2.append(cosine(model[c2], model[word]) if has_word and has_c2 else float("nan"))

    out["cos_C1_Word"] = cosine_c1
    out["cos_C2_Word"] = cosine_c2
    out["in_vocab_Word"] = in_vocab_word
    out["in_vocab_C1"] = in_vocab_c1
    out["in_vocab_C2"] = in_vocab_c2
    print(
        "out-of-vocabulary rows — "
        f"Word: {sum(not value for value in in_vocab_word)}, "
        f"C1: {sum(not value for value in in_vocab_c1)}, "
        f"C2: {sum(not value for value in in_vocab_c2)}"
    )
    return out


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    """Use one shared complete-case sample for the C1 and C2 correlations."""
    required = ["cos_C1_Word", "cos_C2_Word", "C1.ST", "C2.ST"]
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"input lacks columns: {', '.join(missing)}")
    common = frame[required].apply(pd.to_numeric, errors="coerce").dropna()
    if len(common) < 2:
        raise ValueError("fewer than two complete Word2Vec/human-rating rows")

    rows: list[dict[str, object]] = []
    for position, cosine_column, human_column in (
        ("C1", "cos_C1_Word", "C1.ST"),
        ("C2", "cos_C2_Word", "C2.ST"),
    ):
        pearson = pearsonr(common[cosine_column], common[human_column])
        spearman = spearmanr(common[cosine_column], common[human_column])
        rows.extend(
            [
                {
                    "analysis": "word2vec_vs_human",
                    "position": position,
                    "method": "Pearson",
                    "n": len(common),
                    "coefficient": pearson.statistic,
                    "p_value": pearson.pvalue,
                },
                {
                    "analysis": "word2vec_vs_human",
                    "position": position,
                    "method": "Spearman",
                    "n": len(common),
                    "coefficient": spearman.statistic,
                    "p_value": spearman.pvalue,
                },
            ]
        )
    return pd.DataFrame(rows)


def main() -> None:
    load_env_file(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--embedding-binary",
        type=Path,
        default=Path(os.environ["TENCENT_W2V_BIN"]) if os.getenv("TENCENT_W2V_BIN") else None,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--augmented-output",
        type=Path,
        help="optional CSV/XLSX containing cosine and vocabulary-coverage columns",
    )
    parser.add_argument(
        "--reuse-cosines",
        action="store_true",
        help="use existing cos_C1_Word/cos_C2_Word columns instead of loading embeddings",
    )
    args = parser.parse_args()

    frame = read_table(args.input)
    has_cosines = {"cos_C1_Word", "cos_C2_Word"}.issubset(frame.columns)
    if args.reuse_cosines:
        if not has_cosines:
            raise SystemExit("--reuse-cosines requires cos_C1_Word and cos_C2_Word in the input")
    else:
        if args.embedding_binary is None:
            raise SystemExit("provide --embedding-binary or set TENCENT_W2V_BIN in .env")
        frame = add_cosines(frame, args.embedding_binary)

    if args.augmented_output:
        write_table(frame, args.augmented_output)
    result = analyze(frame)
    write_table(result, args.output)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

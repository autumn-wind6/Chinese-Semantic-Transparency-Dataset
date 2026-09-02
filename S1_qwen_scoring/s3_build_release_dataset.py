#!/usr/bin/env python3
"""Normalize the existing scored workbook into the stable public schema."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


PRODUCTION_STRUCTURES = {
    "联合", "偏正", "补充", "动宾", "主谓", "叠音", "重叠", "连绵词", "音译外来词", "前缀", "后缀"
}
DIST_ITEM = re.compile(r"([1-7])\s*:\s*([0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)")


def probability_json(value: object) -> str:
    if pd.isna(value) or not str(value).strip():
        return ""
    pairs = DIST_ITEM.findall(str(value))
    if not pairs:
        raise ValueError(f"unparseable probability distribution: {value!r}")
    distribution = {rating: float(prob) for rating, prob in pairs}
    return json.dumps(distribution, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_release_frame(source: pd.DataFrame, expected_rows: int = 72820) -> pd.DataFrame:
    required = [
        "word", "subtlex", "yuwei", "weiruan", "xianhan",
        "prob_dist_C1", "C1_ST", "prob_dist_C2", "C2_ST", "词汇结构",
    ]
    missing = [column for column in required if column not in source]
    if missing:
        raise ValueError(f"source workbook is missing columns: {missing}")
    if len(source) != expected_rows:
        raise ValueError(f"expected {expected_rows:,} rows, found {len(source):,}")

    word = source["word"].fillna("").astype(str).str.strip()
    if word.duplicated().any() or not word.str.fullmatch(r"[\u4e00-\u9fff]{2}").all():
        raise ValueError("word column must contain unique two-character CJK words")
    c1_score = pd.to_numeric(source["C1_ST"], errors="coerce")
    c2_score = pd.to_numeric(source["C2_ST"], errors="coerce")
    score_ok = c1_score.between(1, 7) & c2_score.between(1, 7)
    structure_ok = source["词汇结构"].isin(PRODUCTION_STRUCTURES)

    release = pd.DataFrame(
        {
            "word": word,
            "c1": word.str[0],
            "c2": word.str[1],
            "source_subtlex": source["subtlex"].fillna(0).astype(int),
            "source_yuwei": source["yuwei"].fillna(0).astype(int),
            "source_microsoft": source["weiruan"].fillna(0).astype(int),
            "source_xianhan": source["xianhan"].fillna(0).astype(int),
            "qwen_c1_probability_distribution": source["prob_dist_C1"].map(probability_json),
            "qwen_c1_score": c1_score,
            "qwen_c2_probability_distribution": source["prob_dist_C2"].map(probability_json),
            "qwen_c2_score": c2_score,
            "lexical_structure": source["词汇结构"].where(structure_ok, ""),
            "st_qc_status": score_ok.map({True: "valid", False: "missing_score"}),
            "structure_qc_status": structure_ok.map({True: "valid", False: "api_error"}),
        }
    )
    return release


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    parser.add_argument("--xlsx-output", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=72820)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = pd.read_excel(args.input)
    release = build_release_frame(source, args.expected_rows)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    args.xlsx_output.parent.mkdir(parents=True, exist_ok=True)
    release.to_csv(args.csv_output, index=False, encoding="utf-8-sig")
    release.to_excel(args.xlsx_output, index=False)
    print(f"wrote {len(release):,} rows")
    print(release[["st_qc_status", "structure_qc_status"]].value_counts().to_string())


if __name__ == "__main__":
    main()


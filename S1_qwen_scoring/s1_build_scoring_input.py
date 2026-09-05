#!/usr/bin/env python3
"""Build the scoring input from SUBTLEX, yuwei, and xianhan."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DIR = REPO_ROOT / "data" / "external"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "input" / "st_scoring_source_matrix.xlsx"
BIGRAM_RE = re.compile(r"^[\u4e00-\u9fff]{2}$")
HEADWORD_RE = re.compile(r"【([^】]+)】")


def is_chinese_bigram(value: object) -> bool:
    return bool(BIGRAM_RE.fullmatch(str(value).strip()))


def load_subtlex(path: Path) -> dict[str, int]:
    """Return two-character SUBTLEX words and their raw WCount frequency."""
    table = pd.read_excel(path, header=2, usecols=["Word", "WCount"])
    table["Word"] = table["Word"].astype(str).str.strip()
    table["WCount"] = pd.to_numeric(table["WCount"], errors="coerce")
    table = table[table["Word"].map(is_chinese_bigram) & table["WCount"].notna()]
    if table["Word"].duplicated().any():
        duplicates = table.loc[table["Word"].duplicated(), "Word"].tolist()
        raise ValueError(f"duplicate SUBTLEX words: {duplicates[:5]}")
    return dict(zip(table["Word"], table["WCount"].astype(int)))


def load_yuwei(path: Path) -> set[str]:
    words: set[str] = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            word = line.rstrip("\r\n").split("\t", 1)[0].strip()
            if is_chinese_bigram(word):
                words.add(word)
    return words


def read_xianhan(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if shutil.which("textutil"):
        process = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return process.stdout
    if shutil.which("antiword"):
        process = subprocess.run(
            ["antiword", str(path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return process.stdout
    raise RuntimeError("reading xianhan.doc requires macOS textutil or antiword; alternatively pass a UTF-8 .txt export")


def load_xianhan(path: Path) -> set[str]:
    text = read_xianhan(path)
    return {
        match.group(1).strip()
        for match in HEADWORD_RE.finditer(text)
        if is_chinese_bigram(match.group(1).strip())
    }


def build_matrix(sources: dict[str, set[str]], subtlex_frequencies: dict[str, int]) -> pd.DataFrame:
    words = sorted(set().union(*sources.values()))
    return pd.DataFrame(
        {
            "word": words,
            "subtlex": [int(word in sources["subtlex"]) for word in words],
            "subtlex_wcount": pd.array(
                [subtlex_frequencies.get(word) for word in words], dtype="Int64"
            ),
            "yuwei": [int(word in sources["yuwei"]) for word in words],
            "xianhan": [int(word in sources["xianhan"]) for word in words],
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subtlex", type=Path, default=EXTERNAL_DIR / "SUBTLEX-CH-WF.xlsx")
    parser.add_argument("--xianhan", type=Path, default=EXTERNAL_DIR / "xianhan.doc")
    parser.add_argument("--yuwei", type=Path, default=EXTERNAL_DIR / "yuwei.txt")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    subtlex_frequencies = load_subtlex(args.subtlex)
    sources = {
        "subtlex": set(subtlex_frequencies),
        "yuwei": load_yuwei(args.yuwei),
        "xianhan": load_xianhan(args.xianhan),
    }
    matrix = build_matrix(sources, subtlex_frequencies)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_excel(args.output, index=False)
    print(f"wrote {len(matrix):,} words to {args.output}")
    for name, words in sources.items():
        print(f"{name}: {len(words):,}")


if __name__ == "__main__":
    main()

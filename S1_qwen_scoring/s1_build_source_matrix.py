#!/usr/bin/env python3
"""Build a de-duplicated two-character word source matrix.

Third-party source files are intentionally not distributed. Pass their paths on
the command line after obtaining them from their original providers.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BIGRAM_RE = re.compile(r"^[\u4e00-\u9fff]{2}$")
HEADWORD_RE = re.compile(r"【([^】]+)】")


def is_chinese_bigram(value: object) -> bool:
    return bool(BIGRAM_RE.fullmatch(str(value).strip()))


def load_subtlex(path: Path) -> set[str]:
    frame = pd.read_excel(path, header=None, usecols=[0])
    return {str(v).strip() for v in frame.iloc[:, 0].dropna() if is_chinese_bigram(v)}


def load_yuwei(path: Path) -> set[str]:
    words: set[str] = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            word = line.rstrip("\r\n").split("\t", 1)[0].strip()
            if is_chinese_bigram(word):
                words.add(word)
    return words


def load_microsoft(path: Path) -> set[str]:
    words: set[str] = set()
    with path.open(encoding="gb18030", errors="replace") as handle:
        for line in handle:
            text = line.rstrip("\r\n")
            if text.endswith("::"):
                word = text[:-2].strip()
                if is_chinese_bigram(word):
                    words.add(word)
    return words


def load_xianhan_text(path: Path) -> set[str]:
    """Read text exported from the source .doc file.

    Convert the legacy Word document to UTF-8 text outside this script. This
    keeps the canonical pipeline cross-platform and avoids Word COM automation.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    return {m.group(1).strip() for m in HEADWORD_RE.finditer(text) if is_chinese_bigram(m.group(1))}


def build_matrix(sources: dict[str, set[str]]) -> pd.DataFrame:
    all_words = sorted(set().union(*sources.values()))
    rows = []
    for word in all_words:
        row: dict[str, object] = {"word": word}
        row.update({f"source_{name}": int(word in words) for name, words in sources.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subtlex", type=Path, required=True)
    parser.add_argument("--yuwei", type=Path, required=True)
    parser.add_argument("--microsoft", type=Path, required=True)
    parser.add_argument("--xianhan-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = {
        "subtlex": load_subtlex(args.subtlex),
        "yuwei": load_yuwei(args.yuwei),
        "microsoft": load_microsoft(args.microsoft),
        "xianhan": load_xianhan_text(args.xianhan_text),
    }
    frame = build_matrix(sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"wrote {len(frame):,} unique words to {args.output}")
    for name, words in sources.items():
        print(f"{name}: {len(words):,}")


if __name__ == "__main__":
    main()


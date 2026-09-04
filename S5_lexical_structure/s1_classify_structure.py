#!/usr/bin/env python3
"""Classify lexical structure with an OpenAI-compatible Qwen endpoint."""

from __future__ import annotations

import argparse
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd


STRUCTURES = ("联合", "偏正", "补充", "动宾", "主谓", "叠音", "重叠", "连绵词", "音译外来词", "前缀", "后缀")
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "lexical_structure_11class_system.txt").read_text(encoding="utf-8")


def parse_structure(text: str) -> str:
    cleaned = re.sub(r"[`\s]+", "", text or "")
    exact = [label for label in STRUCTURES if label in cleaned]
    if len(exact) != 1:
        raise ValueError(f"expected exactly one structure label, got {text!r}")
    return exact[0]


def classify_one(client: Any, word: str, model: str, retries: int) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"词语是：{word}。请直接回复一个结构类型。"},
                ],
                temperature=0.3,
                stream=False,
                extra_body={"enable_thinking": False},
            )
            return parse_structure(response.choices[0].message.content)
        except ValueError:
            raise
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}")


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_excel(path) if path.suffix.lower() == ".xlsx" else pd.read_csv(path)


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".xlsx":
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--word-column", default="word")
    parser.add_argument("--model", default=os.getenv("QWEN_STRUCTURE_MODEL", "qwen3.5-397b-a17b"))
    parser.add_argument("--base-url", default=os.getenv("QWEN_STRUCTURE_BASE_URL", ""))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("QWEN_STRUCTURE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key or not args.base_url:
        raise SystemExit("set QWEN_STRUCTURE_API_KEY (or QWEN_API_KEY) and QWEN_STRUCTURE_BASE_URL")
    from openai import OpenAI

    frame = read_table(args.output if args.resume and args.output.exists() else args.input)
    if args.word_column not in frame:
        raise SystemExit(f"missing word column: {args.word_column}")
    for column in ("lexical_structure", "structure_qc_status"):
        if column not in frame:
            frame[column] = ""
    client = OpenAI(api_key=api_key, base_url=args.base_url, timeout=60)
    jobs = [
        (idx, str(row[args.word_column]).strip())
        for idx, row in frame.iterrows()
        if row["structure_qc_status"] != "valid"
    ]
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        future_map = {pool.submit(classify_one, client, word, args.model, args.retries): (idx, word) for idx, word in jobs}
        for future in as_completed(future_map):
            idx, word = future_map[future]
            try:
                frame.at[idx, "lexical_structure"] = future.result()
                frame.at[idx, "structure_qc_status"] = "valid"
            except ValueError:
                frame.at[idx, "structure_qc_status"] = "invalid_response"
            except Exception:
                frame.at[idx, "structure_qc_status"] = "api_error"
            completed += 1
            if completed % max(1, args.checkpoint_every) == 0:
                write_table(frame, args.output)
                print(f"checkpoint: {completed}/{len(jobs)}")
    write_table(frame, args.output)
    print(frame["structure_qc_status"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()

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
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "input" / "lexical_structure_scoring_input.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "final" / "lexical_structure_scores.csv"
SYSTEM_PROMPT = """你是一位汉语语言学专家，对汉语词汇结构有深入了解。
请根据我提供的词语，从以下十一种结构类型中选择一个最合适的类型。

(1) 联合型：两个意义相同、相近、相关或相反的词根并列组合。
(2) 偏正型：前一个词根修饰、限制后一个词根。
(3) 补充型：后一个词根补充说明前一个词根。
(4) 动宾型：前一个词根表示动作，后一个词根表示动作所支配的事物。
(5) 主谓型：前一个词根表示被陈述的事物，后一个词根陈述前一个词根。
(6) 叠音：由不成语素的音节重叠构成，是单语素词。
(7) 重叠：由相同的词根语素重叠构成。
(8) 连绵词：两个不同音节连缀成同一个语素。
(9) 音译外来词：音译的外来词。
(10) 前缀：词缀位于词根之前。
(11) 后缀：词缀位于词根之后。

请直接回复一个词：联合、偏正、补充、动宾、主谓、叠音、重叠、连绵词、音译外来词、前缀、后缀 中的一个，不要解释。"""


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
    load_env_file(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--word-column", default="word")
    parser.add_argument("--model", default=os.getenv("QWEN_STRUCTURE_MODEL", "qwen3.5-397b-a17b"))
    parser.add_argument("--base-url", default=os.getenv("QWEN_STRUCTURE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
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

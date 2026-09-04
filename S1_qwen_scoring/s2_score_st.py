#!/usr/bin/env python3
"""Score C1/C2 semantic transparency using first-token log probabilities.

The script intentionally fails closed when log probabilities are unavailable.
It never substitutes the generated integer for the probability-weighted score.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


RATINGS = tuple(str(i) for i in range(1, 8))
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
SYSTEM_PROMPT = "你是一个简体中文母语者，请严格按照提示要求只输出一个1-7的数字，不要多余文字。"
PROMPT_C1 = (PROMPTS_DIR / "semantic_transparency_c1.txt").read_text(encoding="utf-8")
PROMPT_C2 = (PROMPTS_DIR / "semantic_transparency_c2.txt").read_text(encoding="utf-8")


class MissingLogprobsError(RuntimeError):
    """The endpoint did not return usable first-token rating logprobs."""


def _field(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, dict) else getattr(item, name)


def weighted_score_from_top_logprobs(entries: Iterable[Any]) -> tuple[dict[str, float], float]:
    probs: dict[str, float] = {}
    for entry in entries:
        token = str(_field(entry, "token")).strip()
        if token in RATINGS:
            probs[token] = probs.get(token, 0.0) + math.exp(float(_field(entry, "logprob")))
    total = sum(probs.values())
    if total <= 0:
        raise MissingLogprobsError("no legal 1-7 token found in top_logprobs")
    normalized = {key: value / total for key, value in sorted(probs.items(), key=lambda kv: int(kv[0]))}
    score = sum(int(key) * value for key, value in normalized.items())
    return normalized, round(score, 4)


def score_from_response(response: Any) -> tuple[dict[str, float], float]:
    try:
        content = response.choices[0].logprobs.content
        entries = content[0].top_logprobs
    except (AttributeError, IndexError, TypeError) as exc:
        raise MissingLogprobsError("endpoint returned no first-token logprobs") from exc
    return weighted_score_from_top_logprobs(entries)


def prompt_for(word: str, position: int) -> str:
    if len(word) != 2:
        raise ValueError(f"expected exactly two characters, got {word!r}")
    template = PROMPT_C1 if position == 1 else PROMPT_C2
    return template.format(morpheme=word[position - 1], word=word)


def score_one(client: Any, word: str, position: int, model: str, retries: int) -> tuple[str, float]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_for(word, position)},
                ],
                temperature=0.0,
                max_tokens=100,
                logprobs=True,
                top_logprobs=5,
            )
            distribution, score = score_from_response(response)
            return json.dumps(distribution, ensure_ascii=False, separators=(",", ":")), score
        except MissingLogprobsError:
            raise
        except Exception as exc:  # network/provider errors are retried
            last_error = exc
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}")


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_excel(path) if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(path)


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".xlsx":
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--word-column", default="word")
    parser.add_argument("--model", default=os.getenv("QWEN_MODEL", "qwen3-max"))
    parser.add_argument("--base-url", default=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
    parser.add_argument("--api-key-env", default="QWEN_API_KEY")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"missing API key in environment variable {args.api_key_env}")
    from openai import OpenAI  # lazy import keeps offline tests network-free

    frame = read_table(args.output if args.resume and args.output.exists() else args.input)
    if args.word_column not in frame:
        raise SystemExit(f"missing word column: {args.word_column}")
    frame[args.word_column] = frame[args.word_column].fillna("").astype(str).str.strip()
    for column in ["qwen_c1_probability_distribution", "qwen_c1_score", "qwen_c2_probability_distribution", "qwen_c2_score", "st_qc_status"]:
        if column not in frame:
            frame[column] = "" if "distribution" in column or column.endswith("status") else float("nan")

    client = OpenAI(api_key=api_key, base_url=args.base_url)
    jobs = []
    for idx, row in frame.iterrows():
        word = row[args.word_column]
        if len(word) != 2:
            frame.at[idx, "st_qc_status"] = "invalid_word_length"
            continue
        if pd.isna(row["qwen_c1_score"]):
            jobs.append((idx, word, 1))
        if pd.isna(row["qwen_c2_score"]):
            jobs.append((idx, word, 2))

    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        future_map = {
            pool.submit(score_one, client, word, position, args.model, args.retries): (idx, word, position)
            for idx, word, position in jobs
        }
        for future in as_completed(future_map):
            idx, word, position = future_map[future]
            prefix = f"qwen_c{position}"
            try:
                distribution, score = future.result()
                frame.at[idx, f"{prefix}_probability_distribution"] = distribution
                frame.at[idx, f"{prefix}_score"] = score
            except MissingLogprobsError:
                frame.at[idx, "st_qc_status"] = "missing_logprobs"
            except Exception:
                frame.at[idx, "st_qc_status"] = "api_error"
            completed += 1
            if completed % max(1, args.checkpoint_every) == 0:
                write_table(frame, args.output)
                print(f"checkpoint: {completed}/{len(jobs)} requests")

    c1_ok = pd.to_numeric(frame["qwen_c1_score"], errors="coerce").between(1, 7)
    c2_ok = pd.to_numeric(frame["qwen_c2_score"], errors="coerce").between(1, 7)
    frame.loc[c1_ok & c2_ok, "st_qc_status"] = "valid"
    frame.loc[~(c1_ok & c2_ok) & frame["st_qc_status"].eq(""), "st_qc_status"] = "missing_score"
    write_table(frame, args.output)
    print(f"wrote {len(frame):,} rows to {args.output}; no existing valid scores were requested again")


if __name__ == "__main__":
    main()

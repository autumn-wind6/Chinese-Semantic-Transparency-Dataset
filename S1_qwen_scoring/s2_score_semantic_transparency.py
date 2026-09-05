#!/usr/bin/env python3
"""Score C1/C2 semantic transparency for the archived LDT word list.

With no arguments, this script reads ``data/input/LDT.xlsx``, keeps real words
with a human C1.ST value (the 8,785-word analysis set), and writes a rerun to
``data/final/Qwen_ST_rerun.xlsx``.  The archived result itself is
``data/final/Qwen_ST.xlsx`` and is never overwritten by the default command.
"""

from __future__ import annotations

import argparse
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "input" / "LDT.xlsx"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "final" / "Qwen_ST_rerun.xlsx"
RATINGS = tuple(str(i) for i in range(1, 8))
SYSTEM_PROMPT = "你是一个简体中文母语者，请严格按照提示要求只输出一个1-7的数字，不要多余文字。"

PROMPT_C1 = """语义透明度是衡量双字词中第一个语素与整词在意义上的关联程度的指标。
如果该语素的意义与整词的意义高度一致或直接构成整词的核心含义，则语义透明度高；
反之，如果该语素的意义与整词意义无关或仅间接相关，则语义透明度低。
请在1（完全无关）到7（极为相关）的量表上，评估以下双字词的语义透明度。
若该词有多个义项，请依据你最先想到的常用义项进行判断。中点（4分）代表中等程度的语义关联。
例如：“美”在“美丽”中直接体现“好看”之义，故评7分；“马”在“马虎”中与“粗心”之义无直接联系，故评1分。
输入为：{morpheme}，{word}。
请仅用1到7之间的数字作答，答案仅限数字。"""

PROMPT_C2 = """语义透明度是衡量双字词中第二个语素与整词在意义上的关联程度的指标。
如果该语素的意义与整词的意义高度一致或直接构成整词的核心含义，则语义透明度高；
反之，如果该语素的意义与整词意义无关或仅间接相关，则语义透明度低。
请在1（完全无关）到7（极为相关）的量表上，评估以下双字词的语义透明度。
若该词有多个义项，请依据你最先想到的常用义项进行判断。中点（4分）代表中等程度的语义关联。
例如：“丽”在“美丽”中直接体现“好看”之义，故评7分；“虎”在“马虎”中与“粗心”之义无直接联系，故评1分。
输入为：{morpheme}，{word}。
请仅用1到7之间的数字作答，答案仅限数字。"""

OUTPUT_COLUMNS = {
    1: ("Prompt", "prob_dist", "C1_ST_qwen"),
    2: ("prompt_1", "prob_dist_1", "C2_ST_qwen"),
}


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


class MissingLogprobsError(RuntimeError):
    """The endpoint did not return usable first-token rating probabilities."""


def _field(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, dict) else getattr(item, name)


def weighted_score(entries: Iterable[Any]) -> tuple[str, float]:
    probabilities: dict[int, float] = {}
    for entry in entries:
        token = str(_field(entry, "token")).strip()
        if token in RATINGS:
            rating = int(token)
            probabilities[rating] = probabilities.get(rating, 0.0) + math.exp(float(_field(entry, "logprob")))
    total = sum(probabilities.values())
    if total <= 0:
        raise MissingLogprobsError("top_logprobs contained no legal 1-7 token")
    probabilities = {rating: value / total for rating, value in probabilities.items()}
    distribution = ", ".join(f"{rating}:{probabilities[rating]:.4f}" for rating in sorted(probabilities))
    score = round(sum(rating * probability for rating, probability in probabilities.items()), 4)
    return distribution, score


def prompt_for(word: str, position: int) -> str:
    if len(word) != 2:
        raise ValueError(f"expected a two-character word, got {word!r}")
    template = PROMPT_C1 if position == 1 else PROMPT_C2
    return template.format(morpheme=word[position - 1], word=word)


def score_one(client: Any, prompt: str, model: str, retries: int) -> tuple[str, float]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=100,
                logprobs=True,
                top_logprobs=5,
            )
            entries = response.choices[0].logprobs.content[0].top_logprobs
            return weighted_score(entries)
        except (AttributeError, IndexError, TypeError) as exc:
            raise MissingLogprobsError("endpoint returned no first-token logprobs") from exc
        except MissingLogprobsError:
            raise
        except Exception as exc:
            last_error = exc
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}")


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".xlsx":
        frame.to_excel(path, index=False)
    else:
        frame.to_csv(path, index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--word-column", default="Word")
    parser.add_argument("--filter-column", default="C1.ST", help="keep non-missing rows; pass an empty string to disable")
    parser.add_argument("--real-column", default="Real", help="keep rows coded 1; pass an empty string to disable")
    parser.add_argument("--model", default=os.getenv("QWEN_MODEL", "qwen3-max"))
    parser.add_argument("--base-url", default=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
    parser.add_argument("--api-key-env", default="QWEN_API_KEY")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    load_env_file(REPO_ROOT / ".env")
    args = parse_args()
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"missing API key in environment variable {args.api_key_env}")
    from openai import OpenAI

    if args.resume and args.output.exists():
        frame = pd.read_excel(args.output) if args.output.suffix.lower() == ".xlsx" else pd.read_csv(args.output)
    else:
        frame = pd.read_excel(args.input) if args.input.suffix.lower() == ".xlsx" else pd.read_csv(args.input)
        if args.filter_column:
            if args.filter_column not in frame:
                raise SystemExit(f"missing filter column: {args.filter_column}")
            frame = frame.dropna(subset=[args.filter_column]).reset_index(drop=True)
        if args.real_column:
            if args.real_column not in frame:
                raise SystemExit(f"missing real-word column: {args.real_column}")
            frame = frame[pd.to_numeric(frame[args.real_column], errors="coerce").eq(1)].reset_index(drop=True)

    if args.word_column not in frame:
        raise SystemExit(f"missing word column: {args.word_column}")
    words = frame[args.word_column].fillna("").astype(str).str.strip()
    if not words.str.fullmatch(r"[\u4e00-\u9fff]{2}").all():
        raise SystemExit("the scoring set contains a blank or non-two-character Chinese word")

    for position, (prompt_column, distribution_column, score_column) in OUTPUT_COLUMNS.items():
        frame[prompt_column] = [prompt_for(word, position) for word in words]
        if distribution_column not in frame:
            frame[distribution_column] = ""
        if score_column not in frame:
            frame[score_column] = float("nan")

    client = OpenAI(api_key=api_key, base_url=args.base_url)
    jobs = []
    for index, word in words.items():
        for position, (prompt_column, _, score_column) in OUTPUT_COLUMNS.items():
            if pd.isna(frame.at[index, score_column]):
                jobs.append((index, position, frame.at[index, prompt_column]))

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        future_map = {
            pool.submit(score_one, client, prompt, args.model, args.retries): (index, position)
            for index, position, prompt in jobs
        }
        for completed, future in enumerate(as_completed(future_map), start=1):
            index, position = future_map[future]
            _, distribution_column, score_column = OUTPUT_COLUMNS[position]
            try:
                distribution, score = future.result()
                frame.at[index, distribution_column] = distribution
                frame.at[index, score_column] = score
            except Exception as exc:
                print(f"row {index}, C{position}: {exc}")
            if completed % max(1, args.checkpoint_every) == 0:
                write_table(frame, args.output)
                print(f"checkpoint: {completed}/{len(jobs)} requests")

    write_table(frame, args.output)
    print(f"wrote {len(frame):,} rows to {args.output}")


if __name__ == "__main__":
    main()

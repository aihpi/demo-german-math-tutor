#!/usr/bin/env python3
"""Download GSM8K and cache it as JSONL.

Run once; the resulting data/gsm8k_cache.jsonl is committed so the demo needs
no network. Stdlib only — the upstream dataset is already JSONL.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

SRC = (
    "https://raw.githubusercontent.com/openai/grade-school-math/master/"
    "grade_school_math/data/train.jsonl"
)

OUT = Path(__file__).resolve().parent.parent / "data" / "gsm8k_cache.jsonl"
CALC = re.compile(r"<<[^>]*>>")

# ponytail: keyword heuristic, good enough for filtering a demo; classify with
# the model if it misfires.
TOPICS = [
    ("percentages", ("percent", "%", "discount", "interest")),
    ("rates", ("per hour", "mph", "km/h", "speed", "miles per", "per minute")),
    ("fractions", ("fraction", "half", "third", "quarter", "two-thirds", "1/2", "1/3", "3/4")),
]


def topic_of(question: str) -> str:
    q = question.lower()
    for name, keywords in TOPICS:
        if any(k in q for k in keywords):
            return name
    return "arithmetic"


def parse(idx: int, question: str, answer: str) -> dict:
    body, _, final = answer.rpartition("####")
    steps = [CALC.sub("", line).strip() for line in body.strip().splitlines()]
    return {
        "id": f"gsm8k-train-{idx:04d}",
        "question": question.strip(),
        "steps": [s for s in steps if s],
        "answer": float(final.strip().replace(",", "")),
        "topic": topic_of(question),
    }


def main() -> int:
    with urllib.request.urlopen(SRC) as resp:
        raw = [json.loads(line) for line in resp.read().decode().splitlines() if line.strip()]
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w") as fh:
        for idx, row in enumerate(raw):
            fh.write(json.dumps(parse(idx, row["question"], row["answer"])) + "\n")
    print(f"wrote {len(raw)} problems to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Sample a GSM8K problem for the math-tutor skill. Prints one JSON object."""
import argparse
import json
import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data"
TOPICS = ("arithmetic", "fractions", "percentages", "rates", "geometry")
TRACKS = ("random", "demo", "hard")


def load(track: str = "random") -> list:
    if track == "demo":
        return json.loads((DATA / "demo_problems.json").read_text())
    if track == "hard":
        overlay = {p["id"]: p for p in json.loads((DATA / "hard_problems.json").read_text())}
        with (DATA / "math_cache.jsonl").open() as fh:
            return [overlay.get(json.loads(l)["id"], json.loads(l)) for l in fh]
    with (DATA / "gsm8k_cache.jsonl").open() as fh:
        return [json.loads(line) for line in fh]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", choices=TOPICS, help="filter by topic")
    ap.add_argument("--id", help="fetch one problem by id")
    ap.add_argument("--demo", action="store_true", help="use the curated demo set")
    ap.add_argument("--hard", action="store_true", help="use the hard (MATH) set")
    args = ap.parse_args()

    problems = load("hard" if args.hard else "demo" if args.demo else "random")
    if args.id:
        problems = [p for p in problems if p["id"] == args.id]
    if args.topic:
        problems = [p for p in problems if p["topic"] == args.topic]
    if not problems:
        print("no problem matched", file=sys.stderr)
        return 1

    print(json.dumps(random.choice(problems), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

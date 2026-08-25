#!/usr/bin/env python3
"""Cache the diagram-free, demo-sized slice of MATH (Hendrycks) as JSONL.

Two filters do the real work:
  * problems carrying Asymptote source need a picture we cannot render, and are
    unsolvable without it — dropped (roughly 40% of geometry)
  * Level 4-5 run past a demo slot — dropped

Unlike GSM8K, MATH solutions are prose, not one calculation per line, so no
`steps` are emitted. The tutor authors the step breakdown itself at runtime.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "math_cache.jsonl"
API = ("https://datasets-server.huggingface.co/rows?dataset=EleutherAI%2Fhendrycks_math"
       "&config={cfg}&split=test&offset={off}&length=100")
CONFIGS = ("geometry",)
LEVELS = ("Level 1", "Level 2", "Level 3")
def boxed(solution: str):
    """Extract \\boxed{...}, matching braces rather than regex.

    A regex stops at the first `}`, which truncates every nested answer —
    \\boxed{\\frac{17}{2}} becomes "\\frac{17". Silently wrong, and only at the
    very end of a session where it is most embarrassing.
    """
    start = solution.find(r"\boxed{")
    if start < 0:
        return None
    depth, i = 0, start + len(r"\boxed")
    for j in range(i, len(solution)):
        if solution[j] == "{":
            depth += 1
        elif solution[j] == "}":
            depth -= 1
            if depth == 0:
                return solution[i + 1:j].strip()
    return None


def usable(row: dict) -> bool:
    return (row["level"] in LEVELS
            and "[asy]" not in row["problem"]
            and "[asy]" not in row["solution"]
            and len(row["problem"]) < 400
            and boxed(row["solution"]) is not None)


def main() -> int:
    out = []
    for cfg in CONFIGS:
        for off in range(0, 700, 100):
            try:
                with urllib.request.urlopen(API.format(cfg=cfg, off=off), timeout=30) as r:
                    rows = [x["row"] for x in json.loads(r.read())["rows"]]
            except Exception as exc:                       # end of split, or a blip
                print(f"  {cfg}@{off}: {type(exc).__name__}", file=sys.stderr)
                break
            if not rows:
                break
            for i, row in enumerate(rows):
                if usable(row):
                    out.append({
                        "id": f"math-{cfg}-test-{off + i:04d}",
                        "label": f"MATH · {row['type']} · {row['level']} · #{off + i}",
                        "question": row["problem"].strip(),
                        "solution": row["solution"].strip(),
                        "answer": boxed(row["solution"]),
                        "topic": "geometry",
                        "story": False,
                    })
            time.sleep(0.2)

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w") as fh:
        for row in out:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} problems to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

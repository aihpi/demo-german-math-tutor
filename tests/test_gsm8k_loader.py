"""Cache integrity + loader CLI contract."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOADER = ROOT / "skills" / "math-tutor" / "gsm8k_loader.py"
TOPICS = {"arithmetic", "fractions", "percentages", "rates"}


def run(*args):
    return subprocess.run(
        [sys.executable, str(LOADER), *args], capture_output=True, text=True
    )


def test_cache_rows_are_well_formed():
    rows = [json.loads(l) for l in (ROOT / "data" / "gsm8k_cache.jsonl").open()]
    assert len(rows) > 7000
    ids = set()
    for r in rows:
        assert isinstance(r["answer"], (int, float))
        assert r["steps"] and all(s.strip() for s in r["steps"])
        assert "<<" not in " ".join(r["steps"])  # calculator annotations stripped
        assert r["topic"] in TOPICS
        ids.add(r["id"])
    assert len(ids) == len(rows)


def test_demo_problems_carry_german_and_trap():
    demo = json.loads((ROOT / "data" / "demo_problems.json").read_text())
    assert len(demo) >= 3
    for p in demo:
        assert p["question_de"].strip() and p["trap"].strip()
        assert 3 <= len(p["steps"]) <= 5  # short enough for a live demo


def test_id_round_trips():
    out = json.loads(run("--id", "gsm8k-train-0000").stdout)
    assert out["id"] == "gsm8k-train-0000"


def test_topic_filter_returns_that_topic():
    assert json.loads(run("--topic", "rates").stdout)["topic"] == "rates"


def test_demo_flag_stays_in_demo_set():
    demo_ids = {p["id"] for p in json.loads((ROOT / "data" / "demo_problems.json").read_text())}
    assert json.loads(run("--demo").stdout)["id"] in demo_ids


def test_unknown_id_exits_nonzero():
    assert run("--id", "nope").returncode != 0


def test_unknown_topic_is_rejected_not_crashed():
    r = run("--topic", "calculus")
    assert r.returncode != 0 and "invalid choice" in r.stderr

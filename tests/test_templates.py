#!/usr/bin/env python3
"""Build every tested GAME_DATA against its template and assert the result is sane.

Run:  python3 tests/test_templates.py

This is the one check that fails if a template abstraction leaks: every JSON in
tested_gamedata/ must produce a complete, marker-free HTML file.
"""
import json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "teaching-games"
GD = SKILL / "tested_gamedata"
sys.path.insert(0, str(SKILL / "scripts"))
import generate_game as gg  # noqa: E402

# Which template each tested GAME_DATA belongs to.
CASES = {
    "moe_routing":              "route_and_sort",
    "moe_routing_hard":         "route_and_sort",
    "email_triage":             "route_and_sort",
    "gradient_descent":         "parameter_control",
    "gradient_ascent_reward":   "parameter_control",
    "attention_weights":        "predict_and_verify",
    "next_word_probability":    "predict_and_verify",
}


def build_all(tmp: pathlib.Path) -> None:
    seen = {p.stem for p in (GD).glob("*.json")}
    assert seen == set(CASES), f"CASES out of sync with tested_gamedata/: {seen ^ set(CASES)}"

    for stem, template in CASES.items():
        data = json.loads((GD / f"{stem}.json").read_text())
        out = gg.build(template, data, tmp / f"{stem}.html")
        html = out.read_text()

        assert "__GAME_DATA__" not in html, f"{stem}: GAME_DATA marker survived"
        assert "__BASE_CSS__" not in html, f"{stem}: base-CSS marker survived"
        assert "--accent:  #FF7500" in html, f"{stem}: base stylesheet not inlined"
        assert "</script>" not in json.dumps(data), f"{stem}: raw </script> would break the page"

        # every {placeholder} in insight text must be one the engine actually fills
        known = {"score", "accuracy", "avgActivated", "savedPct", "bestStreak", "routed", "total",
                 "steps", "rate", "x", "value", "query", "top", "topP"}
        import re
        unknown = set(re.findall(r"\{(\w+)\}", data["insight"])) - known
        assert not unknown, f"{stem}: insight uses unknown placeholder(s) {unknown}"
        print(f"  ok  {stem:24} -> {template}")


def rejects_bad_input(tmp: pathlib.Path) -> None:
    bad = [
        ({}, "missing required"),
        ({"title": "t", "intro": {}, "destinations": [], "insight": "i"}, "intro without headline/body"),
        ({"title": "t", "intro": {"headline": "h", "body": "b"}, "insight": "i"}, "missing destinations"),
    ]
    for data, why in bad:
        try:
            gg.build("route_and_sort", data, tmp / "x.html")
        except ValueError:
            print(f"  ok  rejected: {why}")
        else:
            raise AssertionError(f"accepted invalid GAME_DATA ({why})")

    try:
        gg.build("no_such_template", {"title": "t"}, tmp / "x.html")
    except FileNotFoundError:
        print("  ok  rejected: unknown template name")
    else:
        raise AssertionError("accepted an unknown template name")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        build_all(tmp)
        rejects_bad_input(tmp)
    print("\nall template builds passed")

#!/usr/bin/env python3
"""Build every tested GAME_DATA against its template and assert the result is sane.

Run:  python3 tests/test_templates.py

This is the one check that fails if a template abstraction leaks: every JSON in
tested_gamedata/ must produce a complete, marker-free HTML file.
"""
import json, pathlib, re, sys, tempfile

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
    "precision_recall":         "balance_tradeoff",
    "bias_variance":            "balance_tradeoff",
    "hyperparameter_hunt":      "explore_grid",
    "ab_testing":               "explore_grid",
}


def build_all(tmp: pathlib.Path) -> None:
    seen = {p.stem for p in GD.glob("*.json")} - {"index"}   # index.json is the manifest, not a round
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
                 "destinations", "items",
                 "steps", "rate", "x", "value", "query", "top", "topP",
                 "threshold", "best", "metricA", "metricB", "nameA", "nameB",
                 "missed", "falseAlarms", "caught",
                 "bestX", "bestY", "bestValue", "globalValue", "reveals", "budget",
                 "strategy", "exploitPercent", "uniqueRegions", "optimalReveals"}
        # explore_grid keys its insight text by outcome; everything else has one string
        texts = ([i["body"] for i in data["insights"].values()] if "insights" in data
                 else [data["insight"]])
        unknown = set(re.findall(r"\{(\w+)\}", " ".join(texts))) - known
        assert not unknown, f"{stem}: insight uses unknown placeholder(s) {unknown}"
        print(f"  ok  {stem:24} -> {template}")


def cache_manifest_is_sound() -> None:
    """The fallback cache is the last line of defence on stage — check it points
    at real files, with the template each one was actually built for."""
    index = json.loads((GD / "index.json").read_text())
    listed = {}
    for e in index["entries"]:
        path = GD / e["file"]
        assert path.exists(), f"index.json points at missing {e['file']}"
        assert e["template"] == CASES[path.stem], (
            f"index.json maps {e['file']} to {e['template']}, but it is a {CASES[path.stem]} dataset")
        assert e["match"], f"{e['file']} has no match keywords, so it can never be reached"
        for m in e["match"]:
            assert m == m.lower(), f"match key {m!r} must be lowercase — lookup lowercases the concept"
            prev = listed.get(m)
            assert prev is None, f"match key {m!r} is claimed by both {prev} and {e['file']}"
            listed[m] = e["file"]
    covered = {e["file"] for e in index["entries"]}
    missing = {f"{k}.json" for k in CASES} - covered
    assert not missing, f"tested GAME_DATA absent from the fallback index: {missing}"
    print(f"  ok  cache manifest: {len(covered)} rounds, {len(listed)} match keys, no collisions")


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


def docs_match_reality() -> None:
    """No document may describe a template that exists as missing.

    SKILL.md once said balance_tradeoff was not built, hours after it was built.
    The agent read that and refused to make the game — correctly, it followed its
    instructions. The instructions were the bug, and nothing caught the drift.
    """
    built = {p.stem for p in (SKILL / "templates").glob("*.html")} - {"base"}
    docs = {name: (SKILL / name).read_text() for name in
            ("SKILL.md", "references/concept_to_template.md",
             "references/gamedata_format_guide.md", "README.md")}

    # Scope is the sentence, not the line: the bug that shipped had the template
    # name on one line and "not built" wrapped onto the next. A wider character
    # window instead false-positives on neighbouring prose.
    absent = re.compile(r"not built|are missing|do(?:es)? not exist|no engine|unbuilt", re.I)
    for name, text in docs.items():
        flat = re.sub(r"\s+", " ", text)
        for sentence in re.split(r"(?<=[.!?])\s+", flat):
            if not absent.search(sentence):
                continue
            for t in sorted(built):
                assert t not in sentence, (
                    f"{name} calls the built template '{t}' missing:\n    {sentence.strip()}")
    print(f"  ok  no doc calls any of the {len(built)} built templates missing")

    for t in sorted(built):
        for name in ("references/concept_to_template.md", "references/gamedata_format_guide.md"):
            assert t in docs[name], f"{name} never mentions the built template '{t}'"
    print("  ok  every built template appears in both reference docs")

    # A stale count is the same drift wearing different clothes: "Three engines
    # exist" survived the template-name check because no name sits next to it.
    words = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}
    for name, text in docs.items():
        for m in re.finditer(r"(\w+) (?:game )?engines?\b", text, re.I):
            said = m.group(1).lower()
            if said in words.values():
                assert said == words[len(built)], (
                    f"{name} says '{m.group(0)}' but {len(built)} templates exist")
    print(f"  ok  no doc states a stale engine count ({len(built)} built)")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        build_all(tmp)
        rejects_bad_input(tmp)
        cache_manifest_is_sound()
        docs_match_reality()
    print("\nall template builds passed")

"""Skill contract: SKILL.md must stay loadable by Hermes and keep its clarify rules.

# ponytail: contract test, not a model eval — end-to-end quality stays manual.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "math-tutor" / "SKILL.md"
TEXT = SKILL.read_text()


def frontmatter():
    assert TEXT.startswith("---"), "frontmatter must be the first bytes"
    end = re.search(r"\n---\s*\n", TEXT[3:])
    assert end, "frontmatter must close with ---"
    return yaml.safe_load(TEXT[3 : end.start() + 3]), TEXT[end.end() + 3 :]


def test_hermes_can_load_it():
    fm, body = frontmatter()
    assert fm["name"] == "math-tutor"  # drives the /math-tutor slash command
    assert 0 < len(fm["description"]) <= 1024
    assert body.strip()
    assert len(TEXT) < 100_000


def test_clarify_rules_present():
    assert "clarify" in TEXT
    assert "exactly 3 choices" in TEXT.lower()
    assert re.search(r"never.{0,40}final answer", TEXT, re.I | re.S)


def test_session_script_named_in_body_exists():
    m = re.search(r"python3 \$\{HERMES_SKILL_DIR\}/(\S+\.py)", TEXT)
    assert m, "body must spell out the session command"
    assert (SKILL.parent / m.group(1)).exists()


def test_body_delegates_grading_rather_than_judging():
    assert "$T answer" in TEXT
    assert "$T route" in TEXT
    assert re.search(r"never judge the pick yourself", TEXT, re.I)
    assert re.search(r"follow it through", TEXT, re.I)  # wrong picks get real reasoning
    assert '"verdict": "question"' in TEXT             # typed input is handled
    assert "$T world" in TEXT
    # the gui path failed once by being described but never spelled out
    assert "--render svg" in TEXT
    assert "$T compute" in TEXT
    assert re.search(r"student computes; you do not", TEXT, re.I)


def test_body_opens_with_the_raw_to_story_transformation():
    """The dataset row must be shown before the rewrite, or nothing looks generated."""
    assert re.search(r"GSM8K #\d+", TEXT)
    assert re.search(r"verbatim, as a quote", TEXT, re.I)
    assert re.search(r"every number", TEXT, re.I)
    raw = TEXT.index("Show the Raw Problem")
    assert raw < TEXT.index("Author the Route"), "the reveal comes before any math"
    assert "verbatim" in TEXT


# --- tutor_session.py: the guarantees SKILL.md relies on ---------------------

SESSION = SKILL.parent / "tutor_session.py"
UNBAKED = "gsm8k-train-0003"      # 4 steps, no baked route, every step computes
CURATED = "math-geometry-test-0029"  # the hand-decomposed triangle-inequality problem
def route_of(n):
    """A well-formed n-step route; step 1 carries the strings the tests assert on."""
    steps = [{"choices": ["Correct approach", "Wrong one", "Wrong two"], "correct": 1}]
    steps += [{"choices": [f"Right {i}", f"No {i}", f"Also no {i}"], "correct": 1}
              for i in range(2, n + 1)]
    return json.dumps(steps)


def awaiting(session, tmp_path):
    """The number the script is waiting for. White-box, because it is deliberately
    never returned — the student is supposed to work it out."""
    st = json.loads((tmp_path / f"math-tutor-{session}.json").read_text())
    return st["steps"][st["index"]]["awaiting"]


def tutor(session, *args, stdin=None):
    r = subprocess.run(
        [sys.executable, str(SESSION), "--session", session, *args],
        input=stdin, capture_output=True, text=True,
    )
    return r, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else None)


@pytest.fixture
def started(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    name = "pytest-session"
    total = tutor(name, "start", "--id", UNBAKED)[1]["total_steps"]
    tutor(name, "route", stdin=route_of(total))
    yield name


def test_a_committed_route_cannot_be_overwritten(started):
    other = json.dumps([{"choices": ["A", "B", "C"], "correct": 2}] * 4)
    _, out = tutor(started, "route", stdin=other)
    assert out["committed"] is False
    assert set(out["choices"]) == {"Correct approach", "Wrong one", "Wrong two"}


def test_same_wrong_pick_gets_the_same_verdict(started):
    first = tutor(started, "answer", "Wrong one")[1]
    second = tutor(started, "answer", "Wrong one")[1]
    assert first["verdict"] == second["verdict"] == "wrong"
    assert first["picked"] == second["picked"] == "Wrong one"
    assert first["choices"] == second["choices"], "re-ask must not reorder"


def test_the_script_ships_no_canned_explanations(started):
    """Reasoning is the model's job — freezing it turns the demo into a quiz."""
    out = tutor(started, "answer", "Wrong two")[1]
    assert out["picked"] == "Wrong two"
    assert not {"explain", "why_wrong", "why_correct"} & set(out)


def test_typed_input_becomes_a_question_not_an_error(started):
    r, out = tutor(started, "answer", "Warum kann ich nicht zuerst teilen?")
    assert r.returncode == 0
    assert out["verdict"] == "question"
    assert out["asked"] == "Warum kann ich nicht zuerst teilen?"
    assert "Correct approach" in out["choices"]  # same step is re-asked


def test_a_typed_answer_can_be_mapped_and_graded(started):
    """Typing the right answer must advance the step, not send them to the buttons."""
    r, out = tutor(started, "answer", "in my own words, the first thing", "--as",
                   str(tutor(started, "answer", "x")[1]["choices"].index("Correct approach") + 1))
    assert r.returncode == 0
    assert out["verdict"] == "correct"
    assert out["picked"] == "Correct approach"


def test_mapping_does_not_decide_correctness(started):
    """--as says which choice they meant; the script still says if it is right."""
    wrong = tutor(started, "answer", "x")[1]["choices"].index("Wrong one") + 1
    out = tutor(started, "answer", "my own phrasing", "--as", str(wrong))[1]
    assert out["verdict"] == "wrong", "a mapped answer is graded, not accepted"


def test_typed_answers_are_recorded_as_typed(started):
    n = tutor(started, "answer", "x")[1]["choices"].index("Correct approach") + 1
    tutor(started, "answer", "meine eigenen Worte", "--as", str(n))
    entry = [e for e in tutor(started, "summary")[1]["path"] if e.get("typed")]
    assert entry and entry[0]["typed"] == "meine eigenen Worte"


def test_a_question_does_not_count_as_a_wrong_pick(started):
    for _ in range(3):
        tutor(started, "answer", "Aber warum denn?")
    assert tutor(started, "answer", "Wrong one")[1]["wrong_picks"] == 1


def test_renamed_nouns_reach_the_choices_and_the_grading(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("w", "start", "--id", "gsm8k-train-0113", "--lang", "de")
    _, out = tutor("w", "world", '{"items": "Kristalle", "items_dat": "Kristallen"}')
    assert all("{" not in c for c in out["choices"]), "no placeholder may reach the panel"
    assert "Kristallen" in out["choices"][0]
    # the dressed string is what the student sees, so it must grade
    assert tutor("w", "answer", out["choices"][0])[1]["verdict"] == "correct"


def test_world_rejects_a_noun_the_problem_does_not_have(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("w2", "start", "--id", "gsm8k-train-0113", "--lang", "de")
    assert tutor("w2", "world", '{"vehicle": "Rakete"}')[0].returncode != 0


def test_every_baked_choice_resolves_with_the_default_nouns(tmp_path, monkeypatch):
    """A presenter who skips the world step must still see clean German."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    demo = json.loads((ROOT / "data" / "demo_problems.json").read_text())
    for prob in demo:
        for lang, steps in prob["route"].items():
            nouns = prob["nouns"][lang]
            for st in steps:
                for c in st["choices"]:
                    for key, word in nouns.items():
                        c = c.replace("{" + key + "}", word)
                    assert "{" not in c, f"{prob['id']}/{lang}: unresolved in {c!r}"


def test_hard_track_serves_a_real_math_problem(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    _, out = tutor("hard", "start", "--hard", "--id", CURATED, "--lang", "de")
    assert out["story"] is False, "abstract problems must not be restaged"
    assert "MATH" in out["label"] and "GSM8K" not in out["label"]
    assert len(out["choices"]) == 3, "the curated route needs no world step"


def test_a_random_hard_problem_asks_for_a_route(tmp_path, monkeypatch):
    """97 problems ship prose, not steps — the model breaks them down itself."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    _, out = tutor("rnd", "start", "--hard", "--id", "math-geometry-test-0023")
    assert isinstance(out["solution"], str), "MATH solutions are prose"
    assert out["total_steps"] is None
    assert "3-5" in out["next"]


def test_prose_problems_require_a_calculation_per_step(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("nocalc", "start", "--hard", "--id", "math-geometry-test-0023")
    bare = json.dumps([{"choices": ["a", "b", "c"], "correct": 1}] * 3)
    r, _ = tutor("nocalc", "route", stdin=bare)
    assert r.returncode != 0 and "calculation" in r.stderr


def test_prose_problems_reject_a_demo_length_overrun(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("long", "start", "--hard", "--id", "math-geometry-test-0023")
    one = json.dumps([{"choices": ["a", "b", "c"], "correct": 1, "calculation": "x"}])
    assert tutor("long", "route", stdin=one)[0].returncode != 0


def test_the_curated_overlay_agrees_with_the_dataset():
    """hard_problems.json replaces a cache row — it must not drift from it."""
    cache = {json.loads(l)["id"]: json.loads(l)
             for l in (ROOT / "data" / "math_cache.jsonl").open()}
    for prob in json.loads((ROOT / "data" / "hard_problems.json").read_text()):
        row = cache.get(prob["id"])
        assert row, f"{prob['id']} overlays a row that is no longer cached"
        for key in ("question", "answer", "label"):
            assert prob[key] == row[key], f"{prob['id']}: {key} drifted from the dataset"


def test_boxed_answers_survive_nested_braces():
    """A regex truncates \\boxed{\\frac{17}{2}} to "\\frac{17" — wrong, and only at the end."""
    rows = [json.loads(l) for l in (ROOT / "data" / "math_cache.jsonl").open()]
    assert len(rows) > 50
    for r in rows:
        assert r["answer"].count("{") == r["answer"].count("}"), r["id"]
        assert "[asy]" not in r["question"], f"{r['id']} needs a diagram we cannot draw"
        assert r["level"] if "level" in r else True


def test_figure_generators_refuse_impossible_input():
    sys.path.insert(0, str(SKILL.parent))
    from figures import circle, rectangle, triangle
    import pytest as _pytest
    for call in (lambda: triangle(8, 8, 20), lambda: circle(-1), lambda: rectangle(0, 5)):
        with _pytest.raises(SystemExit):
            call()


def test_the_hard_problem_traps_the_off_by_one(tmp_path, monkeypatch):
    """The demo hinges on 15/31 beating 16/32 — guard the whole path."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("h2", "start", "--hard", "--id", CURATED)
    pick = lambda text: tutor("h2", "answer", text)[1]
    calc = lambda n: tutor("h2", "compute", n)[1]
    assert pick("Apply the Triangle Inequality")["verdict"] == "correct"
    assert calc("16")["verdict"] == "correct"                       # the bound
    assert pick("Take 16, since 8 + 8 = 16.")["verdict"] == "wrong"  # the off-by-one
    assert pick("greatest whole number strictly below 16")["verdict"] == "correct"
    assert calc("15")["verdict"] == "correct"
    assert pick("Add all three side lengths")["verdict"] == "correct"
    assert calc("31")["verdict"] == "correct"
    assert tutor("h2", "summary")[1]["answer"] == "31"


def test_the_trap_pick_returns_a_figure(tmp_path, monkeypatch):
    """Geometry needs a picture, and the TUI can only show text — so ship text."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("fig", "start", "--hard", "--id", CURATED, "--lang", "de")
    tutor("fig", "answer", "Die Dreiecksungleichung anwenden")
    tutor("fig", "compute", "16")   # step 1 correct
    out = tutor("fig", "answer", "16 nehmen")[1]                 # step 2: the 16 trap
    assert out["verdict"] == "wrong"
    assert "●" in out["figure"] and "16" in out["figure"]
    # the degenerate case must read as a straight line, not a triangle
    assert "╱" not in out["figure"]


def test_svg_render_mode_serves_a_real_file_over_loopback(tmp_path, monkeypatch):
    """data: and file: are both rejected by the desktop renderer — http is the way."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("svg", "start", "--hard", "--id", CURATED, "--lang", "de", "--render", "svg")
    tutor("svg", "answer", "Die Dreiecksungleichung anwenden")
    tutor("svg", "compute", "16")
    fig = tutor("svg", "answer", "16 nehmen")[1]["figure"]
    m = re.fullmatch(r"!\[figure\]\(http://127\.0\.0\.1:(\d+)/([0-9a-f]{12}\.svg)\)",
                     fig["markdown"])
    assert m, fig["markdown"]
    served = tmp_path / "math-tutor-figures" / m.group(2)
    assert served.exists() and served.read_text().startswith("<svg")


def test_figure_filenames_are_content_addressed(tmp_path, monkeypatch):
    """A server left running from an earlier session must not serve a stale figure."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    names = []
    for session in ("a", "b"):
        tutor(session, "start", "--hard", "--id", CURATED, "--lang", "de", "--render", "svg")
        tutor(session, "answer", "Die Dreiecksungleichung anwenden")
        tutor(session, "compute", "16")
        names.append(tutor(session, "answer", "16 nehmen")[1]["figure"]["markdown"])
    assert names[0] == names[1], "same figure must resolve to the same URL"


def test_text_render_mode_is_the_default(tmp_path, monkeypatch):
    """A presenter who forgets the flag must still get something legible."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("txt", "start", "--hard", "--id", CURATED, "--lang", "de")
    tutor("txt", "answer", "Die Dreiecksungleichung anwenden")
    tutor("txt", "compute", "16")
    assert isinstance(tutor("txt", "answer", "16 nehmen")[1]["figure"], str)


def test_generator_refuses_an_impossible_triangle():
    """A figure that contradicts the maths is worse than no figure."""
    r = subprocess.run(
        [sys.executable, str(SKILL.parent / "figures.py"), "triangle",
         "--sides", "8", "8", "20"], capture_output=True, text=True)
    assert r.returncode != 0 and "no such triangle" in r.stderr


def test_generated_figures_animate():
    sys.path.insert(0, str(SKILL.parent))
    from figures import triangle
    svg = triangle(8, 8, 15, caption="x")
    assert "@keyframes" in svg and "stroke-dashoffset" in svg


def test_the_degenerate_triangle_has_no_height():
    """8 + 8 = 16 must render flat, or the demo's whole point is lost."""
    sys.path.insert(0, str(SKILL.parent))
    from figures import triangle
    import xml.etree.ElementTree as ET
    root = ET.fromstring(triangle(8, 8, 16, caption="x"))
    ns = "{http://www.w3.org/2000/svg}"
    apex = root.find(f"{ns}g/{ns}path").get("d")
    ys = [float(p.split()[1]) for p in apex.replace("M", "").split("L")]
    assert len(set(round(y, 1) for y in ys)) == 1, f"not flat: {ys}"


def test_every_svg_figure_is_well_formed():
    import xml.etree.ElementTree as ET
    for prob in json.loads((ROOT / "data" / "hard_problems.json").read_text()):
        for lang, steps in prob["route"].items():
            for st in steps:
                for svg in st.get("figures_svg") or []:
                    if svg:
                        root = ET.fromstring(svg)  # raises on malformed markup
                        assert root.tag.endswith("svg") and "viewBox" in root.attrib


def test_figures_are_terminal_safe(tmp_path, monkeypatch):
    """A figure wider than 72 columns wraps and the alignment is destroyed."""
    for prob in json.loads((ROOT / "data" / "hard_problems.json").read_text()):
        for lang, steps in prob["route"].items():
            for st in steps:
                for fig in st.get("figures") or []:
                    if fig:
                        assert max(len(l) for l in fig.splitlines()) <= 72, prob["id"]


def test_figures_must_cover_every_choice(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("badfig", "start", "--id", UNBAKED)
    bad = json.dumps([{"choices": ["A", "B", "C"], "correct": 1, "figures": ["x"]}])
    assert tutor("badfig", "route", stdin=bad)[0].returncode != 0


def test_the_correct_position_is_shuffled_not_authored(tmp_path, monkeypatch):
    """Authors bias to position 1 — the shipped routes were 28/28. So shuffle.

    Checks the served order, not the JSON, because the model authors routes at
    runtime and biases exactly the same way.
    """
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    seen = set()
    for n in range(25):
        tutor(f"pos{n}", "start", "--demo", "--id", "gsm8k-train-0113", "--lang", "de")
        out = tutor(f"pos{n}", "world", "{}")[1]
        seen.add(out["choices"].index(
            next(c for c in out["choices"] if "um den Verlust zu finden" in c)))
    assert seen == {0, 1, 2}, f"correct answer only ever appeared at {sorted(seen)}"


def test_questions_are_kept_for_the_summary(started):
    tutor(started, "answer", "Warum nicht andersherum?")
    tutor(started, "answer", "Correct approach")
    assert "Warum nicht andersherum?" in tutor(started, "summary")[1]["questions"]


def test_hint_fires_on_the_third_wrong_pick(started):
    assert [tutor(started, "answer", "Wrong one")[1]["hint"]
            for _ in range(3)] == [False, False, True]


def test_correct_pick_asks_for_the_arithmetic_before_revealing_it(started):
    """The student does the maths — the approach alone must not advance the step."""
    out = tutor(started, "answer", "Correct approach")[1]
    assert out["verdict"] == "correct"
    assert "calculation" not in out, "the number must not be handed over"
    assert "choices" not in out, "the next step comes after they compute"
    assert "compute" in out["next"]


def test_computing_the_number_advances_and_reveals(started, tmp_path):
    tutor(started, "answer", "Correct approach")
    out = tutor(started, "compute", str(awaiting(started, tmp_path)))[1]
    assert out["verdict"] == "correct"
    assert out["calculation"]
    assert set(out["choices"]) == {"Right 2", "No 2", "Also no 2"}  # no authoring turn


def test_a_wrong_number_never_leaks_the_right_one(started, tmp_path):
    tutor(started, "answer", "Correct approach")
    assert awaiting(started, tmp_path) != 99
    out = tutor(started, "compute", "99")[1]
    assert out["verdict"] == "wrong" and out["their_number"] == 99
    assert "calculation" not in out
    assert tutor(started, "compute", "98")[1]["hint"] is True  # escalates on the second


def test_a_numbered_question_is_not_graded_as_an_answer(started):
    """"warum 20 Prozent?" contains a number but is not an attempt."""
    tutor(started, "answer", "Correct approach")
    out = tutor(started, "compute", "warum 20 Prozent?")[1]
    assert out["verdict"] == "unclear"


def test_compute_accepts_a_number_with_units(started, tmp_path):
    tutor(started, "answer", "Correct approach")
    n = awaiting(started, tmp_path)
    assert tutor(started, "compute", f"{n:g} Seiten")[1]["verdict"] == "correct"


def test_german_renderings_keep_every_number(tmp_path, monkeypatch):
    """Units may be localized 1:1; numbers may not move, or the route breaks."""
    demo = json.loads((ROOT / "data" / "demo_problems.json").read_text())
    for prob in demo:
        nums = lambda t: sorted(re.findall(r"\d+(?:[.,]\d+)?", t))
        assert nums(prob["question"]) == nums(prob["question_de"]), prob["id"]


def test_start_always_quotes_the_english_dataset_row(tmp_path, monkeypatch):
    """GSM8K is English — quoting a translation under a GSM8K label shows nothing."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    _, out = tutor("src", "start", "--id", "gsm8k-train-0019", "--lang", "de")
    assert out["source"].startswith("Tim rides his bike")
    assert "Kilometer" in out["reference"]  # German is a terminology aid only


def test_demo_problems_need_no_authoring(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    for lang in ("en", "de"):
        name = f"baked-{lang}"
        _, out = tutor(name, "start", "--demo", "--lang", lang)
        assert "solution" not in out, "nothing to author, so don't leak the solution"
        # choices arrive once the world is settled, even if nothing was renamed
        assert len(tutor(name, "world", "{}")[1]["choices"]) == 3


def test_route_rejects_a_malformed_definition(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("fresh", "start", "--id", UNBAKED)
    bad = json.dumps([{"choices": ["A", "A", "B"], "correct": 1}])
    assert tutor("fresh", "route", stdin=bad)[0].returncode != 0


def test_answer_without_a_session_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    assert tutor("no-such-session", "answer", "1")[0].returncode != 0


def test_wrong_step_count_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    tutor("short", "start", "--id", UNBAKED)
    one = json.dumps([{"choices": ["A", "B", "C"], "correct": 1}])
    assert tutor("short", "route", stdin=one)[0].returncode != 0

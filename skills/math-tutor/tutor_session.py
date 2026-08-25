#!/usr/bin/env python3
"""Deterministic state for one tutoring session.

The model authors the choices once per step; this script stores them and grades
every pick against that stored definition. A wrong pick re-serves the identical
choices in the identical order, and the verdict for a given choice never changes
— neither of which the model can guarantee on its own.

    start   --demo | --hard | --id ID | --topic T [--lang de] [--render svg]
    world   '{"items": "Energiekristalle"}'              rename the nouns
    route                                 (JSON on stdin) commit every step, once
    answer  "<chosen text or number>" [--as N]           grade the approach
    compute "<their number>"                             grade the arithmetic
    summary                                              the path taken

The script owns what must not drift: the choice strings, which one is correct,
and where the session is. It deliberately owns no explanations — those are the
model's job, live, every time.
"""
import argparse
import hashlib
import json
import re
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gsm8k_loader import load  # noqa: E402

HINT_AFTER = 3


def state_path(session: str) -> Path:
    return Path(tempfile.gettempdir()) / f"math-tutor-{session or 'default'}.json"


def read(session: str) -> dict:
    p = state_path(session)
    if not p.exists():
        sys.exit("no active session — run `start` first")
    return json.loads(p.read_text())


def write(session: str, st: dict) -> None:
    state_path(session).write_text(json.dumps(st, ensure_ascii=False))


def out(**kw) -> None:
    print(json.dumps(kw, ensure_ascii=False, indent=2))


FIGURE_PORT = 8731
FIGURE_DIR = Path(tempfile.gettempdir()) / "math-tutor-figures"


def serving() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", FIGURE_PORT)) == 0


def ensure_figure_server() -> None:
    """Serve the figure directory over http, because that is the only way in.

    The desktop app's markdown renderer rejects `data:` image URIs and its
    hermes-media:// scheme serves audio/video only, so a local http origin is
    the sole route to an inline diagram. Bound to loopback, serving a directory
    that holds nothing but generated SVGs.
    """
    if serving():
        return
    FIGURE_DIR.mkdir(exist_ok=True)
    # ponytail: stdlib http.server is single-threaded; fine for a handful of
    # small files, swap for anything real if it ever serves more.
    subprocess.Popen(
        [sys.executable, "-m", "http.server", str(FIGURE_PORT),
         "--bind", "127.0.0.1", "--directory", str(FIGURE_DIR)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(40):  # ~4s, plenty for a local bind
        if serving():
            return
        time.sleep(0.1)


def figure_for(step: dict, n: int, render: str):
    """The diagram for choice n, in the form the current surface can show.

    A terminal gets Unicode. `--render svg` writes the SVG to the figure
    directory and returns a loopback URL the desktop app will actually load.
    """
    if render == "svg" and step.get("figures_svg"):
        svg = step["figures_svg"][n - 1]
        if svg:
            FIGURE_DIR.mkdir(exist_ok=True)
            # Content-hashed, so a stale server never serves a stale figure.
            name = f"{hashlib.sha1(svg.encode()).hexdigest()[:12]}.svg"
            (FIGURE_DIR / name).write_text(svg)
            ensure_figure_server()
            return {"markdown": f"![figure](http://127.0.0.1:{FIGURE_PORT}/{name})"}
    return (step.get("figures") or [None] * 3)[n - 1]


NUM = re.compile(r"-?\d[\d.,]*")


def parse_number(text: str):
    """First number in a string, tolerant of units, currency and German commas."""
    m = NUM.search(str(text).replace("\u00a0", " "))
    if not m:
        return None
    raw = m.group(0).rstrip(".,")
    if "," in raw and "." not in raw:      # German decimal comma
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


PAIR = re.compile(r"\(\s*-?\d[^)]*,[^)]*\)")


def result_of(calculation: str):
    """The number a worked step lands on — or None if that is not obvious.

    Only the text after the last `=` or the last ` is ` counts, so
    "the greatest whole number below 16 is 15" gives 15, not 16. A coordinate
    pair yields nothing: there is no single number to ask for. Returning None
    is the safe outcome — the step just skips the arithmetic beat instead of
    marking a correct student wrong against a misparsed expectation.
    """
    text = str(calculation)
    for sep in ("=", " is "):
        if sep in text:
            tail = text.rsplit(sep, 1)[-1]
            return None if PAIR.search(tail) else parse_number(tail)
    return None


def shuffle_step(step: dict, rng) -> dict:
    """Randomise which position holds the correct answer.

    Authors bias towards putting it first — the shipped routes were 28 out of 28
    at position 1, and the model does the same. A student who notices can win
    without reading, and on stage it reads as a rigged demo. Figures travel with
    their choice, so the picture always matches the option it belongs to.
    """
    order = list(range(3))
    rng.shuffle(order)
    out = dict(step)
    out["choices"] = [step["choices"][i] for i in order]
    for key in ("figures", "figures_svg"):
        if step.get(key):
            out[key] = [step[key][i] for i in order]
    out["correct"] = order.index(step["correct"] - 1) + 1
    return out


def dataset_steps(problem: dict) -> list:
    """GSM8K ships one calculation per step; MATH ships prose and none."""
    return problem.get("steps") or []


def dress(choices: list, nouns: dict) -> list:
    """Swap {items}/{people} placeholders for the nouns of the chosen world.

    The choice strings stay script-owned — only the nouns move — so the buttons
    can follow the story without the model rewriting them.
    """
    for key, word in nouns.items():
        choices = [c.replace("{" + key + "}", word) for c in choices]
    return choices


def cmd_start(a) -> None:
    import random

    track = "hard" if a.hard else "demo" if a.demo else "random"
    problems = load(track)
    if track == "random":  # a cached problem that also ships a baked route uses it
        baked_by_id = {p["id"]: p for p in load("demo")}
        problems = [baked_by_id.get(p["id"], p) for p in problems]
    if a.id:
        problems = [p for p in problems if p["id"] == a.id]
    if a.topic:
        problems = [p for p in problems if p["topic"] == a.topic]
    if not problems:
        sys.exit("no problem matched")

    problem = random.choice(problems)
    baked = (problem.get("route") or {}).get(a.lang) or []
    st = {"problem": problem, "lang": a.lang, "index": 0, "render": a.render,
          "nouns": (problem.get("nouns") or {}).get(a.lang, {}),
          "steps": [shuffle_step(dict(s, wrong_picks=0), random.Random(f"{a.session}:{i}"))
                    for i, s in enumerate(baked)],
          "log": []}
    write(a.session, st)

    # `source` is always the English dataset row — that is what gets quoted on
    # screen. A German rendering, where one exists, is only a terminology aid.
    payload = dict(
        id=problem["id"],
        label=problem.get("label", f"GSM8K #{problem['id'].rsplit('-', 1)[-1]}"),
        source=problem["question"],
        reference=problem.get("question_de") if a.lang == "de" else None,
        total_steps=len(dataset_steps(problem)) or None,
        # Abstract problems have no world to move to — don't try to restage them.
        story=problem.get("story", True),
    )
    if baked and payload["story"]:  # show the raw text and offer worlds first
        payload.update(nouns=st["nouns"],
                       next="show the raw question, let the student pick a world, then "
                            "register any renamed nouns with `world` before asking step 1")
    elif baked:  # abstract problem — present it as written and start
        payload.update(choices=dress(st["steps"][0]["choices"], st["nouns"]),
                       next="quote the problem under its label, restate it plainly, then "
                            "ask step 1 with clarify using these three strings verbatim")
    else:
        payload.update(solution=dataset_steps(problem) or problem.get("solution"),
                       trap=problem.get("trap", ""),
                       next="author every step now and commit them with `route`"
                            + ("" if dataset_steps(problem) else
                               " — this problem ships prose, not steps, so break it into "
                               "3-5 asks yourself and give each one a `calculation`"))
    out(**payload)


def validate(d: dict) -> dict:
    choices = [str(c).strip() for c in d["choices"]]
    if len(choices) != 3 or len(set(choices)) != 3:
        sys.exit("each step needs exactly 3 distinct choices")
    if not 1 <= int(d["correct"]) <= 3:
        sys.exit("`correct` must be 1, 2 or 3")
    step = {"choices": choices, "correct": int(d["correct"]), "wrong_picks": 0}
    if d.get("calculation"):  # required when the dataset ships no step breakdown
        step["calculation"] = str(d["calculation"])
    for key in ("figures", "figures_svg"):
        if d.get(key):  # optional diagram per choice
            if len(d[key]) != 3:
                sys.exit(f"`{key}` needs one entry per choice (use null for none)")
            step[key] = d[key]
    return step


def cmd_world(a) -> None:
    st = read(a.session)
    renamed = json.loads(a.nouns)
    unknown = set(renamed) - set(st["nouns"])
    if unknown and st["nouns"]:
        sys.exit(f"this problem has no {sorted(unknown)} to rename; "
                 f"it uses {sorted(st['nouns'])}")
    st["nouns"].update({k: str(v) for k, v in renamed.items()})
    write(a.session, st)
    step = st["steps"][st["index"]] if st["index"] < len(st["steps"]) else None
    out(nouns=st["nouns"],
        step=st["index"] + 1 if step else None,
        choices=dress(step["choices"], st["nouns"]) if step else None,
        next="ask this step with clarify, using these three strings verbatim"
             if step else "author the route with `route`")


def cmd_route(a) -> None:
    st = read(a.session)
    if st["steps"]:  # already committed — hand back what is stored
        out(committed=False, reason="this route is already defined; use these",
            step=st["index"] + 1,
            choices=dress(st["steps"][st["index"]]["choices"], st["nouns"]))
        return

    import random

    steps = [shuffle_step(validate(d), random.Random(f"{a.session}:{i}"))
             for i, d in enumerate(json.load(sys.stdin))]
    dataset = dataset_steps(st["problem"])
    if dataset and len(steps) != len(dataset):
        sys.exit(f"need one entry per solution step ({len(dataset)})")
    if not dataset:
        if not 3 <= len(steps) <= 5:
            sys.exit("author 3-5 steps — fewer is not tutoring, more overruns the demo")
        missing = [i + 1 for i, s in enumerate(steps) if "calculation" not in s]
        if missing:
            sys.exit(f"steps {missing} need a `calculation`: this problem ships no "
                     f"step breakdown, so you supply the arithmetic shown after a "
                     f"correct pick")
    st["steps"] = steps
    write(a.session, st)
    out(committed=True, total_steps=len(steps), step=1,
        choices=dress(steps[0]["choices"], st["nouns"]),
        next="ask step 1 with clarify, using these three strings verbatim")


def cmd_answer(a) -> None:
    st = read(a.session)
    i = st["index"]
    if i >= len(st["steps"]):
        sys.exit("no committed route to answer — run `route` first")
    step = st["steps"][i]

    pick, typed = a.choice.strip(), False
    if pick.isdigit() and 1 <= int(pick) <= 3:
        n = int(pick)
    else:
        shown = dress(step["choices"], st["nouns"])
        matches = [j for j, c in enumerate(shown, 1) if c.lower() == pick.lower()]
        if not matches:  # tolerate light paraphrasing of the choice text
            matches = [j for j, c in enumerate(shown, 1) if pick.lower() in c.lower()]
        if not matches and a.as_choice:
            # The student answered in their own words and the model mapped it to
            # a choice. Mapping is interpretation, which the model is good at;
            # whether that choice is correct stays this script's call.
            matches = [a.as_choice]
            typed = True
        if len(matches) != 1:
            # The student typed something of their own via clarify's "Other" row.
            # That is the interesting case, not an error.
            st["log"].append({"step": i + 1, "asked": pick})
            write(a.session, st)
            out(verdict="question", asked=pick,
                choices=dress(step["choices"], st["nouns"]),
                next="if this was a QUESTION, answer it in your own words — revealing "
                     "nothing about which choice is correct — then re-ask this step "
                     "with clarify using these three strings verbatim. If it was an "
                     "ATTEMPT AT THE ANSWER, do not judge it yourself: call `answer` "
                     "again with --as N naming the choice it means")
            return
        n = matches[0]

    entry = {"step": i + 1, "picked": dress([step["choices"][n - 1]], st["nouns"])[0],
             "correct": n == step["correct"]}
    if typed:
        entry["typed"] = pick   # they answered in their own words, not by tapping
    st["log"].append(entry)

    if n == step["correct"]:
        calc = step.get("calculation") or dataset_steps(st["problem"])[i]
        expected = step.get("result", result_of(calc))
        if expected is not None:
            # They chose the right method. Now they do the arithmetic — the whole
            # point of a maths tutor is that the student computes, not the tutor.
            step["awaiting"] = expected
            write(a.session, st)
            out(verdict="correct", picked=dress([step["choices"][n - 1]], st["nouns"])[0],
                figure=figure_for(step, n, st.get("render", "text")),
                next="say in one sentence why this approach works — WITHOUT doing the "
                     "arithmetic and without naming the result. Then ask them for the "
                     "number with clarify and NO choices, and pass their reply to "
                     "`compute`")
            return

        st["index"] = i + 1
        write(a.session, st)
        done = st["index"] >= len(st["steps"])
        out(verdict="correct", picked=dress([step["choices"][n - 1]], st["nouns"])[0],
            figure=figure_for(step, n, st.get("render", "text")),
            calculation=calc,
            choices=None if done else dress(st["steps"][st["index"]]["choices"], st["nouns"]),
            next="say in one sentence why this approach works, show the calculation, "
                 + ("then run `summary`" if done else
                    "then ask the next step with clarify, using these three strings verbatim"))
        return

    step["wrong_picks"] += 1
    write(a.session, st)
    out(verdict="wrong", picked=dress([step["choices"][n - 1]], st["nouns"])[0],
        figure=figure_for(step, n, st.get("render", "text")),
        wrong_picks=step["wrong_picks"], hint=step["wrong_picks"] >= HINT_AFTER,
        choices=dress(step["choices"], st["nouns"]),
        next="explain why THIS approach fails on THIS problem: follow it through to the "
             "number it would produce and say what is wrong with that number. Reveal "
             "nothing about the other two. Then re-ask with clarify, using these three "
             "strings verbatim"
             + (". This is their third miss — rule one distractor out first"
                if step["wrong_picks"] >= HINT_AFTER else ""))


def cmd_compute(a) -> None:
    st = read(a.session)
    i = st["index"]
    if i >= len(st["steps"]) or "awaiting" not in st["steps"][i]:
        sys.exit("nothing to compute — the approach for this step is not settled yet")
    step = st["steps"][i]
    expected = step["awaiting"]

    # "warum 20 Prozent?" contains a number but is a question, not an answer.
    # Grading it as 20 would be both wrong and insulting.
    value = a.value.strip()
    got = None if ("?" in value or len(value.split()) > 6) else parse_number(value)
    if got is None:
        out(verdict="unclear", asked=value,
            next="that is not a bare number. If it was a question, answer it without "
                 "giving the result away and ask for the number again; otherwise ask "
                 "them to state just the number")
        return

    step["tries"] = step.get("tries", 0) + 1
    if abs(got - expected) > 1e-6:
        st["log"].append({"step": i + 1, "computed": got, "correct": False})
        write(a.session, st)
        out(verdict="wrong", their_number=got, tries=step["tries"],
            hint=step["tries"] >= 2,
            next="do not give them the number. Say what their number would have "
                 "meant, or which part of the calculation to re-check, and ask "
                 "again with clarify and no choices"
                 + (". Second miss — walk them through the operation one term at "
                    "a time, still without stating the result" if step["tries"] >= 2 else ""))
        return

    calc = step.get("calculation") or dataset_steps(st["problem"])[i]
    st["log"].append({"step": i + 1, "computed": got, "correct": True})
    st["index"] = i + 1
    write(a.session, st)
    done = st["index"] >= len(st["steps"])
    out(verdict="correct", their_number=got, calculation=calc,
        choices=None if done else dress(st["steps"][st["index"]]["choices"], st["nouns"]),
        next="confirm the number in a few words" + (
            ", then run `summary`" if done else
            ", restate where we are, then ask the next step with clarify using these "
            "three strings verbatim"))


def cmd_summary(a) -> None:
    st = read(a.session)
    out(id=st["problem"]["id"], answer=st["problem"]["answer"],
        solution=dataset_steps(st["problem"]) or st["problem"].get("solution"),
        path=st["log"],
        mistakes=[e for e in st["log"] if e.get("correct") is False],
        questions=[e["asked"] for e in st["log"] if "asked" in e])
    state_path(a.session).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", default=os.environ.get("HERMES_SESSION_ID", ""))
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start")
    s.add_argument("--demo", action="store_true")
    s.add_argument("--hard", action="store_true")
    s.add_argument("--render", default="text", choices=("text", "svg"),
                   help="svg for image-capable surfaces (desktop app, Telegram)")
    s.add_argument("--id")
    s.add_argument("--topic", choices=("arithmetic", "fractions", "percentages",
                                      "rates", "geometry"))
    s.add_argument("--lang", default="en", choices=("en", "de"))
    s.set_defaults(fn=cmd_start)

    w = sub.add_parser("world")
    w.add_argument("nouns", help='JSON, e.g. \'{"items": "Energiekristalle"}\'')
    w.set_defaults(fn=cmd_world)

    sub.add_parser("route").set_defaults(fn=cmd_route)

    a = sub.add_parser("answer")
    a.add_argument("choice")
    a.add_argument("--as", dest="as_choice", type=int, choices=(1, 2, 3),
                   help="the choice a free-text answer means; grading stays ours")
    a.set_defaults(fn=cmd_answer)

    cp = sub.add_parser("compute")
    cp.add_argument("value")
    cp.set_defaults(fn=cmd_compute)

    sub.add_parser("summary").set_defaults(fn=cmd_summary)

    args = ap.parse_args()
    args.fn(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

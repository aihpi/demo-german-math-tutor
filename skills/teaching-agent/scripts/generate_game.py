#!/usr/bin/env python3
"""Inject a GAME_DATA object into a teaching-agent template.

    generate_game.py --template route_and_sort --game-data-file moe_routing.json
    generate_game.py --template route_and_sort --game-data '{"title": ...}'

Writes a standalone HTML file (default /tmp/game.html) and prints its path.
"""
import argparse, json, os, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

# Fields a template's engine reads unconditionally. Anything else has a default.
REQUIRED = {
    "route_and_sort":     ["title", "intro", "destinations", "insight"],
    "parameter_control":  ["title", "intro", "landscape", "insight"],
    "predict_and_verify": ["title", "intro", "items", "insight"],
    "balance_tradeoff":   ["title", "intro", "insight"],
    "explore_grid":       ["title", "intro", "grid", "landscape", "insights"],
}


def js_literal(data) -> str:
    """JSON that is safe to paste inside a <script> block."""
    out = json.dumps(data, ensure_ascii=False, indent=2)
    out = out.replace("<", "\\u003c")            # can never close the script tag
    for ch in (0x2028, 0x2029):                 # line separators: illegal raw in JS
        out = out.replace(chr(ch), f"\\u{ch:04x}")
    return out


def validate(name: str, data) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"GAME_DATA must be a JSON object, got {type(data).__name__}")
    missing = [k for k in REQUIRED.get(name, []) if k not in data]
    if missing:
        raise ValueError(f"{name}: GAME_DATA is missing required field(s): {', '.join(missing)}")
    intro = data.get("intro")
    if not isinstance(intro, dict) or not intro.get("headline") or not intro.get("body"):
        raise ValueError(f"{name}: intro must be an object with 'headline' and 'body'")

    # Below: things that build fine and then break, or build fine and teach nothing.
    if name == "predict_and_verify":
        items, masked = data.get("items") or [], data.get("maskSelf", True)
        pairwise = all(isinstance(i.get("q"), list) and isinstance(i.get("v"), list) for i in items)
        floor = 4 if (pairwise and masked) else 3
        if len(items) < floor:
            raise ValueError(
                f"{name}: needs at least {floor} items"
                + (" (pairwise with maskSelf leaves one fewer to choose between)" if pairwise and masked else "")
                + f", got {len(items)}. Fewer makes the distribution degenerate — "
                  "the player cannot be wrong, so the game teaches nothing.")
        if pairwise:
            d = len(data.get("dims") or [])
            bad = [i["label"] for i in items if len(i["q"]) != d or len(i["v"]) != d]
            if bad:
                raise ValueError(f"{name}: q and v must each have {d} entries (one per dim); wrong on: {', '.join(bad)}")

    if name == "balance_tradeoff":
        known = {"precision", "recall", "sensitivity", "tpr", "ppv", "npv",
                 "specificity", "fpr", "accuracy", "f1"}
        if "items" in data:
            m = data.get("metrics") or {}
            unknown = {v for v in (m.get("a"), m.get("b"), data.get("objective", "f1")) if v and v not in known}
            if unknown:
                raise ValueError(f"{name}: unknown metric(s) {', '.join(sorted(unknown))}. "
                                 f"Use one of: {', '.join(sorted(known))}")
            scores = [(i.get("score"), i.get("positive")) for i in data.get("items") or []]
            pos = [s for s, p in scores if p]
            neg = [s for s, p in scores if not p]
            if pos and neg and max(neg) <= min(pos):
                raise ValueError(f"{name}: the classes separate cleanly (every positive outranks every "
                                 "negative), so a perfect threshold exists and the game disproves its own "
                                 "lesson. Make at least one negative score above the lowest positive.")
        elif "curves" not in data:
            raise ValueError(f"{name}: needs either `items` or `curves`")


def build(name: str, data, out: pathlib.Path) -> pathlib.Path:
    tpl = TEMPLATES / f"{name}.html"
    if not tpl.exists():
        have = ", ".join(sorted(p.stem for p in TEMPLATES.glob("*.html") if p.stem != "base"))
        raise FileNotFoundError(f"no template '{name}'. Available: {have}")
    validate(name, data)

    html = tpl.read_text()
    css = (TEMPLATES / "base.html").read_text().split("-->", 1)[1].strip()
    js = (TEMPLATES / "base.js").read_text()
    # GAME_DATA must land before base.js, which reads it at definition time.
    subs = [("/*__GAME_DATA__*/", js_literal(data)), ("/*__BASE_CSS__*/", css), ("/*__BASE_JS__*/", js)]
    for marker, value in subs:
        if marker not in html:
            if marker == "/*__BASE_JS__*/":
                continue                      # templates predating the customization runtime
            raise ValueError(f"{name}.html has no {marker} marker")
        html = html.replace(marker, value, 1)

    out.write_text(html)
    return out


# ---------------------------------------------------------------- authoring --
# Live GAME_DATA generation with deterministic retries. The retry lives here
# rather than in the agent loop because a model that just emitted broken JSON is
# the least reliable thing to ask for a correction — and on stage there is no
# second chance. Every failure path ends at a cached round that is known to play.

GD = ROOT / "tested_gamedata"


def cached_for(concept: str):
    """(template, data, filename) for the first manifest entry matching `concept`."""
    index = GD / "index.json"
    if not index.exists():
        return None
    needle = concept.lower()
    for e in json.loads(index.read_text())["entries"]:
        if any(m in needle for m in e["match"]):
            path = GD / e["file"]
            if path.exists():
                return e["template"], json.loads(path.read_text()), e["file"]
    return None


def model_config(args):
    """Endpoint from flags, then env, then the Hermes config already on this box."""
    base, key, model = args.base_url, args.api_key, args.model
    if not (base and key):
        cfg = pathlib.Path.home() / ".hermes/config.yaml"
        if cfg.exists():
            text = cfg.read_text()
            base = base or (re.search(r"base_url: (\S+)", text) or [None, None])[1]
            key = key or (re.search(r"api_key: (sk-\S+)", text) or [None, None])[1]
            model = model or (re.search(r"default: (\S+)", text) or [None, None])[1]
    return (base or os.environ.get("TEACHING_GAMES_BASE_URL"),
            key or os.environ.get("TEACHING_GAMES_API_KEY"),
            model or os.environ.get("TEACHING_GAMES_MODEL"))


def ask_model(base, key, model, messages, timeout=180):
    body = json.dumps({"model": model, "temperature": 0.2, "max_tokens": 4000,
                       "messages": messages}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions", body,
                                 {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.load(f)["choices"][0]["message"]["content"]


def author(concept: str, template: str | None, retries: int, args):
    """Ask the model for GAME_DATA, retrying with the exact error, then fall back.

    Returns (template, data, provenance). Provenance is reported on stderr only:
    stdout stays clean so the agent pastes the same thing either way and a
    fallback never becomes a visible stumble on stage.
    """
    base, key, model = model_config(args)
    docs = "\n\n".join((ROOT / f).read_text() for f in
                        ("references/concept_to_template.md", "references/gamedata_format_guide.md"))
    system = (docs + "\n\nReply with ONE JSON object and nothing else:\n"
              '{"template": "<name>", "game_data": {...}}')
    ask = f"Build a teaching game for: {concept}"
    if template:
        ask += f"\nUse the {template} template."

    messages = [{"role": "system", "content": system}, {"role": "user", "content": ask}]
    last = "no attempt made"

    if base and key and model:
        for attempt in range(retries + 1):
            raw = ""
            try:
                raw = ask_model(base, key, model, messages)
                blob = re.search(r"\{.*\}", raw, re.S)
                if not blob:
                    raise ValueError("no JSON object in the reply")
                obj = json.loads(blob.group(0))
                picked = obj.get("template") or template
                if picked in (None, "none"):
                    raise ValueError(f"model declined: {obj.get('reason', 'no reason given')}")
                validate(picked, obj["game_data"])          # same gate as --game-data-file
                return picked, obj["game_data"], f"model (attempt {attempt + 1})"
            except Exception as e:                          # noqa: BLE001 — any failure retries
                last = f"{type(e).__name__}: {e}"
                print(f"authoring attempt {attempt + 1} failed: {last}", file=sys.stderr)
                if attempt == retries:
                    break
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Your JSON was invalid: {last}. "
                                                "Fix it and return only valid JSON."},
                ]
    else:
        last = "no model endpoint configured"
        print(f"skipping live authoring: {last}", file=sys.stderr)

    fallback = cached_for(concept)
    if not fallback:
        raise ValueError(f"live authoring failed ({last}) and no cached round matches '{concept}'")
    tpl, data, name = fallback
    print(f"falling back to cached {name} after {retries + 1} attempts", file=sys.stderr)
    return tpl, data, f"cache ({name})"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--template", help="required unless --author picks one")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--game-data", help="GAME_DATA as a JSON string")
    g.add_argument("--game-data-file", help="path to a .json file")
    g.add_argument("--author", metavar="CONCEPT",
                   help="generate GAME_DATA live, retrying on invalid JSON, then falling back to cache")
    p.add_argument("--retries", type=int, default=2, help="authoring retries after the first attempt (default 2)")
    p.add_argument("--model"), p.add_argument("--base-url"), p.add_argument("--api-key")
    p.add_argument("--out", default="/tmp/game.html")
    p.add_argument("--serve", action="store_true",
                   help="publish on loopback http and print the preview marker to paste into chat")
    p.add_argument("--url-only", action="store_true",
                   help="with --serve, print the bare URL instead of the preview marker")
    a = p.parse_args()

    if a.author:
        try:
            template, data, how = author(a.author, a.template, max(0, a.retries), a)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        print(f"source: {how}", file=sys.stderr)
    else:
        if not a.template:
            print("--template is required unless you use --author", file=sys.stderr)
            return 2
        template = a.template
        raw = pathlib.Path(a.game_data_file).read_text() if a.game_data_file else a.game_data
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            # The model gets this message back verbatim, so say where it broke.
            print(f"invalid JSON at line {e.lineno} col {e.colno}: {e.msg}", file=sys.stderr)
            return 2
    try:
        out = build(template, data, pathlib.Path(a.out))
        if a.serve:
            from serve_game import publish, preview_marker   # same server as the figures, different port
            url = publish(out.read_text())
            print(url if a.url_only else preview_marker(url))
        else:
            print(out)
    except (ValueError, FileNotFoundError) as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

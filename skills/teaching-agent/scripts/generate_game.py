#!/usr/bin/env python3
"""Inject a GAME_DATA object into a teaching-agent template.

    generate_game.py --template route_and_sort --game-data-file moe_routing.json
    generate_game.py --template route_and_sort --game-data '{"title": ...}'

Writes a standalone HTML file (default /tmp/game.html) and prints its path.
"""
import argparse, json, pathlib, re, sys

import authoring

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
GD = ROOT / "tested_gamedata"

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


def author(concept: str, template: str | None, retries: int, args):
    docs = "\n\n".join((ROOT / f).read_text() for f in
                        ("references/concept_to_template.md", "references/gamedata_format_guide.md"))

    def unwrap(obj, _requested):
        picked = obj.get("template") or template
        if picked in (None, "none"):
            raise ValueError(f"model declined: {obj.get('reason', 'no reason given')}")
        return picked, obj["game_data"]

    return authoring.author(
        concept, template, retries, args,
        guide=docs + '\n\nReply with ONE JSON object and nothing else:\n'
                     '{"template": "<name>", "game_data": {...}}',
        validate=validate, cache_dir=GD, unwrap=unwrap,
        ask=lambda c, t: f"Build a teaching game for: {c}" + (f"\nUse the {t} template." if t else ""))


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

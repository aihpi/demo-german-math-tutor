#!/usr/bin/env python3
"""Inject a GAME_DATA object into a teaching-games template.

    generate_game.py --template route_and_sort --game-data-file moe_routing.json
    generate_game.py --template route_and_sort --game-data '{"title": ...}'

Writes a standalone HTML file (default /tmp/game.html) and prints its path.
"""
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

# Fields a template's engine reads unconditionally. Anything else has a default.
REQUIRED = {
    "route_and_sort":     ["title", "intro", "destinations", "insight"],
    "parameter_control":  ["title", "intro", "landscape", "insight"],
    "predict_and_verify": ["title", "intro", "items", "insight"],
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


def build(name: str, data, out: pathlib.Path) -> pathlib.Path:
    tpl = TEMPLATES / f"{name}.html"
    if not tpl.exists():
        have = ", ".join(sorted(p.stem for p in TEMPLATES.glob("*.html") if p.stem != "base"))
        raise FileNotFoundError(f"no template '{name}'. Available: {have}")
    validate(name, data)

    html = tpl.read_text()
    css = (TEMPLATES / "base.html").read_text().split("-->", 1)[1].strip()
    for marker, value in (("/*__BASE_CSS__*/", css), ("/*__GAME_DATA__*/", js_literal(data))):
        if marker not in html:
            raise ValueError(f"{name}.html has no {marker} marker")
        html = html.replace(marker, value, 1)

    out.write_text(html)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--template", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--game-data", help="GAME_DATA as a JSON string")
    g.add_argument("--game-data-file", help="path to a .json file")
    p.add_argument("--out", default="/tmp/game.html")
    p.add_argument("--serve", action="store_true",
                   help="also publish on loopback http and print the URL instead of the path")
    a = p.parse_args()

    raw = pathlib.Path(a.game_data_file).read_text() if a.game_data_file else a.game_data
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        # The model gets this message back verbatim, so say where it broke.
        print(f"invalid JSON at line {e.lineno} col {e.colno}: {e.msg}", file=sys.stderr)
        return 2
    try:
        out = build(a.template, data, pathlib.Path(a.out))
        if a.serve:
            from serve_game import publish          # same server the figures use, different port
            print(publish(out.read_text()))
        else:
            print(out)
    except (ValueError, FileNotFoundError) as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

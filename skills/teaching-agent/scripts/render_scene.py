#!/usr/bin/env python3
"""Render a JSON-driven Manim animation and hand back a marker the chat can play.

    render_scene.py --author "dense vs MoE inference"          # generate, retry, render
    render_scene.py --template comparison_split --data dense_vs_moe.json
    render_scene.py --author "..." --quality l                 # fast preview

Prints one line: a `#media:` marker the desktop app turns into an inline video
player. Provenance (which attempt worked, or that a cached scene was used) goes
to stderr, so stdout is identical whether the scene was authored live or not.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse

import authoring

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES, SCENE_DATA = ROOT / "manim_templates", ROOT / "scene_data"

# manim.constants.QUALITIES — the older copy of this map in the manim-animator
# skill omits "p", so a -qp render died on a KeyError instead of rendering.
QUALITY = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}

# manim writes media/ relative to CWD, so an agent invoked from /tmp scattered its
# renders into /tmp/media. Pin it: the marker carries an absolute path, and the
# agent's working directory is not ours to depend on.
MEDIA = pathlib.Path(tempfile.gettempdir()) / "teaching-agent-media"

REQUIRED = {"comparison_split": ["title", "left", "right"],
            "curve_plot":       ["title", "domain", "curves"],
            "pipeline_flow":    ["title", "stages", "item"]}
CURVE_TERMS = {"const", "lin", "quad", "sin", "cos", "exp", "inv"}


def resolve(kind: str, name: str, folder: pathlib.Path, suffix: str) -> pathlib.Path:
    for candidate in (pathlib.Path(name), folder / name, folder / f"{name}{suffix}"):
        if candidate.exists():
            return candidate.resolve()
    have = ", ".join(sorted(p.stem for p in folder.glob(f"*{suffix}")))
    sys.exit(f"no {kind} '{name}'. Available: {have}")


def scene_names(template: pathlib.Path) -> list[str]:
    return re.findall(r"^class (\w+)\(Scene\)", template.read_text(), re.M)


def validate(template: str, data) -> None:
    """Catch the shapes that render into something broken rather than erroring."""
    if not isinstance(data, dict):
        raise ValueError(f"SCENE_DATA must be a JSON object, got {type(data).__name__}")
    missing = [k for k in REQUIRED.get(template, []) if k not in data]
    if missing:
        raise ValueError(f"{template}: SCENE_DATA is missing required field(s): {', '.join(missing)}")
    if template == "curve_plot":
        return _validate_curve_plot(data)
    if template == "pipeline_flow":
        return _validate_pipeline_flow(data)
    for side in ("left", "right"):
        s = data.get(side, {})
        if not isinstance(s, dict) or not s.get("label"):
            raise ValueError(f"{template}: '{side}' needs a label")
        n = s.get("nodes", {})
        total, active = int(n.get("total", 0)), n.get("active", 0)
        if total < 1:
            raise ValueError(f"{template}: {side}.nodes.total must be at least 1")
        if total > 200:
            raise ValueError(f"{template}: {side}.nodes.total is {total}; over ~120 the dots are unreadable")
        count = len(active) if isinstance(active, list) else int(active)
        if count > total:
            raise ValueError(f"{template}: {side}.nodes.active ({count}) exceeds total ({total})")
        if n.get("arrangement") == "grid":
            rows, cols = int(n.get("rows", 0)), int(n.get("cols", 0))
            if rows * cols != total:
                raise ValueError(
                    f"{template}: {side}.nodes rows*cols ({rows}x{cols}={rows * cols}) "
                    f"must equal total ({total})")
        act = n.get("activation", "stagger")
        if act not in ("stagger", "sequential", "simultaneous"):
            raise ValueError(f"{template}: {side}.nodes.activation '{act}' must be "
                             "stagger, sequential or simultaneous")
        if "metric" in s and not isinstance(s["metric"].get("value", 0), (int, float)):
            raise ValueError(f"{template}: {side}.metric.value must be a number")


def _validate_pipeline_flow(data) -> None:
    stages = data.get("stages")
    if not isinstance(stages, list) or not 2 <= len(stages) <= 6:
        raise ValueError("pipeline_flow: needs 2-6 stages, got "
                         f"{len(stages) if isinstance(stages, list) else type(stages).__name__}"
                         " — one stage is not a process, seven will not fit the frame")
    for i, st in enumerate(stages):
        if not isinstance(st, dict) or not st.get("label"):
            raise ValueError(f"pipeline_flow: stages[{i}] needs a label")
        if len(st["label"]) > 20:
            raise ValueError(f"pipeline_flow: stages[{i}].label is {len(st['label'])} chars; "
                             "keep it under 20 or the box text shrinks to nothing")
    item = data.get("item")
    if not isinstance(item, dict):
        raise ValueError("pipeline_flow: `item` must be an object")
    labels = item.get("labels")
    if not isinstance(labels, list) or len(labels) != len(stages):
        raise ValueError(f"pipeline_flow: item.labels needs exactly one entry per stage "
                         f"({len(stages)}), got {len(labels) if isinstance(labels, list) else 0}")
    if not item.get("start") and not labels[0]:
        raise ValueError("pipeline_flow: item needs a `start` label, or a first entry in `labels`")
    # A process whose thing never changes is a row of boxes, not a lesson.
    forms = [item.get("start") or labels[0]] + [l for l in labels if l]
    if len(set(forms)) < 2:
        raise ValueError("pipeline_flow: the item is identical at every stage — nothing is "
                         "being transformed, so there is no process to show")


def _validate_curve_plot(data) -> None:
    dom = data.get("domain")
    if not (isinstance(dom, list) and len(dom) == 2 and all(isinstance(v, (int, float)) for v in dom)):
        raise ValueError("curve_plot: domain must be [min, max], two numbers")
    if dom[0] >= dom[1]:
        raise ValueError(f"curve_plot: domain {dom} must go low to high")
    curves = data.get("curves")
    if not isinstance(curves, list) or not 1 <= len(curves) <= 3:
        raise ValueError("curve_plot: needs 1-3 curves, got "
                         f"{len(curves) if isinstance(curves, list) else type(curves).__name__}")
    for i, c in enumerate(curves):
        terms = c.get("terms")
        if not isinstance(terms, list) or not terms:
            raise ValueError(f"curve_plot: curves[{i}] needs a non-empty `terms` list")
        for t in terms:
            kind = (t or {}).get("type")
            if kind not in CURVE_TERMS:
                raise ValueError(f"curve_plot: curves[{i}] has unknown term type {kind!r}; "
                                 f"use one of {', '.join(sorted(CURVE_TERMS))}")
    w = data.get("walker")
    if w is not None:
        if not isinstance(w, dict):
            raise ValueError("curve_plot: walker must be an object or omitted")
        if not (dom[0] <= float(w.get("start", 0)) <= dom[1]):
            raise ValueError(f"curve_plot: walker.start {w.get('start')} is outside domain {dom}")
        if float(w.get("rate", 0.1)) <= 0:
            raise ValueError("curve_plot: walker.rate must be positive")
        if w.get("direction", "min") not in ("min", "max"):
            raise ValueError("curve_plot: walker.direction must be 'min' or 'max'")
    # A flat line with nothing moving on it is not a lesson.
    if len(curves) == 1 and not w and all(t["type"] == "const" for t in curves[0]["terms"]):
        raise ValueError("curve_plot: a single constant curve with no walker shows nothing")


def author(concept: str, template: str, retries: int, args):
    guide = (ROOT / "references/scenedata_format_guide.md").read_text()
    _, data, how = authoring.author(
        concept, template, retries, args,
        guide=guide + "\n\nReply with ONE JSON object and nothing else — the SCENE_DATA "
                      "itself, with no wrapper key.",
        validate=validate, cache_dir=SCENE_DATA,
        ask=lambda c, t: f"Make a comparison animation for: {c}")
    return data, how


def media_marker(path: pathlib.Path) -> str:
    """The only markdown the desktop app turns into an inline video player.

    It streams the file over a custom Electron scheme with Range support, so it
    takes an absolute PATH, not an http URL — the opposite of the game preview,
    which needs loopback http and rejects file paths.
    """
    return f"[Watch: {path.name}](#media:{urllib.parse.quote(str(path), safe='')})"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--template", default="comparison_split")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--data", help="a .json file in scene_data/")
    g.add_argument("--author", metavar="CONCEPT",
                   help="generate SCENE_DATA live, retrying on invalid JSON, then falling back to cache")
    p.add_argument("--quality", default="h", choices=sorted(QUALITY),
                   help="l=480p15 m=720p30 h=1080p60 (default) p=1440p60 k=2160p60")
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--model"), p.add_argument("--base-url"), p.add_argument("--api-key")
    a = p.parse_args()

    template = resolve("template", a.template, TEMPLATES, ".py")

    if a.author:
        try:
            data, how = author(a.author, template.stem, max(0, a.retries), a)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        print(f"source: {how}", file=sys.stderr)
        slug = re.sub(r"[^a-z0-9]+", "_", a.author.lower()).strip("_")[:40] or "scene"
        data_path = pathlib.Path("/tmp") / f"scene_{slug}.json"
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        data_path = resolve("scene data", a.data, SCENE_DATA, ".json")
        try:
            validate(template.stem, json.loads(data_path.read_text()))
        except json.JSONDecodeError as e:
            print(f"invalid JSON at line {e.lineno} col {e.colno}: {e.msg}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        slug = data_path.stem

    scenes = scene_names(template)
    scene = scenes[0] if scenes else None
    if not scene:
        sys.exit(f"{template.name} defines no Scene subclass")

    env = {**os.environ, "SCENE_DATA_PATH": str(data_path)}
    started = time.time()
    MEDIA.mkdir(exist_ok=True)
    r = subprocess.run(["manim", f"-q{a.quality}", "--media_dir", str(MEDIA), str(template), scene],
                       capture_output=True, text=True, env=env)
    elapsed = time.time() - started

    if r.returncode != 0:
        print("\n".join((r.stderr or r.stdout).splitlines()[-30:]), file=sys.stderr)
        print(f"\nrender failed after {elapsed:.1f}s", file=sys.stderr)
        return r.returncode

    out = MEDIA / "videos" / template.stem / QUALITY[a.quality] / f"{scene}.mp4"
    if not out.exists():
        print(f"manim exited 0 but {out} is missing", file=sys.stderr)
        return 1

    # Rename per concept so a second render never overwrites the first — the
    # agent may hand back two animations in one session.
    final = out.with_name(f"{slug}.mp4")
    out.replace(final)
    final = final.resolve()

    print(media_marker(final))
    print(f"rendered in {elapsed:.1f}s -> {final} ({final.stat().st_size / 1024:.0f} KB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Render a JSON-driven Manim template and report what came out.

    render_scene.py --template comparison_split --data dense_vs_moe.json
    render_scene.py --template comparison_split --data dense_vs_moe.json --quality l

Sets SCENE_DATA_PATH, shells out to manim, and reports render time, output path,
file size and duration. Errors print manim's own message and exit non-zero.
"""
import argparse
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES, SCENE_DATA = ROOT / "templates", ROOT / "scene_data"

# manim.constants.QUALITIES — the skill's older copy of this map omits "p",
# so a -qp render died with a KeyError instead of rendering.
QUALITY = {"l": "480p15", "m": "720p30", "h": "1080p60", "p": "1440p60", "k": "2160p60"}


def resolve(kind: str, name: str, folder: pathlib.Path, suffix: str) -> pathlib.Path:
    """Accept 'comparison_split', 'comparison_split.py' or a full path."""
    for candidate in (pathlib.Path(name), folder / name, folder / f"{name}{suffix}"):
        if candidate.exists():
            return candidate.resolve()
    have = ", ".join(sorted(p.stem for p in folder.glob(f"*{suffix}")))
    sys.exit(f"no {kind} '{name}'. Available: {have}")


def scene_names(template: pathlib.Path) -> list[str]:
    return re.findall(r"^class (\w+)\(Scene\)", template.read_text(), re.M)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--template", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--quality", default="h", choices=sorted(QUALITY),
                   help="l=480p15 m=720p30 h=1080p60 (default) p=1440p60 k=2160p60")
    p.add_argument("--scene", help="scene class name; inferred from the template if omitted")
    a = p.parse_args()

    template = resolve("template", a.template, TEMPLATES, ".py")
    data = resolve("scene data", a.data, SCENE_DATA, ".json")

    scenes = scene_names(template)
    scene = a.scene or (scenes[0] if scenes else None)
    if not scene:
        sys.exit(f"{template.name} defines no Scene subclass")

    env = {**os.environ, "SCENE_DATA_PATH": str(data)}
    started = time.time()
    r = subprocess.run(["manim", f"-q{a.quality}", str(template), scene],
                       capture_output=True, text=True, env=env)
    elapsed = time.time() - started

    if r.returncode != 0:
        # manim puts the traceback on stderr; the tail is the part that says why.
        print("\n".join((r.stderr or r.stdout).splitlines()[-30:]), file=sys.stderr)
        print(f"\nrender failed after {elapsed:.1f}s", file=sys.stderr)
        return r.returncode

    out = pathlib.Path("media/videos") / template.stem / QUALITY[a.quality] / f"{scene}.mp4"
    if not out.exists():
        print(f"manim exited 0 but {out} is missing", file=sys.stderr)
        return 1

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
    print(f"{out}")
    print(f"  data      {data.name}")
    print(f"  quality   {QUALITY[a.quality]}")
    print(f"  render    {elapsed:.1f}s")
    print(f"  duration  {float(dur):.1f}s" if dur else "  duration  unknown")
    print(f"  size      {out.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

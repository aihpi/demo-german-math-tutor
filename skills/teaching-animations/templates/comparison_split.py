"""comparison_split — two things side by side, all content from JSON.

The engine is never edited to change the concept. Everything visible comes from
the SCENE_DATA file named by the SCENE_DATA_PATH environment variable:

    SCENE_DATA_PATH=scene_data/dense_vs_moe.json manim -qh comparison_split.py ComparisonSplit

Use scripts/render_scene.py rather than calling manim directly.
"""
import json
import os
import pathlib
import random
import re

from manim import *  # noqa: F403 — manim's own idiom, matches the repo's other scenes

# --------------------------------------------------------------------------- data
DEFAULTS = {
    "title": "",
    "left":  {"label": "", "color": "#FF4444",
              "nodes": {"total": 16, "active": 16, "arrangement": "grid",
                        "rows": 4, "cols": 4, "activation": "stagger"},
              "metric": {"label": "", "value": 0, "unit": "", "countUp": True, "duration": 3.0}},
    "right": {"label": "", "color": "#50C878",
              "nodes": {"total": 16, "active": 16, "arrangement": "grid",
                        "rows": 4, "cols": 4, "activation": "stagger"},
              "metric": {"label": "", "value": 0, "unit": "", "countUp": True, "duration": 3.0}},
    "comparison": {"show": True, "label": "", "highlightColor": "#FF7500"},
    "style": {"background": "#1a1a1a", "textColor": "#e0e0e0", "accent": "#FF7500",
              "font": "Helvetica", "dividerColor": "#444444", "inactiveColor": "#5A6B7C"},
    "timing": {"titleDuration": 1.5, "labelsDuration": 1.0, "animationDuration": 4.0,
               "comparisonDuration": 2.0, "endHold": 1.5},
    "seed": 7,
}


def _merge(base, over):
    """Deep-merge dicts; anything else replaces. Missing fields must never crash."""
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(base.get(k), dict) and isinstance(v, dict) else v
    return out


_path = os.environ.get("SCENE_DATA_PATH")
DATA = _merge(DEFAULTS, json.loads(pathlib.Path(_path).read_text()) if _path else {})

S, T = DATA["style"], DATA["timing"]
config.background_color = S["background"]

# Manim logs a warning and silently falls back on an unknown font, so the render
# succeeds looking wrong. Resolve once — font_list() hits fontconfig.
FONT = {"font": S["font"]} if S["font"] in Text.font_list() else {}

# --------------------------------------------------------------------------- layout
HALF_X = 3.55          # centre of each half
NODE_W, NODE_H = 6.3, 2.9
Y_LABEL, Y_NODES, Y_METRIC, Y_UNIT, Y_COMPARE = 2.25, 0.30, -1.95, -2.62, -3.50


def fit(mob, width):
    """Labels come from JSON and can be any length. Never let one cross the divider."""
    return mob.scale(width / mob.width) if mob.width > width else mob


def grid_positions(spec, cx):
    """One formula for both arrangements, so a 1x9 row and a 4x4 grid read as the
    same kind of object (their radii land within ~4% of each other)."""
    rows, cols = int(spec.get("rows") or 1), int(spec.get("cols") or 1)
    if spec.get("arrangement") == "row":
        rows, cols = 1, int(spec.get("total", cols))
    total = int(spec.get("total", rows * cols))
    pitch = min(NODE_W / max(cols, 1), NODE_H / max(rows, 1), 0.95)
    pts = []
    for i in range(total):
        r, c = divmod(i, cols)
        pts.append(np.array([cx + (c - (cols - 1) / 2) * pitch,
                             Y_NODES + ((rows - 1) / 2 - r) * pitch, 0.0]))
    return pts, pitch * 0.40


def active_indices(spec):
    """`active` is a count (first N) or an explicit index list."""
    a = spec.get("active", 0)
    total = int(spec.get("total", 0))
    return [i for i in a if 0 <= i < total] if isinstance(a, list) else list(range(min(int(a), total)))


# ----------------------------------------------------------------------- animation
LAG = {"stagger": 0.14, "sequential": 1.0, "simultaneous": 0.0}
# A lag_ratio=0 group stretched over the whole window is one sluggish swell; let
# `simultaneous` finish early and hold, so the counters stay the moving thing.
BUSY = {"stagger": 1.0, "sequential": 1.0, "simultaneous": 0.55}


def pulse(node, colour, glow):
    """Dim -> overshoot -> settle visibly ON.

    Two explicit Transform targets, not chained `.animate` (both targets would be
    computed from the same pre-play state, so the second is wrong) and not
    Indicate (that is there_and_back — it ends dim, which is the opposite of
    'this expert fired')."""
    on = node.copy().set_opacity(1.0).set_fill(colour, 1.0).set_stroke(colour, 4.0)
    return Succession(
        Transform(node, on.copy().scale(glow), rate_func=rate_functions.ease_out_cubic, run_time=0.55),
        Transform(node, on, rate_func=rate_functions.ease_in_out_sine, run_time=0.45),
    )


def side_animation(nodes, spec, colour, rng):
    """Whatever the pattern and node count, this fills exactly the play's run_time:
    AnimationGroup rescales its internal timeline to the run_time it is given."""
    pattern = spec.get("activation", "stagger")
    order = active_indices(spec)
    if pattern == "stagger":
        rng.shuffle(order)                      # organic: not a left-to-right sweep
    anims = [pulse(nodes[i], colour, 1.25 + rng.random() * 0.20) for i in order]
    if not anims:                               # active: 0 — LaggedStart would raise
        return Wait(run_time=0.01)
    body = LaggedStart(*anims, lag_ratio=LAG.get(pattern, 0.14))
    busy = BUSY.get(pattern, 1.0)
    return body if busy >= 1.0 else Succession(body, Wait(run_time=(1 / busy - 1)))


def ratio_text(label, left, right):
    """{ratio} -> '9.9x' from 31.6/3.2, '6x' from 6/1. Never divides by zero."""
    a, b = abs(float(left)), abs(float(right))
    lo, hi = min(a, b), max(a, b)
    r = "" if lo == 0 else f"{hi / lo:.1f}".removesuffix(".0")
    return label.replace("{ratio}", r)


class ComparisonSplit(Scene):
    def hold_until(self, t):
        """Absolute marks from JSON, but manim only takes durations. Reading the
        renderer clock self-corrects, so one long run_time cannot cascade."""
        dt = t - self.renderer.time
        if dt > 1e-3:
            self.wait(dt)

    def construct(self):
        rng = random.Random(DATA.get("seed", 7))
        text = S["textColor"]

        # -- title -------------------------------------------------------------
        title = fit(Text(DATA["title"], **FONT, font_size=42, color=text), 12.0)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.9)
        self.play(title.animate.move_to(UP * 3.45), run_time=T["titleDuration"] - 0.9)

        # -- divider -----------------------------------------------------------
        # Create follows point order: start UP so it draws downward.
        divider = Line(UP * 2.90, DOWN * 2.85, stroke_width=2, color=S["dividerColor"])
        self.play(Create(divider), run_time=0.5)

        # -- labels, nodes, counters -------------------------------------------
        sides, trackers, opacity = [], [], []
        for key, cx in (("left", -HALF_X), ("right", HALF_X)):
            d = DATA[key]
            colour = d["color"]
            label = fit(Text(d["label"], **FONT, font_size=32, color=colour), NODE_W).move_to([cx, Y_LABEL, 0])

            pts, radius = grid_positions(d["nodes"], cx)
            nodes = VGroup(*[
                Circle(radius=radius, stroke_width=2, color=S["inactiveColor"],
                       fill_color=S["inactiveColor"], fill_opacity=1.0)
                .move_to(p).set_opacity(0.20)   # one call so stroke and fill dim together
                for p in pts])

            m = d["metric"]
            tracker = ValueTracker(0.0 if m.get("countUp", True) else float(m["value"]))
            fade = ValueTracker(0.0)
            places = 0 if float(m["value"]) == int(float(m["value"])) else 1
            number = always_redraw(lambda t=tracker, f=fade, c=colour, p=places, u=m["unit"], x=cx: fit(
                Text(f"{t.get_value():.{p}f}{u}", **FONT, font_size=54, color=c), NODE_W)
                .move_to([x, Y_METRIC, 0]).set_opacity(f.get_value()))
            caption = Text(m["label"], **FONT, font_size=22, color=text).set_opacity(0.6).move_to([cx, Y_UNIT, 0])

            self.add(number)                    # updaters only run while in the scene
            sides.append((label, nodes, caption, m, d, colour))
            trackers.append(tracker)
            opacity.append(fade)

        self.hold_until(T["titleDuration"] + T["labelsDuration"] - 0.5)
        self.play(
            *[FadeIn(s[0], shift=UP * 0.2) for s in sides],
            *[FadeIn(s[2]) for s in sides],
            *[f.animate.set_value(1.0) for f in opacity],
            *[LaggedStart(*[FadeIn(n) for n in s[1]], lag_ratio=0.04) for s in sides],
            run_time=T["labelsDuration"],
        )

        # -- both sides fire together ------------------------------------------
        window = T["animationDuration"]
        counts = []
        for (label, nodes, caption, m, d, colour), tracker in zip(sides, trackers):
            counts.append(
                tracker.animate(rate_func=rate_functions.ease_out_cubic).set_value(float(m["value"]))
                if m.get("countUp", True) else Wait(run_time=0.01))
        self.play(
            *[side_animation(s[1], s[4]["nodes"], s[5], rng) for s in sides],
            *counts, run_time=window,
        )
        # Stop re-rendering two Pango Texts 90 times during the hold.
        for mob in self.mobjects:
            if mob.get_updaters():
                mob.clear_updaters()

        # -- comparison ---------------------------------------------------------
        if DATA["comparison"].get("show", True) and DATA["comparison"].get("label"):
            line = ratio_text(DATA["comparison"]["label"],
                              DATA["left"]["metric"]["value"], DATA["right"]["metric"]["value"])
            comp = fit(Text(line, **FONT, font_size=36, color=DATA["comparison"]["highlightColor"]), 13.0)
            comp.move_to([0, Y_COMPARE, 0])
            self.play(FadeIn(comp, shift=UP * 0.25, scale=1.06), run_time=min(1.0, T["comparisonDuration"]))
            self.wait(max(0.0, T["comparisonDuration"] - 1.0))

        self.wait(T["endHold"])

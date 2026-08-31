"""curve_plot — one or two declared curves on shared axes, all content from JSON.

Two shapes from one engine:
  - a walker: one curve plus a marker that steps downhill (or up), for descent,
    convergence and divergence
  - two curves: lines that cross or diverge, for train-vs-validation, bias vs
    variance, scaling laws

Content comes from the SCENE_DATA file named by SCENE_DATA_PATH. Curves are
declared as terms, never as formulas, so the derivative the walker follows is
exact and nothing has to eval a string.
"""
import json
import os
import pathlib
import random

from manim import *  # noqa: F403 — manim's own idiom, matches the repo's other scenes

DEFAULTS = {
    "title": "",
    "domain": [0, 10],
    "axes": {"x": "", "y": ""},
    "curves": [],          # [{label, color, terms:[...], dashed?}]
    "walker": None,        # {start, rate, steps, direction, color, label}
    "callout": {"show": True, "label": "", "at": None, "highlightColor": "#FF7500"},
    "style": {"background": "#1a1a1a", "textColor": "#e0e0e0", "accent": "#FF7500",
              "font": "Helvetica", "axisColor": "#4a4a4a", "gridColor": "#2a2a2a"},
    "timing": {"titleDuration": 1.5, "axesDuration": 1.0, "curveDuration": 2.0,
               "walkDuration": 3.5, "calloutDuration": 2.0, "endHold": 1.5},
    "seed": 7,
}


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(base.get(k), dict) and isinstance(v, dict) else v
    return out


_path = os.environ.get("SCENE_DATA_PATH")
DATA = _merge(DEFAULTS, json.loads(pathlib.Path(_path).read_text()) if _path else {})

S, T = DATA["style"], DATA["timing"]
config.background_color = S["background"]
# Manim raises on any run_time or wait of 0, and a JSON-authored timing block can
# hold a zero for any phase. Floor them once here rather than at ten call sites.
T = {k: (max(0.1, float(v)) if isinstance(v, (int, float)) else v) for k, v in T.items()}

FONT = {"font": S["font"]} if S["font"] in Text.font_list() else {}

# Same term vocabulary as parameter_control's landscape and base.js's TG.curve,
# so an author who has read one format guide already knows this one.
TERM = {
    "const": lambda t, x: t["c"],
    "lin":   lambda t, x: t["m"] * x,
    "quad":  lambda t, x: t["a"] * x * x,
    "sin":   lambda t, x: t["amp"] * np.sin(t["freq"] * x + t.get("phase", 0)),
    "cos":   lambda t, x: t["amp"] * np.cos(t["freq"] * x + t.get("phase", 0)),
    "exp":   lambda t, x: t["amp"] * np.exp(t["rate"] * x),
    "inv":   lambda t, x: t["a"] / (x + t.get("shift", 1)),
}
DTERM = {
    "const": lambda t, x: 0.0,
    "lin":   lambda t, x: t["m"],
    "quad":  lambda t, x: 2 * t["a"] * x,
    "sin":   lambda t, x: t["amp"] * t["freq"] * np.cos(t["freq"] * x + t.get("phase", 0)),
    "cos":   lambda t, x: -t["amp"] * t["freq"] * np.sin(t["freq"] * x + t.get("phase", 0)),
    "exp":   lambda t, x: t["amp"] * t["rate"] * np.exp(t["rate"] * x),
    "inv":   lambda t, x: -t["a"] / (x + t.get("shift", 1)) ** 2,
}
bad = {t["type"] for c in DATA["curves"] for t in c.get("terms", []) if t["type"] not in TERM}
if bad:
    raise ValueError("unknown curve term type(s): " + ", ".join(sorted(bad)))


def evaluate(terms):
    """(f, df) for a term list — the derivative is analytic, never a difference."""
    return (lambda x: sum(TERM[t["type"]](t, x) for t in terms),
            lambda x: sum(DTERM[t["type"]](t, x) for t in terms))


def fit(mob, width):
    return mob.scale(width / mob.width) if mob.width > width else mob


class CurvePlot(Scene):
    def pause(self, seconds):
        """Manim raises on wait(0), and a JSON-authored timing block may hold a
        zero for any phase. Skip instead of crashing."""
        if seconds and seconds > 1e-3:
            self.wait(seconds)

    def hold_until(self, t):
        dt = t - self.renderer.time
        if dt > 1e-3:
            self.wait(dt)

    def construct(self):
        rng = random.Random(DATA.get("seed", 7))
        curves = DATA["curves"]
        if not curves:
            raise ValueError("curve_plot needs at least one entry in `curves`")
        x0, x1 = DATA["domain"]
        fns = [evaluate(c["terms"]) for c in curves]

        # Y range from the curves themselves, so an author never sets it by hand.
        samples = [f(x0 + (x1 - x0) * i / 200) for f, _ in fns for i in range(201)]
        lo, hi = float(min(samples)), float(max(samples))
        pad = (hi - lo) * 0.15 or 1.0
        y0, y1 = lo - pad, hi + pad

        # -- title -------------------------------------------------------------
        title = fit(Text(DATA["title"], **FONT, font_size=42, color=S["textColor"]), 12.0)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.9)
        self.play(title.animate.move_to(UP * 3.4), run_time=max(0.1, T["titleDuration"] - 0.9))

        # -- axes --------------------------------------------------------------
        ax = Axes(x_range=[x0, x1, (x1 - x0) / 5], y_range=[y0, y1, (y1 - y0) / 4],
                  x_length=10.4, y_length=4.6,
                  axis_config={"color": S["axisColor"], "stroke_width": 2,
                               "include_ticks": True, "include_tip": False},
                  tips=False).move_to(DOWN * 0.05)
        labels = VGroup(
            Text(DATA["axes"].get("x", ""), **FONT, font_size=22, color=S["textColor"]).set_opacity(.7)
                .next_to(ax, DOWN, buff=0.22),
            Text(DATA["axes"].get("y", ""), **FONT, font_size=22, color=S["textColor"]).set_opacity(.7)
                .rotate(PI / 2).next_to(ax, LEFT, buff=0.28))
        self.play(Create(ax), FadeIn(labels), run_time=T["axesDuration"])

        # -- curves ------------------------------------------------------------
        drawn, legend = [], VGroup()
        for i, (c, (f, _)) in enumerate(zip(curves, fns)):
            g = ax.plot(f, x_range=[x0, x1], color=c.get("color", S["accent"]), stroke_width=4)
            if c.get("dashed"):
                g = DashedVMobject(g, num_dashes=42)
            drawn.append(g)
            if c.get("label"):
                tag = Text(c["label"], **FONT, font_size=24, color=c.get("color", S["accent"]))
                legend.add(tag)
        if len(legend):
            legend.arrange(DOWN, aligned_edge=LEFT, buff=0.22).to_corner(UR, buff=0.55).shift(DOWN * 0.5)
        self.play(*[Create(g) for g in drawn], FadeIn(legend),
                  run_time=T["curveDuration"], lag_ratio=0.15)

        # -- walker ------------------------------------------------------------
        w = DATA.get("walker")
        if w:
            f, df = fns[0]
            sign = -1.0 if w.get("direction") == "max" else 1.0
            x = float(w.get("start", (x0 + x1) / 2))
            rate = float(w.get("rate", 0.1))
            steps = int(w.get("steps", 12))
            colour = w.get("color", S["accent"])

            dot = Dot(ax.c2p(x, f(x)), radius=0.13, color=colour, z_index=4)
            trail = VGroup()
            self.play(FadeIn(dot, scale=1.6), run_time=0.35)

            # One mark per visited point, NOT a chord along the curve. A chord
            # just re-colours the curve and hides the step structure — and the
            # step structure is the lesson: long strides while the gradient is
            # steep, then a visible pile-up as it flattens.
            per = max(0.05, T["walkDuration"] / max(1, steps))
            for _ in range(steps):
                trail.add(Dot(ax.c2p(x, f(x)), radius=0.075, color=colour,
                              z_index=3).set_opacity(0.55))
                nx = x - sign * rate * float(df(x))
                nx = min(max(nx, x0), x1)          # a diverging walker stops at the edge
                self.play(FadeIn(trail[-1], scale=1.4),
                          dot.animate.move_to(ax.c2p(nx, f(nx))),
                          run_time=per, rate_func=rate_functions.ease_in_out_sine)
                x = nx
                if abs(float(df(x))) < 1e-3:       # settled: stop early, hold the rest
                    break
            self.pause(max(0.0, T["walkDuration"] - per * len(trail)))

        # -- callout -----------------------------------------------------------
        co = DATA["callout"]
        if co.get("show") and co.get("label"):
            text = fit(Text(co["label"], **FONT, font_size=32,
                            color=co.get("highlightColor", S["accent"])), 12.0)
            at = co.get("at")
            if at is None:
                text.to_edge(DOWN, buff=0.28)
            else:
                f, _ = fns[0]
                text.move_to(ax.c2p(float(at), f(float(at))) + UP * 0.75)
            self.play(FadeIn(text, shift=UP * 0.25, scale=1.05),
                      run_time=min(1.0, T["calloutDuration"]))
            self.pause(max(0.0, T["calloutDuration"] - 1.0))

        self.pause(T["endHold"])

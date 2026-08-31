"""pipeline_flow — one thing travelling through named stages, transforming as it goes.

For processes: tokenise → embed → attend → predict, a RAG lookup, a training
loop, the water cycle. The lesson is the *sequence* and what changes at each
step, which neither comparison_split (counts) nor curve_plot (shapes) can show.

Set `loop: true` and the last stage arrows back to the first — that is the whole
difference between a pipeline and a cycle.

Content comes from the SCENE_DATA file named by SCENE_DATA_PATH.
"""
import json
import os
import pathlib

from manim import *  # noqa: F403 — manim's own idiom, matches the repo's other scenes

DEFAULTS = {
    "title": "",
    "stages": [],                       # [{label, color, note?}]
    "item": {"start": "", "labels": [], "color": "#FF7500"},
    "loop": False,
    "loopLabel": "",
    "callout": {"show": True, "label": "", "highlightColor": "#FF7500"},
    "style": {"background": "#1a1a1a", "textColor": "#e0e0e0", "accent": "#FF7500",
              "font": "Helvetica", "boxColor": "#3a3e46", "arrowColor": "#5A6B7C"},
    "timing": {"titleDuration": 1.5, "stagesDuration": 1.5, "perStage": 1.3,
               "loopDuration": 1.5, "calloutDuration": 2.0, "endHold": 1.5},
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

# One vertical budget for the whole frame (y from -4 to 4), so nothing collides:
Y_STAGES = 0.60          # stage boxes, 1.5 tall -> 1.35 .. -0.15
Y_NOTE = -0.72           # per-stage caption, under its box
Y_ITEM = -1.55           # the travelling item, 0.72 tall -> -1.19 .. -1.91
Y_LOOP_LABEL = -2.18     # above the arc, below the item lane
Y_LOOP = -2.50           # arc endpoints; it bows further down from here
Y_CALLOUT = -3.50


def fit(mob, width):
    return mob.scale(width / mob.width) if mob.width > width else mob


class PipelineFlow(Scene):
    def pause(self, seconds):
        if seconds and seconds > 1e-3:
            self.wait(seconds)

    def construct(self):
        stages = DATA["stages"]
        if not stages:
            raise ValueError("pipeline_flow needs at least one entry in `stages`")
        item = DATA["item"]
        labels = list(item.get("labels") or [])
        icolour = item.get("color", S["accent"])

        # -- title -------------------------------------------------------------
        title = fit(Text(DATA["title"], **FONT, font_size=42, color=S["textColor"]), 12.0)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=0.9)
        self.play(title.animate.move_to(UP * 3.4), run_time=max(0.1, T["titleDuration"] - 0.9))

        # -- stage boxes -------------------------------------------------------
        # One pitch for any count, so 3 stages and 6 stages both fill the frame
        # and the text inside shrinks rather than overflowing.
        n = len(stages)
        span, gap = 13.0, 0.5
        w = min(3.0, (span - gap * (n - 1)) / n)
        pitch = w + gap
        boxes, captions = VGroup(), VGroup()
        for i, st in enumerate(stages):
            cx = (i - (n - 1) / 2) * pitch
            box = RoundedRectangle(width=w, height=1.5, corner_radius=0.14,
                                   stroke_color=S["boxColor"], stroke_width=2,
                                   fill_color=st.get("color", S["accent"]), fill_opacity=0.10)
            box.move_to([cx, Y_STAGES, 0])
            tag = fit(Text(st["label"], **FONT, font_size=24,
                           color=st.get("color", S["accent"])), w - 0.25).move_to(box)
            boxes.add(VGroup(box, tag))
            if st.get("note"):
                captions.add(fit(Text(st["note"], **FONT, font_size=17,
                                      color=S["textColor"]), w + 0.2)
                             .set_opacity(0.55).move_to([cx, Y_NOTE, 0]))

        arrows = VGroup(*[
            Arrow(boxes[i][0].get_right(), boxes[i + 1][0].get_left(),
                  buff=0.06, stroke_width=3, max_tip_length_to_length_ratio=0.22,
                  color=S["arrowColor"])
            for i in range(n - 1)])

        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.2) for b in boxes], lag_ratio=0.18),
                  run_time=T["stagesDuration"])
        if len(arrows):
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2), run_time=0.7)
        if len(captions):
            self.play(FadeIn(captions), run_time=0.5)

        # -- the item travels --------------------------------------------------
        start_text = item.get("start") or (labels[0] if labels else "")
        chip = self._chip(start_text, icolour, boxes[0][0].get_center()[0])
        self.play(FadeIn(chip, scale=1.3), run_time=0.45)

        for i, st in enumerate(stages):
            cx = boxes[i][0].get_center()[0]
            box = boxes[i][0]
            lit = box.copy().set_fill(st.get("color", S["accent"]), 0.30).set_stroke(
                st.get("color", S["accent"]), 3)
            # Slide under the stage, light the stage, then become what it is now.
            self.play(chip.animate.move_to([cx, Y_ITEM, 0]),
                      Transform(box, lit),
                      run_time=T["perStage"] * 0.55,
                      rate_func=rate_functions.ease_in_out_sine)
            if i < len(labels) and labels[i] and labels[i] != start_text:
                new = self._chip(labels[i], icolour, cx)
                self.play(Transform(chip, new), run_time=T["perStage"] * 0.45)
                start_text = labels[i]
            else:
                self.pause(T["perStage"] * 0.45)

        # -- the loop back -----------------------------------------------------
        if DATA.get("loop") and n > 1:
            # Anchored below the item lane and bowed DOWNWARD (negative angle).
            # A positive angle arcs the other way and cuts straight through the
            # stage boxes, which is what the first version did. The angle is
            # shallow on purpose: sagitta is (chord/2)*tan(angle/4), so -PI/3.2
            # over a 10-unit chord dipped 1.3 units and crossed the callout.
            last_x = boxes[-1][0].get_center()[0]
            first_x = boxes[0][0].get_center()[0]
            back = CurvedArrow([last_x, Y_LOOP, 0], [first_x, Y_LOOP, 0],
                               angle=-PI / 9, stroke_width=3, color=S["accent"])
            bits = [Create(back), chip.animate.move_to([first_x, Y_ITEM, 0])]
            if DATA.get("loopLabel"):
                tag = fit(Text(DATA["loopLabel"], **FONT, font_size=20, color=S["accent"]), 11.0)
                tag.set_opacity(0.85).move_to([0, Y_LOOP_LABEL, 0])
                bits.append(FadeIn(tag))
            self.play(*bits, run_time=T["loopDuration"])

        # -- callout -----------------------------------------------------------
        co = DATA["callout"]
        if co.get("show") and co.get("label"):
            text = fit(Text(co["label"], **FONT, font_size=32,
                            color=co.get("highlightColor", S["accent"])), 13.0)
            text.move_to([0, Y_CALLOUT, 0])
            self.play(FadeIn(text, shift=UP * 0.25, scale=1.05),
                      run_time=min(1.0, T["calloutDuration"]))
            self.pause(T["calloutDuration"] - 1.0)

        self.pause(T["endHold"])

    def _chip(self, text, colour, cx):
        """The travelling item: a rounded label that keeps its size as text changes."""
        label = fit(Text(text, **FONT, font_size=24, color="#1a1a1a"), 3.4)
        pill = RoundedRectangle(width=label.width + 0.5, height=0.72, corner_radius=0.36,
                                stroke_width=0, fill_color=colour, fill_opacity=1.0)
        return VGroup(pill, label).move_to([cx, Y_ITEM, 0])

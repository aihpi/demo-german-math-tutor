from manim import *

config.background_color = BLACK

FONT = "Helvetica"
ACCENT = "#FF7500"        # HPI orange — active / attended
ACCENT2 = "#FF9940"       # secondary emphasis
INACTIVE = "#5A6B7C"      # muted blue-grey

TOKENS = ["The", "cat", "sat", "on", "mat"]
QUERY = 1                 # "cat" is the query we follow
# rows = query token, cols = key token; each row sums to ~1
W = [
    [0.70, 0.10, 0.10, 0.05, 0.05],
    [0.05, 0.35, 0.30, 0.05, 0.25],   # cat -> sat, mat
    [0.05, 0.30, 0.40, 0.15, 0.10],
    [0.10, 0.10, 0.30, 0.30, 0.20],
    [0.05, 0.20, 0.15, 0.10, 0.50],
]
CELL = 0.72


class SelfAttentionScene(Scene):
    def construct(self):
        title = Text("Self-Attention", font=FONT, font_size=42,
                     color=WHITE).move_to(UP * 3.5)

        # --- token row, y = +2.5 -------------------------------------------
        boxes = VGroup()
        for tok in TOKENS:
            label = Text(tok, font=FONT, font_size=28, color=WHITE)
            box = RoundedRectangle(width=1.5, height=0.8, corner_radius=0.12,
                                   color=INACTIVE, stroke_width=3)
            boxes.add(VGroup(box, label))
        boxes.arrange(RIGHT, buff=0.55).move_to(UP * 2.5)

        self.play(LaggedStart(*[FadeIn(b, shift=DOWN * 0.2) for b in boxes],
                              lag_ratio=0.15), run_time=1.2)
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.6)

        # --- query token lights up ----------------------------------------
        self.play(boxes[QUERY][0].animate.set_color(ACCENT).set_stroke(width=5),
                  boxes[QUERY][1].animate.set_color(ACCENT), run_time=0.6)

        # --- attention arcs: thickness proportional to weight -------------
        arcs = VGroup()
        for j, w in enumerate(W[QUERY]):
            if j == QUERY:
                continue
            strong = w >= 0.2
            arc = ArcBetweenPoints(
                boxes[QUERY][0].get_bottom() + DOWN * 0.02,
                boxes[j][0].get_bottom() + DOWN * 0.02,
                angle=TAU / 5 if j > QUERY else -TAU / 5,
                color=ACCENT if strong else INACTIVE,
                stroke_width=1.5 + 14 * w,
                stroke_opacity=1.0 if strong else 0.5,
            )
            arcs.add(arc)
        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.18),
                  run_time=1.5)

        # --- heatmap, centered y = -1.1 -----------------------------------
        grid = VGroup()
        for i, row in enumerate(W):
            for j, w in enumerate(row):
                grid.add(Square(
                    side_length=CELL, stroke_width=1.5, stroke_color=INACTIVE,
                    fill_color=ACCENT, fill_opacity=0.10 + 0.90 * w,
                ).move_to(RIGHT * j * CELL + DOWN * i * CELL))
        grid.move_to(DOWN * 1.1)

        col_labels = VGroup(*[
            Text(t, font=FONT, font_size=22, color=WHITE)
            .move_to(grid[j].get_center()).next_to(grid[j], UP, buff=0.18)
            for j, t in enumerate(TOKENS)
        ])
        row_labels = VGroup(*[
            Text(t, font=FONT, font_size=22, color=WHITE)
            .next_to(grid[i * 5], LEFT, buff=0.25)
            for i, t in enumerate(TOKENS)
        ])
        block = VGroup(grid, col_labels, row_labels)
        block.move_to(DOWN * 1.0)
        self.play(FadeIn(col_labels), FadeIn(row_labels), run_time=0.7)
        self.play(LaggedStart(*[
            LaggedStart(*[FadeIn(grid[i * 5 + j], scale=0.6) for j in range(5)],
                        lag_ratio=0.08)
            for i in range(5)], lag_ratio=0.22), run_time=2.4)

        # --- highlight the "cat" row --------------------------------------
        band = SurroundingRectangle(
            VGroup(*[grid[QUERY * 5 + j] for j in range(5)]),
            color=ACCENT, buff=0.06, stroke_width=4)
        self.play(Create(band), row_labels[QUERY].animate.set_color(ACCENT),
                  run_time=0.8)

        note = Text('"cat" attends most strongly to "sat" and "mat"',
                    font=FONT, font_size=32, color=ACCENT).move_to(DOWN * 3.5)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.9)
        self.wait(2.0)

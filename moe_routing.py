from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer

config.background_color = BLACK

# ManimML emits empty AnimationGroup()s in its forward pass; manim 0.21 rejects
# those. Fill them with a no-op Wait.
# ponytail: monkeypatch, drop it when manim-ml supports manim >= 0.19
_ag_init = AnimationGroup.__init__
AnimationGroup.__init__ = lambda self, *a, **kw: _ag_init(
    self, *(a or (Wait(run_time=0.01),)), **kw
)

ACTIVE = "#76B900"
INACTIVE = "#5A6B7C"
SELECTED = (2, 5)  # experts the gate routes to


def expert(i):
    c = ACTIVE if i in SELECTED else INACTIVE
    net = NeuralNetwork(
        [FeedForwardLayer(3, node_color=c, node_outline_color=c, rectangle_color=c),
         FeedForwardLayer(2, node_color=c, node_outline_color=c, rectangle_color=c)],
        layer_spacing=0.3,
    )
    net.scale(0.8)
    label = Text(f"E{i}", font_size=22, color=c).next_to(net, DOWN, buff=0.15)
    return Group(net, label), net


class MoERoutingScene(Scene):
    def construct(self):
        built = [expert(i) for i in range(8)]
        nets = [n for _, n in built]
        experts = Group(*[g for g, _ in built]).arrange(RIGHT, buff=0.32)
        experts.set(width=12.4).move_to(DOWN * 0.4).set_opacity(0.28)

        token = Text('"the"', font_size=44, color=WHITE).move_to(UP * 3.2)
        gate = VGroup(
            RoundedRectangle(width=3.0, height=0.85, corner_radius=0.14,
                             color=WHITE, stroke_width=2),
            Text("Gating Network", font_size=24, color=WHITE),
        ).move_to(UP * 1.9)

        self.play(FadeIn(experts, shift=UP * 0.2), run_time=1.2)
        self.play(Write(token), run_time=0.7)
        self.play(FadeIn(gate, shift=DOWN * 0.2), run_time=0.7)
        self.play(GrowArrow(Arrow(token.get_bottom(), gate[0].get_top(),
                                  buff=0.1, color=WHITE)), run_time=0.5)

        # route: gate -> the 2 chosen experts
        routes = VGroup(*[
            Arrow(gate[0].get_bottom(), experts[i].get_top(), buff=0.12,
                  color=ACTIVE, stroke_width=5)
            for i in SELECTED
        ])
        self.play(
            *[Create(r) for r in routes],
            *[experts[i].animate.set_opacity(1.0) for i in SELECTED],
            run_time=1.3,
        )
        self.wait(0.3)

        # forward pass through the 2 selected experts only
        self.play(*[nets[i].make_forward_pass_animation(run_time=2.4)
                    for i in SELECTED], run_time=2.4)

        # merge the two outputs back into one representation
        merged = Circle(radius=0.32, color=ACTIVE, fill_opacity=0.9).move_to(DOWN * 2.4)
        out = Text("output", font_size=24, color=WHITE).next_to(merged, RIGHT, buff=0.3)
        merge_lines = VGroup(*[
            Line(experts[i].get_bottom(), merged.get_center(),
                 color=ACTIVE, stroke_width=4)
            for i in SELECTED
        ])
        self.play(Create(merge_lines), run_time=0.9)
        self.play(GrowFromCenter(merged), FadeIn(out), run_time=0.6)

        note = Text("2 of 8 experts active = 10x less compute",
                    font_size=32, color=ACTIVE).move_to(DOWN * 3.4)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.9)
        self.wait(2.0)

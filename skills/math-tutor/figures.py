#!/usr/bin/env python3
"""Draw a geometry figure as an animated SVG.

The model chooses the shape and the numbers; this module does the geometry, so
a figure is never wrong on stage. Animation is plain CSS inside the SVG, which
Chromium runs even inside an <img> — the lines draw themselves, no video.

    python3 figures.py triangle  --sides 8 8 16 --caption "kein Dreieck"
    python3 figures.py circle     --radius 3 --caption "r = 3"
    python3 figures.py rectangle  --size 8 5 --caption "8 x 5"

Covers the three shapes that dominate diagram-free MATH geometry (triangle 27%,
circle 31%, rectangle/square 8%). Anything else runs without a figure — no
picture beats a wrong picture.
"""
import argparse
import math
import sys

U, PAD, W, H = 19, 26, 372, 150
GREEN, RED, GREY = "#22c55e", "#ef4444", "#94a3b8"


def triangle(a: float, b: float, c: float, caption: str = "", colour: str = GREEN,
             draw_ms: int = 1100) -> str:
    """Two sides `a` and `b` closing on a base of length `c`.

    Degenerate when a + b == c: the apex sits on the base and it reads as a
    line, which is the whole point of the triangle-inequality problem.
    """
    if a + b < c:
        sys.exit(f"{a} + {b} < {c}: no such triangle, not even a degenerate one")
    # Apex from the base-left corner: x by the law of cosines, y by Pythagoras.
    x = (c * c + a * a - b * b) / (2 * c)
    y = math.sqrt(max(a * a - x * x, 0))
    bx, by = PAD, H - 46
    ax, ay = bx + x * U, by - y * U
    ex = bx + c * U
    sides = math.hypot(ax - bx, ay - by) + math.hypot(ex - ax, by - ay)

    return (
      f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
      f'<style>'
      f'.s{{stroke-dasharray:{sides:.0f};stroke-dashoffset:{sides:.0f};'
      f'animation:d {draw_ms}ms ease-out forwards}}'
      f'.b{{stroke-dasharray:{c*U:.0f};stroke-dashoffset:{c*U:.0f};'
      f'animation:d {draw_ms}ms ease-out {draw_ms}ms forwards}}'
      f'.f{{opacity:0;animation:f 400ms ease-out {draw_ms*2}ms forwards}}'
      f'@keyframes d{{to{{stroke-dashoffset:0}}}}@keyframes f{{to{{opacity:1}}}}'
      f'</style>'
      f'<g fill="none" stroke="{colour}" stroke-width="3" stroke-linecap="round">'
      f'<path class="s" d="M{bx:.1f} {by:.1f} L{ax:.1f} {ay:.1f} L{ex:.1f} {by:.1f}"/>'
      f'<path class="b" d="M{bx:.1f} {by:.1f} L{ex:.1f} {by:.1f}"/></g>'
      f'<g class="f" font-family="ui-sans-serif,system-ui,sans-serif" font-size="15" fill="#64748b">'
      f'<text x="{(bx+ax)/2-16:.1f}" y="{(by+ay)/2-6:.1f}">{a:g}</text>'
      f'<text x="{(ax+ex)/2+8:.1f}" y="{(by+ay)/2-6:.1f}">{b:g}</text>'
      f'<text x="{(bx+ex)/2-8:.1f}" y="{by+22:.1f}">{c:g}</text></g>'
      f'<text class="f" x="{PAD}" y="{H-8}" fill="{colour}" font-size="14" font-weight="600" '
      f'font-family="ui-sans-serif,system-ui,sans-serif">{caption}</text></svg>')


def _frame(body: str, caption: str, colour: str, length: float, draw_ms: int) -> str:
    return (
      f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
      f'<style>'
      f'.s{{stroke-dasharray:{length:.0f};stroke-dashoffset:{length:.0f};'
      f'animation:d {draw_ms}ms ease-out forwards}}'
      f'.f{{opacity:0;animation:f 400ms ease-out {draw_ms}ms forwards}}'
      f'@keyframes d{{to{{stroke-dashoffset:0}}}}@keyframes f{{to{{opacity:1}}}}'
      f'</style>{body}'
      f'<text class="f" x="{PAD}" y="{H-8}" fill="{colour}" font-size="14" font-weight="600" '
      f'font-family="ui-sans-serif,system-ui,sans-serif">{caption}</text></svg>')


def circle(radius: float, caption: str = "", colour: str = GREEN,
           draw_ms: int = 1100) -> str:
    """A circle with its radius drawn in — the shape behind 31% of the set."""
    if radius <= 0:
        sys.exit(f"radius {radius:g}: a circle needs a positive radius")
    r = min(radius * U, (H - 70) / 2)
    cx, cy = PAD + r + 4, (H - 40) / 2
    body = (f'<g fill="none" stroke="{colour}" stroke-width="3" stroke-linecap="round">'
            f'<circle class="s" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/></g>'
            f'<g class="f"><line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + r:.1f}" y2="{cy:.1f}" '
            f'stroke="{colour}" stroke-width="2" stroke-dasharray="4 3"/>'
            f'<text x="{cx + r / 2 - 8:.1f}" y="{cy - 8:.1f}" fill="#64748b" font-size="15" '
            f'font-family="ui-sans-serif,system-ui,sans-serif">{radius:g}</text></g>')
    return _frame(body, caption, colour, 2 * math.pi * r, draw_ms)


def rectangle(width: float, height: float, caption: str = "", colour: str = GREEN,
              draw_ms: int = 1100) -> str:
    """A rectangle with both sides labelled. A square is the equal-sides case."""
    if width <= 0 or height <= 0:
        sys.exit(f"{width:g} x {height:g}: both sides must be positive")
    scale = min(U, (W - 2 * PAD - 40) / width, (H - 80) / height)
    w, h = width * scale, height * scale
    x, y = PAD, (H - 40 - h) / 2
    body = (f'<g fill="none" stroke="{colour}" stroke-width="3" stroke-linejoin="round">'
            f'<rect class="s" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/></g>'
            f'<g class="f" fill="#64748b" font-size="15" '
            f'font-family="ui-sans-serif,system-ui,sans-serif">'
            f'<text x="{x + w / 2 - 8:.1f}" y="{y + h + 20:.1f}">{width:g}</text>'
            f'<text x="{x + w + 8:.1f}" y="{y + h / 2 + 5:.1f}">{height:g}</text></g>')
    return _frame(body, caption, colour, 2 * (w + h), draw_ms)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="shape", required=True)
    specs = {"triangle": ("--sides", dict(nargs=3, type=float, metavar=("A", "B", "C"))),
             "circle": ("--radius", dict(type=float, metavar="R")),
             "rectangle": ("--size", dict(nargs=2, type=float, metavar=("W", "H")))}
    for shape, (flag, kw) in specs.items():
        sp = sub.add_parser(shape)
        sp.add_argument(flag, required=True, **kw)
        sp.add_argument("--caption", default="")
        sp.add_argument("--colour", default="green", choices=("green", "red", "grey"))

    a = ap.parse_args()
    colour = {"green": GREEN, "red": RED, "grey": GREY}[a.colour]
    args = {"triangle": lambda: a.sides, "circle": lambda: [a.radius],
            "rectangle": lambda: a.size}[a.shape]()
    print({"triangle": triangle, "circle": circle, "rectangle": rectangle}[a.shape](
        *args, caption=a.caption, colour=colour))
    return 0


if __name__ == "__main__":
    sys.exit(main())

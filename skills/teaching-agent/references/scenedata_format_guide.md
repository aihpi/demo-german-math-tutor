# SCENE_DATA format guide

You produce **one JSON object**. Nothing else — no prose, no markdown fence, no
Python. It is passed straight to:

```bash
render_scene.py --template comparison_split --data scene.json
```

which validates it, renders a 1080p60 MP4, and prints a marker the chat plays
inline. On a bad field it exits 2 with a message naming the field. Read the
message, fix that field, try again.

SCENE_DATA drives a **WATCH** output — something the user observes. For
something the user plays, see `gamedata_format_guide.md` instead.

---

## `comparison_split`

Two things side by side. Each side has a label, a colour, a grid or row of
circular nodes (some lit, some dim), and a number that counts up. A comparison
line lands at the bottom. Runs 10.5 seconds.

Use it whenever the lesson is **"this versus that, and here is the gap"**.

```json
{
  "title": "Dense vs MoE Inference",
  "left": {
    "label": "Dense Model (31.6B)",
    "color": "#FF4444",
    "nodes": { "total": 16, "active": 16, "arrangement": "grid", "rows": 4, "cols": 4,
               "activation": "stagger" },
    "metric": { "label": "FLOPs", "value": 31.6, "unit": "B", "countUp": true }
  },
  "right": {
    "label": "MoE Model (3.2B active)",
    "color": "#50C878",
    "nodes": { "total": 16, "active": 3, "arrangement": "grid", "rows": 4, "cols": 4,
               "activation": "stagger" },
    "metric": { "label": "FLOPs", "value": 3.2, "unit": "B", "countUp": true }
  },
  "comparison": { "show": true, "label": "{ratio}x less compute", "highlightColor": "#FF7500" },
  "style": { "background": "#1a1a1a", "textColor": "#e0e0e0", "accent": "#FF7500",
             "font": "Helvetica", "dividerColor": "#444444" },
  "timing": { "titleDuration": 1.5, "labelsDuration": 1.0, "animationDuration": 4.0,
              "comparisonDuration": 2.0, "endHold": 1.5 }
}
```

### Fields

| field | required | notes |
|---|---|---|
| `title` | yes | one line, shown top-centre |
| `left` / `right` | yes | each needs `label`; everything under them has defaults |
| `*.label` | yes | keep under ~28 characters — it must fit half a frame |
| `*.color` | no | hex. Give the two sides **contrasting** colours; that contrast is the argument |
| `*.nodes.total` | no | how many circles. **3–64.** Over ~120 they are unreadable dots |
| `*.nodes.active` | no | how many light up — an integer (the first N) or a list of indices |
| `*.nodes.arrangement` | no | `"grid"` or `"row"` |
| `*.nodes.rows` / `.cols` | grid only | **`rows * cols` must equal `total`**, or the build fails |
| `*.nodes.activation` | no | see below; default `"stagger"` |
| `*.metric.label` | no | caption under the number, e.g. `FLOPs` |
| `*.metric.value` | no | a number, not a string |
| `*.metric.unit` | no | suffix glued to the number: `"B"` → `31.6B`. Use `""` for none |
| `*.metric.countUp` | no | `true` animates 0 → value; `false` shows it statically |
| `comparison.label` | no | may contain `{ratio}` — see below |
| `style`, `timing` | no | omit them; the defaults are the house style |

### `activation` — how the lit nodes come on

| value | looks like | use for |
|---|---|---|
| `"stagger"` (default) | all active nodes pulse in a shuffled order | most things — parallel but organic |
| `"sequential"` | one at a time, left to right | autoregressive decoding, serial pipelines, anything strictly ordered |
| `"simultaneous"` | every active node brightens together | parallel denoising, batch processing, SIMD |

**This is the field that carries the meaning** when both sides look alike.
Autoregressive versus diffusion are both a row of 9 nodes; `sequential` versus
`simultaneous` is the entire difference between them.

### `{ratio}`

`comparison.label` may contain `{ratio}`, replaced by the larger metric divided
by the smaller, to one decimal with a trailing `.0` stripped:

- `31.6` and `3.2` → `9.9`, so `"{ratio}x less compute"` renders **"9.9x less compute"**
- `6` and `1` → `6`, so `"{ratio}x throughput gain"` renders **"6x throughput gain"**

If either value is 0 the placeholder empties rather than dividing by zero — so
phrase the label to survive that, or avoid a zero metric.

### Making it teach something

- **The node counts are the argument.** 16-of-16 beside 3-of-16 says the whole
  thing before a word is read. If both sides light the same fraction, the
  animation has no point.
- **The metric should match the nodes.** If the left side lights 5× more nodes,
  its number should be roughly 5× bigger. A viewer who notices a mismatch stops
  trusting the picture.
- **Use `total` values that make a clean grid.** 16 (4×4), 20 (4×5), 24 (4×6),
  64 (8×8). A prime total forces a 1×N row.
- **Both sides should use the same `total`** when the point is *which fraction
  fires*. Use different totals only when the point is *how many exist* — CPU
  cores versus GPU cores.

---

## `curve_plot`

One to three declared curves on shared axes, with an optional marker that walks
downhill (or up). Use it when the lesson is **a shape over a range** — a descent,
a divergence, a crossover — rather than a two-way count.

Two shapes, from the same engine:

**A. A walker.** One curve, plus a dot that steps along it by
`rate × gradient`. For gradient descent, convergence, divergence, getting stuck.

```json
{
  "title": "Gradient Descent",
  "domain": [-6, 6],
  "axes": { "x": "parameter θ", "y": "loss" },
  "curves": [
    { "label": "loss surface", "color": "#4A9EFF",
      "terms": [ { "type": "quad", "a": 0.15 }, { "type": "sin", "amp": 1, "freq": 1.5 } ] }
  ],
  "walker": { "start": 5.2, "rate": 0.35, "steps": 14, "direction": "min", "color": "#FF7500" },
  "callout": { "show": true, "label": "it stops at the nearest valley, not the deepest" }
}
```

**B. Two curves.** No walker. For train-vs-validation, bias vs variance,
anything where the *gap* is the point.

```json
{
  "title": "Overfitting",
  "domain": [1, 12],
  "axes": { "x": "model complexity", "y": "error" },
  "curves": [
    { "label": "training error", "color": "#50C878",
      "terms": [ { "type": "exp", "amp": 9, "rate": -0.42 }, { "type": "const", "c": 0.3 } ] },
    { "label": "validation error", "color": "#FF4444", "dashed": true,
      "terms": [ { "type": "exp", "amp": 9, "rate": -0.42 }, { "type": "quad", "a": 0.075 },
                 { "type": "const", "c": 0.5 } ] }
  ],
  "callout": { "show": true, "label": "training error keeps falling — the gap is the overfit" }
}
```

### Fields

| field | required | notes |
|---|---|---|
| `title` | yes | one line, top-centre |
| `domain` | yes | `[min, max]`, low to high |
| `curves` | yes | **1–3.** Each needs a non-empty `terms` list |
| `curves[].label` | no | appears in the legend, top-right |
| `curves[].color` | no | give contrasting colours; the contrast is the argument |
| `curves[].dashed` | no | `true` for the "worse" line — it reads as the warning |
| `axes.x` / `.y` | no | short axis captions |
| `walker` | no | omit for shape B |
| `walker.start` | no | must be inside `domain` |
| `walker.rate` | no | step size × gradient. Too small and it crawls; too big and it flies off |
| `walker.steps` | no | 10–16. It stops early once the gradient is ~0 |
| `walker.direction` | no | `min` (default) or `max` for ascent |
| `callout.label` | no | one short line at the bottom. This is where the lesson goes |
| `callout.at` | no | an x value to pin the callout near, instead of the bottom |

**No y-range field** — it is computed from the curves, so it always fits.

### Term types

Same vocabulary as `parameter_control`'s landscape, so one guide teaches both:

| type | fields | contributes |
|---|---|---|
| `const` | `c` | `c` |
| `lin` | `m` | `m·x` |
| `quad` | `a` | `a·x²` |
| `sin` / `cos` | `amp`, `freq`, `phase?` | `amp·sin(freq·x + phase)` |
| `exp` | `amp`, `rate` | `amp·e^(rate·x)` |
| `inv` | `a`, `shift?` | `a / (x + shift)` |

The derivative is worked out analytically from these, so the walker follows the
true gradient. **You never write a formula.**

### Making it teach something

- **A walker needs more than one valley.** A single `quad` converges from
  anywhere and shows nothing; add a `sin` so where you start decides where you
  stop. That is the whole lesson of local minima.
- **Two curves must actually separate.** If they stay parallel there is no gap
  to point at. One falling `exp` plus a rising `quad` gives the classic U.
- **Put the insight in `callout`, not the title.** The title names the concept;
  the callout says what the picture proves.

Placeholders: none — `curve_plot` text is literal, not templated.

---

## Common mistakes

| symptom | cause |
|---|---|
| exit 2, "rows*cols must equal total" | grid arithmetic is wrong — fix `rows`, `cols` or `total` |
| exit 2, "active exceeds total" | more lit nodes than nodes |
| exit 2, "activation must be…" | typo; it is `stagger`, `sequential` or `simultaneous` |
| the two sides look identical | same `active`/`total` fraction on both — there is no comparison |
| unreadable speckle | `total` over ~120 |
| `{ratio}` renders empty | one of the metric values is 0 |
| label runs into the divider | over ~28 characters; it is auto-shrunk, but it gets small |
| the numbers contradict the dots | metric ratio and node ratio disagree |

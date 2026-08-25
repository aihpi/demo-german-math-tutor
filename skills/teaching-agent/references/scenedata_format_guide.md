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

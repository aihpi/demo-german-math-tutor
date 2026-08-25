# GAME_DATA format guide

You produce **one JSON object**. Nothing else — no prose, no markdown fence, no
JavaScript. It is passed straight to:

```bash
generate_game.py --template <name> --game-data-file data.json
```

which validates it and writes a standalone `/tmp/game.html`. If the JSON is
invalid or a required field is missing, that command prints the exact problem on
stderr and exits 2. Read the message, fix the field, try again.

## Rules that apply to every template

- **`insight` is the whole point.** It is the text the player reads after
  playing. It must connect what they just *did* to what the concept *is*. Write
  2–4 sentences. Reference their actual result using `{placeholders}` (listed
  per template below). A placeholder the engine does not know is left on screen
  as literal `{braces}` — only use the ones listed.
- **HTML is allowed** in `intro.headline`, `intro.body`, `insight` and
  `messages.*`: `<b>`, `<i>`, `<sup>`, `<br>`, and `<span class="accent">`.
  Never write `<script>` or an unescaped `<`.
- **`intro` is required everywhere** and must have both `headline` and `body`.
  The headline is one short line. The body explains the controls in 1–3
  sentences — the player has never seen this game before.
- Keep item text **short**. Anything over ~24 characters is unreadable from the
  back of a lecture hall.
- Do not invent fields. Unknown keys are ignored silently, so a typo in an
  optional field looks like the engine ignoring you.

---

## `route_and_sort`

Items fall one at a time; the player clicks the destination each belongs to.

```json
{
  "title": "MoE ROUTER",
  "nouns": { "item": "token", "destination": "expert" },
  "intro": { "headline": "…", "body": "…" },
  "roundLength": 12,
  "speed": { "start": 1.6, "increaseEvery": 3, "increaseBy": 0.35 },
  "destinations": [
    { "name": "Math", "color": "#FF7500", "items": ["7 × 8 =", "√144"] }
  ],
  "insight": "…{accuracy}…{avgActivated}…{total}…{savedPct}…"
}
```

| field | required | default | notes |
|---|---|---|---|
| `title` | yes | — | short, uppercase reads well |
| `intro` | yes | — | `{headline, body}` |
| `destinations` | yes | — | **3–8**. Fewer than 3 is trivial; more than 8 stops fitting on screen |
| `destinations[].items` | yes | — | 4–6 each, so the pool does not repeat |
| `insight` | yes | — | see placeholders below |
| `nouns` | no | `{item, destination}` | drives the stat labels; give singulars, the engine adds `s` |
| `roundLength` | no | `12` | items per round |
| `speed` | no | `{1.6, 3, 0.35}` | `start` px/frame; speeds up every `increaseEvery` correct answers |

**Ambiguous items** — an item may be an object instead of a string:

```json
{ "text": "numpy.linalg.solve(A,b)", "also": ["Code"] }
```

It then counts as correct for its own destination *and* every name in `also`,
and is drawn with a dashed blue border. Names in `also` must match a
`destinations[].name` exactly or they are dropped. Use these for a
"make it harder" round.

Placeholders: `{score}` `{accuracy}` `{avgActivated}` `{savedPct}` `{total}`
`{bestStreak}` `{routed}`.

---

## `parameter_control`

A ball descends (or ascends) a landscape. A slider sets the step size.

```json
{
  "title": "GRADIENT DESCENT",
  "intro": { "headline": "…", "body": "…" },
  "landscape": { "domain": [-6, 6], "terms": [ {"type":"quad","a":0.15}, {"type":"sin","amp":1,"freq":1.5} ], "tolerance": 0.001 },
  "direction": "min",
  "start": 3.0,
  "param": { "label": "Learning rate", "min": 0.001, "max": 1.0, "default": 0.1, "log": true },
  "axis": { "x": "parameter θ", "y": "loss" },
  "messages": { "converged": "…", "diverged": "…", "tooSlow": "…" },
  "insight": "…{x}…{value}…{steps}…{rate}…"
}
```

**The landscape is declarative — you never write a formula.** The engine sums
the terms and differentiates them analytically, so the gradient shown is exact.

| `type` | fields | contributes |
|---|---|---|
| `const` | `c` | `c` |
| `lin` | `m` | `m·x` |
| `quad` | `a` | `a·x²` |
| `cubic` | `a` | `a·x³` |
| `sin` | `amp`, `freq`, `phase?` | `amp·sin(freq·x + phase)` |
| `cos` | `amp`, `freq`, `phase?` | `amp·cos(freq·x + phase)` |

Any other `type` throws on load and the page stays blank. 

**Design the landscape so the lesson is visible:** one quadratic for the bowl
plus one sine for ripples gives several local optima, which is what makes
"where you start matters" land. A pure quadratic converges from anywhere and
teaches nothing.

`direction` is `"min"` (default) or `"max"` — `"max"` flips the sign so the ball
climbs, which covers gradient *ascent* / reward maximisation with the same
engine. `param.log` gives the slider a logarithmic scale; use it whenever
`max/min > 100`, otherwise the useful range is one pixel wide.

Placeholders: `{x}` `{value}` `{steps}` `{rate}`.

---

## `predict_and_verify`

The player guesses a probability distribution, then sees the model's. Scored by
`100 × (1 − total-variation distance)`.

**Two shapes, pick one.** Every item must use the same shape.

**A. Pairwise (attention).** Items carry a value/key vector `v` and a query
vector `q`. The player picks a query item; the engine scores `qᵢ·kⱼ/√d`,
softmaxes, and draws arcs between items.

```json
{
  "title": "ATTENTION",
  "intro": { "headline": "…", "body": "…" },
  "nouns": { "item": "word", "query": "query" },
  "dims": ["DET", "ENTITY", "ACTION", "PLACE"],
  "temp": 6.25,
  "maskSelf": true,
  "startQuery": 1,
  "items": [ { "label": "cat", "v": [0,1,0,0], "q": [0,0,1,0.2] } ],
  "insight": "…{query}…{top}…{topP}…{score}…"
}
```

- `dims` names the feature axes. All `v` and `q` arrays must be exactly
  `dims.length` long.
- `v` is what the word *offers*; `q` is what it *looks for*. Make them
  interpretable — the weighted-sum table shows them to the player.
- `temp` scales the logits. With unit-ish vectors, `1` gives an almost flat
  distribution that teaches nothing; **6–7 gives a readable peak**. Tune it.
- `maskSelf: true` (default) stops a word attending to itself, which otherwise
  dominates and hides the point.

**B. Fixed logits (any distribution).** Items carry a raw `logit`. No query
selection, no arcs — bars only. Use for next-token probability, temperature
sampling, class scores.

```json
{
  "title": "NEXT-WORD PROBABILITY",
  "intro": { "headline": "…", "body": "…" },
  "context": "The cat sat on the <span class=\"accent\">___</span>",
  "temp": 1,
  "items": [ { "label": "mat", "logit": 4.1 } ],
  "insight": "…{top}…{topP}…{score}…"
}
```

The weighted-sum table only appears when every item has a `v` **and** `dims` is
set, so shape B skips it automatically.

Placeholders: `{score}` `{top}` `{topP}` `{query}` (pairwise only).

---

## Common mistakes

| symptom | cause |
|---|---|
| literal `{avgActivated}` on screen | placeholder not in that template's list |
| blank page | `landscape.terms` has an unknown `type`, or a `v`/`q` array is the wrong length |
| distribution looks flat and boring | `temp` too low in `predict_and_verify` |
| ball converges instantly from every start | landscape is a single `quad` — add a `sin` |
| ambiguous item never accepts the second expert | name in `also` does not match a `destinations[].name` |
| exit code 2, "missing required field" | read stderr, it names the field |

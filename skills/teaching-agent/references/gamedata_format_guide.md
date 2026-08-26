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

### Placeholders — check the meaning, the names are not self-explanatory

| placeholder | is | example |
|---|---|---|
| `{score}` | points scored | `252` |
| `{accuracy}` | percent correct, **bare number, no `%` sign** — write `{accuracy}%` | `85` |
| `{routed}` / `{items}` | how many items the player actually handled | `12` |
| `{total}` / `{destinations}` | how many **destinations** exist, *not* items played | `8` |
| `{avgActivated}` | destinations clicked per item | `1.3` |
| `{savedPct}` | percent of destinations left untouched per item | `84` |
| `{bestStreak}` | longest run of correct routes | `9` |

**`{total}` is the number of boxes on screen, not the number of items played.**
"You sorted {total} animals" prints "You sorted 8 animals" no matter how many
they sorted — use `{items}`. And `{accuracy}` has no percent sign of its own, so
`with {accuracy} accuracy` prints "with 85 accuracy".

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
| `sin` | `amp`, `freq`, `phase?` | `amp·sin(freq·x + phase)` |

Any other `type` throws on load and the page stays blank. 

**Design the landscape so the lesson is visible:** one quadratic for the bowl
plus one sine for ripples gives several local optima, which is what makes
"where you start matters" land. A pure quadratic converges from anywhere and
teaches nothing.

`direction` is `"min"` (default) or `"max"` — `"max"` flips the sign so the ball
climbs, which covers gradient *ascent* / reward maximisation with the same
engine. `param.log` gives the slider a logarithmic scale; use it whenever
`max/min > 100`, otherwise the useful range is one pixel wide.

### Placeholders

| placeholder | is |
|---|---|
| `{x}` | where the ball came to rest, on the x axis |
| `{value}` | the curve's value there (the loss or reward) |
| `{steps}` | how many steps it took |
| `{rate}` | the step size the player chose |

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

### Placeholders

| placeholder | is |
|---|---|
| `{score}` | 0–100, how close the guess was (bare number) |
| `{top}` | label of the item the model weighted highest |
| `{topP}` | that item's probability, e.g. `0.73` |
| `{query}` | the chosen query item's label — **pairwise shape only**, empty otherwise |

---

## `balance_tradeoff`

One slider, two meters that move in opposite directions, and no correct answer.
**Two shapes, pick one.**

**A. Classification (`items`).** Each item has a `score` 0–1 and `positive`
true/false. The engine builds the confusion matrix live and derives the metrics.

```json
{
  "title": "SPAM FILTER",
  "intro": { "headline": "…", "body": "…" },
  "param": { "label": "Spam threshold", "min": 0.05, "max": 0.95, "default": 0.5, "step": 0.01 },
  "buckets": { "above": "🚫 Spam folder", "below": "📥 Inbox" },
  "metrics": { "a": "precision", "b": "recall" },
  "objective": "f1",
  "items": [ { "label": "YOU HAVE WON", "score": 0.97, "positive": true } ],
  "insight": "…{threshold}…{metricA}…{metricB}…{best}…{caught}…{missed}…{falseAlarms}…"
}
```

Metric names: `precision`, `recall`, `specificity`, `fpr`, `accuracy`, `f1`.
`objective` is the one being scored against the best achievable threshold.

**The classes must overlap.** If every positive scores above every negative, a
threshold exists with a perfect score and the game teaches the opposite of its
own lesson. At least one negative must outrank a positive. 12–16 items.

**B. Two declared curves (`curves`).** No items, no classifier. Both curves use
the same term vocabulary as `parameter_control`, plus `exp` (`amp`, `rate`).

```json
{
  "param": { "label": "Model complexity", "min": 1, "max": 12, "default": 2, "step": 0.1 },
  "objective": "min-sum",
  "curves": {
    "a": { "label": "Bias²",    "terms": [ {"type":"exp","amp":9,"rate":-0.45}, {"type":"const","c":0.3} ] },
    "b": { "label": "Variance", "terms": [ {"type":"quad","a":0.075}, {"type":"const","c":0.2} ] }
  }
}
```

`objective` is `min-sum` (total error, U-shaped) or `max-sum`. **Make one curve
fall and the other rise**, or there is no tradeoff to find.

### Placeholders

| placeholder | is |
|---|---|
| `{threshold}` | where the player left the slider |
| `{best}` | the slider position that would have been optimal |
| `{score}` | 0–100 against that optimum (bare number) |
| `{metricA}` / `{metricB}` | the two metric values — **items shape: bare number, no `%`** |
| `{nameA}` / `{nameB}` | the metric names, e.g. `precision` |
| `{caught}` / `{missed}` / `{falseAlarms}` | true positives / false negatives / false positives — **items shape only**, all `0` in curves shape |

---

## `explore_grid`

Fog-of-war tiles over a hidden landscape, a fixed budget of reveals, and the
choice of whether to probe near your best result or look somewhere new.

```json
{
  "title": "HYPERPARAMETER HUNT",
  "intro": { "headline": "…", "body": "…" },
  "grid": { "width": 10, "height": 10, "totalBudget": 25, "budgetLabel": "GPU hours left" },
  "axes": { "x": { "label": "Learning rate", "range": "0.0001 → 0.1" },
            "y": { "label": "Batch size", "range": "8 → 512" } },
  "landscape": {
    "peaks": [ { "x": 3, "y": 6, "value": 95.2, "radius": 2.0, "label": "Global optimum" },
               { "x": 7, "y": 2, "value": 88.5, "radius": 1.5, "label": "Local optimum" } ],
    "baseValue": 60, "noiseAmount": 3, "valueLabel": "Validation accuracy (%)"
  },
  "strategies": { "bayesianLike": "…", "randomSearch": "…", "mixed": "…" },
  "insights": {
    "foundGlobal": { "title": "…", "body": "…" },
    "foundLocal":  { "title": "…", "body": "…" },
    "scattered":   { "title": "…", "body": "…" }
  }
}
```

**This template uses `insights` (plural, keyed), not `insight`.** All three keys
are required; the engine picks one from the outcome. "Found the global optimum"
is decided by whether the best revealed tile lies inside the top peak's
`radius` — position, not value, because noise can push a local peak's reading
above a sample near the global one.

- **At least two peaks**, or there is no exploration dilemma. Put the second
  one nearer the likely starting corner than the global peak.
- `noiseAmount` well under the gap between peak values — noise larger than the
  gap makes the landscape unreadable.
- `totalBudget` around a quarter of the tiles. All 100 reveals is not a game.

### Placeholders

| placeholder | is |
|---|---|
| `{bestX}` / `{bestY}` | grid coordinates of the best tile found |
| `{bestValue}` | its value |
| `{globalValue}` | the best value that existed anywhere |
| `{reveals}` | tiles actually revealed |
| `{budget}` | tiles they were allowed |
| `{strategy}` | the matching sentence from your `strategies` block |
| `{exploitPercent}` | percent of reveals made next to the running best |
| `{uniqueRegions}` | how many separate areas were probed |
| `{optimalReveals}` | roughly what a good search would have needed |

---

## `customization` — optional, every template

Every field is optional and every default is sensible. Omit the whole block and
the game still looks right. Add fields to give a concept a mood.

```json
"customization": {
  "theme":       { "accent": "#FF4444", "secondary": "#4A9EFF", "success": "#50C878",
                   "error": "#FF4444", "background": "#1a1a1a", "surface": "#252525",
                   "particleEffect": "sparks" },
  "sounds":      { "enabled": true, "correct": "chirp", "wrong": "buzz", "complete": "fanfare" },
  "difficulty":  { "mode": "adaptive", "startLevel": 1, "maxLevel": 5, "adaptiveThreshold": 0.8 },
  "titleScreen": { "emoji": "🧠", "flavor": "…", "instructions": "…",
                   "showScore": true, "showStreak": true },
  "endScreen":   { "grading": [ { "min": 90, "emoji": "🏆", "label": "Expert!" } ],
                   "shareText": "I scored {score}!", "showReplayButton": true },
  "animations":  { "speed": "normal", "transitions": "slide", "celebrationIntensity": 3 },
  "layout":      { "mobileOptimized": true },
  "multiplayer": { "enabled": false, "players": ["Ada", "Alan"], "showLeaderboard": true }
}
```

- `particleEffect`: `sparks` · `confetti` · `ripple` · `none`
- `sounds.correct`: `chirp` · `ding` · `pop` · `chord`; `.wrong`: `buzz` · `thud`
  · `descend`; `.complete`: `fanfare` · `tada` · `calm`. Oscillators, no files.
- `difficulty.mode`: `fixed` · `linear` · `adaptive` · `sudden`
- `animations.speed`: `slow` · `normal` · `fast` · `instant`
- `multiplayer` is **local hot-seat** — players take turns on one machine and a
  leaderboard appears at the end. Nothing is networked.
- `grading` replaces the whole ladder, so give every band you want, ending at
  `"min": 0`.

**Match the mood to the concept.** Overfitting deserves a red accent, no
particles and `speed: "fast"`. A first-contact explainer deserves the playful
default. Do not set customization at random — an unset field is better than a
wrong one.

## Common mistakes

| symptom | cause |
|---|---|
| literal `{avgActivated}` on screen | placeholder not in that template's list |
| blank page | `landscape.terms` has an unknown `type`, or a `v`/`q` array is the wrong length |
| distribution looks flat and boring | `temp` too low in `predict_and_verify` |
| ball converges instantly from every start | landscape is a single `quad` — add a `sin` |
| ambiguous item never accepts the second expert | name in `also` does not match a `destinations[].name` |
| exit code 2, "missing required field" | read stderr, it names the field |
| `balance_tradeoff` scores 100 too easily | the item classes separate cleanly — make them overlap |
| `explore_grid` always says "found the optimum" | only one peak, so every tile is in its basin |
| customization ignored | a typo'd key is silently dropped; check spelling against the list |
| "You sorted 8 animals" when 20 were played | `{total}` is the destination count — use `{items}` |
| "with 85 accuracy" | `{accuracy}` carries no `%`; write `{accuracy}%` |
| an unknown placeholder printed as `{braces}` | it is not in that template's table above |

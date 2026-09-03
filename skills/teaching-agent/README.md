# Teaching Agent — a Hermes Agent skill

Teaches a concept by rendering an animation to **watch**, generating a game to
**play**, or both in sequence — then explaining what the learner just saw and did.

Two kinds of engine, one skill:

- **WATCH** — three Manim templates render a 1080p60 MP4 from a SCENE_DATA JSON
  object, played inline in the chat via a `#media:` marker.
  `comparison_split` answers *how many of these versus those*; `curve_plot`
  answers *what shape does this take over a range* (one curve with a descending
  walker, or two curves diverging); `pipeline_flow` answers *what happens, in
  what order* (set `loop: true` for a cycle).
- **PLAY** — five HTML game engines built from a GAME_DATA JSON object. Opens in
  the preview rail via a `#preview/` marker.

`references/concept_to_output.md` decides which. The two markers are not
interchangeable: video takes an absolute file path, the game takes a loopback URL.

## Animations

```bash
python3 skills/teaching-agent/scripts/render_scene.py --author "dense vs MoE inference"
python3 skills/teaching-agent/scripts/render_scene.py --template curve_plot --data overfitting_curves.json --quality l
```

`--author` generates SCENE_DATA, retries twice feeding the validator's error
back, then falls back to a cached scene — the same contract as
`generate_game.py --author`. Renders 1080p60 in ~15 s; the whole
generate-and-render round trip is 40–70 s.

| template | mechanic | tested with |
|---|---|---|
| `comparison_split` | two node grids side by side, counters running | dense vs MoE, AR vs diffusion |
| `curve_plot` | declared curves, with an optional marker walking downhill | gradient descent, overfitting |
| `pipeline_flow` | one thing through named stages, transforming; `loop` for cycles | transformer pipeline, water cycle |

A template reads everything from `SCENE_DATA_PATH` and is never edited to change
the concept: dense-vs-MoE and AR-vs-diffusion render from a byte-identical Python
file, and so do the two `curve_plot` scenes.

The model-facing spec is
[`references/scenedata_format_guide.md`](references/scenedata_format_guide.md).

## Games

Each game engine is a complete HTML page with two markers punched out of it;
`generate_game.py` fills them in and writes a standalone file that needs no
server, no network, and no build step to open.

```bash
python3 skills/teaching-agent/scripts/generate_game.py --author "MoE routing" --serve
python3 skills/teaching-agent/scripts/generate_game.py \
    --template route_and_sort --game-data-file tested_gamedata/moe_routing.json --serve
# -> [Preview: <hash>.html](#preview/http%3A%2F%2F127.0.0.1%3A8732%2F<hash>.html)
```

| template | mechanic | tested with |
|---|---|---|
| `route_and_sort` | items fall, click the destination each belongs to | MoE routing, MoE routing (hard), ticket triage |
| `parameter_control` | a slider sets step size, a ball walks a landscape | gradient descent, gradient ascent / reward |
| `predict_and_verify` | guess a distribution, then see the model's | attention weights, next-word probability |
| `balance_tradeoff` | one slider, two meters that fight | precision/recall (spam filter), bias/variance |
| `explore_grid` | spend a fixed budget to find something hidden | hyperparameter search, A/B testing |

The model-facing spec for GAME_DATA is
[`references/gamedata_format_guide.md`](references/gamedata_format_guide.md); the
template-picking rules are in
[`references/concept_to_template.md`](references/concept_to_template.md).

## What each template is for

The engines are not about machine learning. Each is a **shape of understanding**,
and every subject has those shapes — a taxonomy is a routing problem, a
diagnostic threshold is a tradeoff, a dig site is a search under budget. Pick the
shape, then dress it in the learner's subject.

### WATCH — animations (`manim_templates/`)

| template | the question it answers | ML | beyond ML |
|---|---|---|---|
| `comparison_split` | how many of **these** versus **those**? | dense vs MoE · AR vs diffusion · CPU vs GPU cores · quantized vs full-precision · batch 1 vs 8 | chromosome counts in mitosis vs meiosis · energy per kWh coal vs solar · two national budgets · army sizes in history · calories in two meals |
| `curve_plot` | what **shape** does this take over a range? | gradient descent · overfitting · scaling laws · loss curves · convergence vs divergence | supply and demand crossing · logistic vs exponential growth · radioactive decay · projectile paths · enzyme kinetics · dose–response · compound interest |
| `pipeline_flow` | what happens, **in what order**, and what does it become? | tokenise → embed → attend → predict · RAG lookup · training loop · diffusion sampling | the water cycle · photosynthesis · digestion · rock and nitrogen cycles · DNA → RNA → protein · a bill becoming law · a factory line |

### PLAY — games (`templates/`)

| template | the question it answers | ML | beyond ML |
|---|---|---|---|
| `route_and_sort` | which of several places does this belong in? | MoE routing · load balancing · KV cache · sharding · tokenization | biological taxonomy · organelles to functions · elements to periodic groups · parts of speech · rock types · climate zones · blood typing · symptoms to body systems · waste sorting |
| `parameter_control` | one knob — can you live with what it does? | learning rate · momentum · optimizers · local vs global optima | a molecule finding its lowest-energy shape · a system settling to equilibrium · profit against price · dosage titration · tuning a PID gain |
| `predict_and_verify` | commit to a guess, then see the truth | attention weights · next-token probability · temperature · embedding similarity | Punnett-square ratios · allele frequencies · dice and cards · diagnostic likelihoods · election and weather forecasts |
| `balance_tradeoff` | helping one number hurts another | precision vs recall · overfitting · bias vs variance · quantization | a test's sensitivity vs specificity · burden of proof · safety factor vs cost · strength vs weight · inflation vs unemployment · conservation vs development |
| `explore_grid` | something is hidden and the budget runs out first | hyperparameter search · bandits · Bayesian optimization · A/B testing | where to excavate a dig · which compounds to screen · where to drill · which channels to test · an animal choosing foraging patches |

### Choosing between them

Ask what the learner has to **do**, not what subject it is:

- a decision with a wrong answer → **PLAY**
- only a magnitude or a shape to notice → **WATCH**
- both → WATCH first, then PLAY

Non-ML has been exercised, not just asserted: the games were probed across
biology, maths and geography (all five picked sensibly and rendered), and
`curve_plot` was checked on supply/demand and logistic growth. What no template covers yet is a **spatial architecture walkthrough** (how the
parts of a network sit together) or a **progressive reveal** (something emerging
from noise, which is diffusion's own subject).

## Installing

The skill is self-contained — everything it reads lives under this directory:

```bash
cp -r skills/teaching-agent ~/.hermes/skills/
```

`SKILL.md` uses `${HERMES_SKILL_DIR}`, so `skills.template_vars: true` must be
set in `~/.hermes/config.yaml` (it already is for the math-tutor demo — see
`config/hermes_config.yaml`).

## Serving

`--serve` publishes the built page and prints a loopback URL:

```bash
python3 scripts/generate_game.py --template route_and_sort \
    --game-data-file tested_gamedata/moe_routing.json --serve
# -> [Preview: 74d00491d26e.html](#preview/http%3A%2F%2F127.0.0.1%3A8732%2F74d00491d26e.html)
#    (--url-only prints the bare URL instead)
```

Three deliberate choices there, all copied from how math-tutor serves its SVG
figures, because that mechanism is already proven against the desktop app:

- **http, not `file://` or a `data:` URI.** The desktop app's renderer rejects
  `data:` URIs and its `hermes-media://` scheme carries audio and video only. A
  loopback origin is the only route that renders.
- **Detached server.** `Popen(..., start_new_session=True)` plus a readiness
  poll, so the agent's `terminal` call returns immediately (~0.2s cold) instead
  of blocking on a server that never exits.
- **Content-hashed filenames.** "Make it harder" produces different bytes, so it
  produces a different URL, so the preview rail can never show a cached copy of
  the previous round.

Port **8732**; math-tutor holds 8731.

## How substitution works

`base.html` is not a page — it is the shared stylesheet (all design tokens, the
HPI orange, the button and card styles). Each template writes two markers:

```
/*__BASE_CSS__*/     <- base.html is inlined here
/*__GAME_DATA__*/    <- the JSON object is inlined here
```

`generate_game.py` refuses to build if either marker is missing, if the JSON is
malformed, or if a template's required fields are absent — and prints a message
naming the field, because that message is what the generating model gets to
read before its retry.

## Checking a change

```bash
python3 tests/test_templates.py
```

Builds every JSON in `tested_gamedata/` against its template and asserts the
output has no surviving markers, has the stylesheet inlined, and uses only
placeholders the engine actually fills. It also asserts that malformed
GAME_DATA is rejected rather than silently producing a broken page. If you add
a template, add two GAME_DATA files for it and a line in `CASES` — one example
never catches a leaking abstraction.

## Rendering inside the app

The rail takes an `http(s)` target as `kind: 'url'`, which
`right-rail/preview-pane.tsx` routes to a live web view — so the page's
JavaScript runs and the game is playable in the chat window.

It only opens for one specific markdown form:

```
[Preview: game.html](#preview/http%3A%2F%2F127.0.0.1%3A8732%2Fgame.html)
```

A plain `[Open the game](http://127.0.0.1:8732/game.html)` does **not** work.
`lib/markdown-preprocess.ts` strips bare loopback URLs from assistant text, and
`extractPreviewTargets()` ignores them by design — its own test asserts
`extractPreviewTargets('Preview: http://localhost:5173/')` returns `[]`. Only
`#preview:` / `#preview/` registers a target.

`serve_game.py` emits that marker so the model never hand-encodes it; the
percent-encoding is checked byte-for-byte against `encodeURIComponent`, and the
result against the app's own `PREVIEW_MARKDOWN_RE`. `--url-only` prints the
plain URL for opening in a browser instead.

## Customization

Every engine reads an optional `customization` block from GAME_DATA via the
shared runtime in `templates/base.js` (theme, Web Audio sounds, difficulty
curve, title and end screens, animation speed, and local hot-seat multiplayer).
Every field is optional; the tested GAME_DATA files that omit the block render
exactly as they did before it existed.

Multiplayer is **hot-seat**, not networked — players take one machine in turns
and a leaderboard appears at the end.

## Not built yet

`race_algorithm` and `build_and_test` do not exist. Neither appears in the
scripted demo; they are only reached by audience-choice topics.

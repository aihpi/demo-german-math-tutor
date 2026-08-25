# Teaching Games — a Hermes Agent skill

Teaches a concept by generating a playable browser game, serving it on loopback,
and explaining afterwards what the player just did. Five game engines. Each one is a complete HTML page with two markers punched
out of it; `generate_game.py` fills them in and writes a standalone file that
needs no server, no network, and no build step to open.

```bash
python3 skills/teaching-games/scripts/generate_game.py \
    --template route_and_sort \
    --game-data-file tested_gamedata/moe_routing.json \
    --out /tmp/game.html

python3 skills/teaching-games/scripts/serve_game.py --file /tmp/game.html
# -> http://127.0.0.1:8080/game.html
```

| template | mechanic | tested with |
|---|---|---|
| `route_and_sort` | items fall, click the destination each belongs to | MoE routing, MoE routing (hard), ticket triage |
| `parameter_control` | a slider sets step size, a ball walks a landscape | gradient descent, gradient ascent / reward |
| `predict_and_verify` | guess a distribution, then see the model's | attention weights, next-word probability |
| `balance_tradeoff` | one slider, two meters that fight | precision/recall (spam filter), bias/variance |
| `explore_grid` | spend a fixed budget to find something hidden | hyperparameter search, A/B testing |

The model-facing spec for authoring GAME_DATA is
[`references/gamedata_format_guide.md`](references/gamedata_format_guide.md); the
template-picking rules are in
[`references/concept_to_template.md`](references/concept_to_template.md).

## Installing

The skill is self-contained — everything it reads lives under this directory:

```bash
cp -r skills/teaching-games ~/.hermes/skills/
```

`SKILL.md` uses `${HERMES_SKILL_DIR}`, so `skills.template_vars: true` must be
set in `~/.hermes/config.yaml` (it already is for the math-tutor demo — see
`config/hermes_config.yaml`).

## Serving

`--serve` publishes the built page and prints a loopback URL:

```bash
python3 scripts/generate_game.py --template route_and_sort \
    --game-data-file tested_gamedata/moe_routing.json --serve
# -> http://127.0.0.1:8732/74d00491d26e.html
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

## Known unknown: does the preview rail render interactive HTML?

Proven: the desktop app renders **images** from a loopback origin — that is what
math-tutor's `figures.py` does today. Not proven: that the preview rail will
open an **interactive HTML page** and run its JavaScript. Nothing in this repo
exercises that path, and no amount of local testing settles it.

The games have been verified end to end over `http://127.0.0.1:8732` in a real
browser — full round played, styles applied, scoring correct — so if the rail
does not cooperate, opening the same URL in a browser beside the app is a
working fallback that costs nothing.

**This is the day-1 check in the project plan. Do it before anything else.**

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

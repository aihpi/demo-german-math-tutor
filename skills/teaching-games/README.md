# Teaching Games — template engines

Three game engines. Each one is a complete HTML page with two markers punched
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

The model-facing spec for authoring GAME_DATA is
[`references/gamedata_format_guide.md`](references/gamedata_format_guide.md).

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

## Not built yet

`balance_tradeoff`, `race_algorithm` and `build_and_test` do not exist.
`balance_tradeoff` is the one the scripted demo needs (Round 2, precision vs
recall); the other two are only reached by audience-choice topics.

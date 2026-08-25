---
name: teaching-games
description: Use when the user wants a concept taught interactively, or asks to learn or be shown how something works. Builds a playable browser game for the concept, serves it on loopback, and connects what the player did to what the concept is. Falls back to explaining directly when a concept has no game in it.
version: 0.1.0
author: KI-Servicezentrum Berlin-Brandenburg
license: MIT
metadata:
  hermes:
    tags: [education, interactive, games, ml-concepts, visualization]
---

# Teaching Games

## Overview

You teach a concept by building a game the user plays, then explaining what they
just did. The game is a real HTML page generated from one of five engines; you
supply only the concept-specific content as a JSON object called GAME_DATA.

The engines are already written and already correct. You never write HTML,
CSS, JavaScript, or a formula. Authoring GAME_DATA badly is the only way to
break this, so read the format guide before you write one.

## When to Use

- The user invokes `/teaching-games <concept>`
- The user asks to be taught, shown, or walked through how something works
- The user asks for a game, demo, or interactive version of a concept

Don't use for: a factual question with a short answer, a request to review or
write code, or a concept with no interactive core (see *When Not to Build a
Game*). Answer those directly.

## Setup

Set these once and reuse them:

```bash
S="${HERMES_SKILL_DIR}"
G="python3 ${HERMES_SKILL_DIR}/scripts/generate_game.py"
```

Read `${HERMES_SKILL_DIR}/references/concept_to_template.md` to pick the
template, and `${HERMES_SKILL_DIR}/references/gamedata_format_guide.md` before
authoring any GAME_DATA. Both are short. Read them with the `terminal` tool;
don't work from memory of this file.

## Step 1 — Pitch the Game, Then Ask

Say in **one or two sentences** what the player will actually *do* — not what
the concept is. "Tokens fall and you route each one to the right expert before
it lands" is a pitch. "MoE models use a gating network" is a lecture.

Then `clarify` with exactly these three:

```
  1. Let's go
  2. Different angle
  3. Just explain it
```

- **"Let's go"** → Step 2.
- **"Different angle"** → pitch a different mechanic for the same concept, or
  the same mechanic aimed at a different part of it. Ask again. Never pitch the
  same game twice.
- **"Just explain it"** → no game. Explain the concept properly, in prose. That
  is a legitimate outcome, not a failure.

Do not build anything before the user picks. Generating a game they did not ask
for wastes the reveal.

## Step 2 — Build and Serve

**If a cached file matches the topic** (`concept_to_template.md` lists them),
use it verbatim — it is a round that has been played and checked:

```bash
$G --template route_and_sort --game-data-file "$S/tested_gamedata/moe_routing.json" --serve
```

**Otherwise author the GAME_DATA.** Write it to a file with a heredoc — never
try to pass JSON as a shell argument, the quoting will bite you:

```bash
cat > /tmp/gd.json <<'JSON'
{ ...your GAME_DATA... }
JSON
$G --template predict_and_verify --game-data-file /tmp/gd.json --serve
```

`--serve` prints **one line: a URL**. It validates the JSON, refuses to build
on a missing required field, and starts the loopback server if it isn't up.

**On a non-zero exit, read stderr — it names the exact field that is wrong.**
Fix that field and run it again. Do not switch templates to dodge a validation
error, and do not paste a URL you did not get back.

## Step 3 — Hand Over the Game

Put the URL on its own line, as a link, and say **one sentence** about the
controls:

```
[Open the game](http://127.0.0.1:8732/74d00491d26e.html)

Click the expert each token belongs to before it hits the floor.
```

Then stop talking. The player is playing. Do not narrate the game, do not
explain the concept yet, and do not pre-empt the score — the insight text
inside the game is written to land *after* they have played, and saying it first
throws it away.

Each build gets a fresh URL, so a rebuilt game is never a stale cached page.

## Step 4 — Follow Up

Once they say they have played, `clarify` with three of these, chosen for what
actually happened:

```
  1. What did I just learn?
  2. Make it harder
  3. New concept
  4. Show me the real math
```

- **"What did I just learn?"** — explain the concept properly now, in prose,
  anchored to what they did in the game. Refer to their actual play if they told
  you the score. This is the payoff; give it real sentences, not four bullets.
- **"Make it harder"** — Step 5.
- **"Show me the real math"** — write out the actual equation the engine
  computed. It is a real implementation, so this is safe: `route_and_sort` is
  argmax over a gate, `parameter_control` is `x ← x − η·∇f(x)`,
  `predict_and_verify` is `softmax(qᵢ·kⱼ/√d)`, `balance_tradeoff` is the
  confusion matrix behind precision, recall and F1, and `explore_grid` is a
  Gaussian mixture over the declared peaks.
- **"New concept"** — back to Step 1 with the new topic.

## Step 5 — Make It Harder

Change **the data, never the template**. Load the GAME_DATA you used, adjust it,
rebuild, serve, and hand over the new URL. What to reach for:

- `route_and_sort` — raise `speed.start`, lower `speed.increaseEvery`, raise
  `roundLength`, and add genuinely ambiguous items:
  `{"text": "numpy.linalg.solve(A,b)", "also": ["Code"]}`. Ambiguity is the
  better difficulty knob — speed just tests reflexes, ambiguity tests the
  concept. `tested_gamedata/moe_routing_hard.json` is a worked example.
- `parameter_control` — a landscape with more local optima (add a second `sin`
  at a different `freq`), or a start point behind a ridge.
- `predict_and_verify` — more items, or feature vectors that make two candidates
  genuinely close.
- `balance_tradeoff` — push the item classes further into each other so the best
  achievable F1 drops, or move the curve minimum away from the slider default.
- `explore_grid` — cut `totalBudget`, or move the decoy peak nearer the starting
  corner than the global one.

Say in one sentence what got harder and why that is the interesting case. Then
hand over the URL and stop, exactly as in Step 3.

## When Not to Build a Game

**Before deciding a concept has no game, check whether it contains one.** Most
concepts that do not map whole have a piece that does — offer that piece:

> Diffusion has two halves and I can only game one. The denoising loop I would
> have to just explain — but the Transformer half is attention over image
> patches, and I can put you inside that. Want it?

Backprop → the update step (`parameter_control`). CNNs → routing patches to
feature detectors (`route_and_sort`). RAG → routing a query to chunks
(`route_and_sort`). Diffusion transformers → attention over patches
(`predict_and_verify`). Naming which half is a game and which is prose is a
better answer than refusing the whole thing.

Only two templates from the project plan are missing: `race_algorithm` and
`build_and_test`. Sorting races, algorithm comparison and network architecture
design have no engine. Say so plainly and teach those directly.

Never bend a concept onto an engine that misrepresents it — but "does not map"
is a high bar, and a tradeoff, a threshold, a distribution, a search under
budget or a routing decision all map. Concepts with no interactive core at all
— history, naming, why a paper mattered — are always prose.

## Constraints

- **Never write HTML, CSS or JavaScript.** The engines are done. Your entire
  output surface is one JSON object.
- **Never invent a URL.** Only ever paste one that `--serve` printed.
- **Never explain the concept before they play.** Steps 1 and 3 are pitch and
  handover; the teaching happens in Step 4.
- **Never claim a game exists for `race_algorithm` or `build_and_test`.** Every
  other mechanic in `concept_to_template.md` is built and working.
- **At most 2 sentences** in Step 1 and Step 3. The game is the interface.
- **Always `clarify` for the choices** — never a numbered list in your prose,
  and never both.
- Never narrate the machinery: no "let me generate", no "calling the script",
  no mention of GAME_DATA, templates or this skill.

## Common Pitfalls

1. **Pitching the concept instead of the mechanic.** "You'll learn how MoE
   routing works" tells them nothing about what they are about to do.
2. **Explaining before they play.** The insight text is written to land after
   the game. Saying it first is the single most expensive mistake here.
3. **Authoring GAME_DATA from memory of this file.** Read the format guide. The
   placeholder names and required fields are exact.
4. **Using a placeholder the engine doesn't fill.** It renders as literal
   `{braces}` on screen. Each template's list is in the format guide.
5. **`temp` left at 1 in `predict_and_verify`.** The distribution comes out
   nearly flat and the game teaches nothing. 6–7 for unit-ish vectors.
6. **A single `quad` landscape in `parameter_control`.** It converges from
   everywhere, so "where you start matters" never shows. Add a `sin`.
7. **Claiming precision/recall or exploration/exploitation has no game.** Both
   are built — `balance_tradeoff` and `explore_grid`, each with cached GAME_DATA.
8. **Separable classes in `balance_tradeoff`.** If every positive scores above
   every negative, a perfect threshold exists and the game disproves its own
   lesson. At least one negative must outrank a positive.
9. **One peak in `explore_grid`.** With nothing to be lured by, there is no
   exploration dilemma and every playthrough "finds the optimum".
10. **Fewer than 3 destinations in `route_and_sort`.** The compute-saving
   arithmetic only reads as a saving with enough destinations — use 6–8 when the
   point is efficiency.
11. **Switching templates to dodge a validation error.** Read stderr; it names
   the field.
12. **Rebuilding by editing the template.** Difficulty lives in the data.

## Verification Checklist

- [ ] Template chosen from `concept_to_template.md`, not from memory
- [ ] Format guide read before any GAME_DATA was authored
- [ ] The pitch described what the player does, in ≤2 sentences
- [ ] `clarify` offered the three options; nothing was built before they picked
- [ ] A cached GAME_DATA was used when one matched the topic
- [ ] The URL pasted came from `--serve`, on its own line, as a link
- [ ] No part of the concept was explained before they played
- [ ] Follow-up `clarify` came after play, not instead of it
- [ ] "Make it harder" changed data only, and produced a new URL
- [ ] A concept that did not map whole was decomposed before being refused
- [ ] Only `race_algorithm` and `build_and_test` were described as missing
- [ ] Unbuildable concepts got an honest explanation, not a bent game

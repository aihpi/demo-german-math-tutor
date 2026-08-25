# Teaching Games — demo script

**Every number here is derived from the shipped GAME_DATA, not from the project
plan.** Where the plan and this file disagree, this file is right — the plan was
written before the games existed. Re-derive after changing any
`tested_gamedata/*.json`:

```bash
python3 scripts/demo_numbers.py
```

---

## Before you start

- Hermes **desktop app** (the preview rail does not exist in the terminal)
- Skill symlinked and the app restarted since the last edit
- `hermes skills list` shows `teaching-games` as `enabled`
- Branch `teaching-games` checked out — the skill directory does not exist on `main`

---

## Round 1 — MoE routing (5 min)

> "Teach me how MoE routing works."

Agent pitches the mechanic, offers **Let's go / Different angle / Just explain it**.
Click **Let's go**.

### Timing, and where the silence is

`delegate_task` **blocks the parent until every child returns** — it buys
concurrency, not the ability to talk over a render. So the agent teaches in
words *first*, then delegates the animation and the game in one call, then
presents. Measured on this box:

| | |
|---|---|
| animation, authored + rendered at 480p15 | 16 s |
| game, authored + served | 24 s |
| **sequential** | **40 s** |
| **both delegated in one call** | **23 s** — 42% less |

Parallel total ≈ the slower job alone, so two concurrent inference calls to the
same endpoint cost nothing measurable in throughput.

The 20–30 s after the delegation call **is** dead air. Fill it before, not
during: the agent should give the whole plain-language explanation ahead of the
call, so the wait lands after the audience already understands the idea and is
waiting to *see* it confirmed. Rehearse that sentence order.

> **PRESENTER TIP:** while the batch runs, the Hermes `/agents` overlay shows a
> live subagent tree. Leave it on screen for a beat — two agents working in
> parallel on one desktop box is part of the point. Don't narrate it; just let
> it be visible.

**The game: 8 experts, not 3.** Math, Language, Logic, Code, Science, Creative,
Facts, Translation. 12 tokens per round drawn from a pool of 40.

> ⚠️ The original plan said three experts. It is eight, and that matters: with
> three boxes, "2.3 experts per token" is *bad routing*, not a saving. With
> eight it is the point of the demo. Do not quote three on stage.

What the end screen will say, depending on how you play:

| your average | what the game reports |
|---|---|
| 1.0 experts/token (clean round) | **88% less compute** |
| 1.3 experts/token (a few misclicks) | **84% less compute** |
| 2.3 experts/token (top-2 territory) | **71% less compute** |

The line to land: a dense model runs all 8 every time; real MoE gates to about
two. Your 1.3 is *tighter* than production top-2 routing, which is the joke —
the gating network is doing this thousands of times a second and it is allowed
to be less decisive than you are.

Then click **Make it harder** → 14 tokens, faster spawn (2.6 vs 1.6), and **6
deliberately ambiguous tokens** with dashed blue borders — `numpy.linalg.solve(A,b)`
accepts Math *or* Code, `prove by induction` accepts Math *or* Logic. Either
answer scores. That ambiguity is where real MoE uses soft top-k routing.

## Round 2 — precision vs recall (4 min)

> "Now teach me about precision vs recall."

**The game:** 14 emails, 7 spam and 7 real, each scored 0–1. Slider from 0.05 to
0.95, starting at 0.50.

**The classes overlap on purpose.** `Invoice #4471 from Acme` (real) scores 0.66,
above two actual spam messages. So:

- **Best achievable F1 is 0.875, at threshold 0.41** — precision 78%, recall 100%
- There is **no perfect threshold**. That is the entire lesson, and it only works
  because the data overlaps.

Drag to both extremes on stage: low threshold catches all the spam and bins your
boss's invoice; high threshold keeps the inbox honest and lets scams through.

Closing line: which error is worse is not a maths question. A bank and a mailing
list tune this differently.

## Round 3 — audience choice (4 min)

Ask the room. Covered mechanics, with a cached round ready for each:

| if they shout | engine |
|---|---|
| gradient descent, learning rate, optimizers | `parameter_control` |
| attention, transformers, next-token, temperature | `predict_and_verify` |
| overfitting, regularization, quantization, bias/variance | `balance_tradeoff` |
| hyperparameter search, bandits, A/B testing | `explore_grid` |
| KV cache, load balancing, RAG retrieval, tokenizers | `route_and_sort` |

Not covered: sorting races, algorithm comparison, architecture design. The skill
will say so and explain in prose — that is correct behaviour, not a failure.

**If gradient descent comes up** (the likeliest), the numbers are:

| learning rate | what happens |
|---|---|
| 0.001 | still crawling after 400 steps — "too small" made visible |
| **0.1** | converges to θ = 2.753 in **26 steps** |
| 1.0 | oscillates forever, never settles |

Start the ball at 3.0. Land on 0.1 last so the round ends on a convergence.

## Wrap-up (2 min)

Three games, three different engines, generated live on the Spark. Engines by
Claude Code, content by the local model. Repo is open.

---

## Safety net

`--author` retries invalid JSON twice, feeding the parser error back each time,
then silently serves a cached round. Provenance goes to **stderr only**, so a
fallback looks identical on stage:

```bash
python3 skills/teaching-agent/scripts/generate_game.py --author "MoE routing" --serve
```

All three demo concepts resolve to a cached round, so **the demo survives the
model being completely unreachable.** Verified with the endpoint refused: three
failed attempts, then `moe_routing.json`, then a playable game.

## If something breaks

| symptom | do this |
|---|---|
| rail shows nothing | the second output line is a plain browser link — click that |
| game looks squished | it is built for 290–610px; if it is worse, widen the rail |
| agent says it has no game for a covered topic | a doc is stale; `python3 tests/test_templates.py` |
| authoring hangs | it retries twice at up to 180s each — wait, or `--retries 0` |

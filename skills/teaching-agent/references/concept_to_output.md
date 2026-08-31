# Concept → output mode

Decide this **first**, before picking any template. There are two ways to teach
a concept and they carry different kinds of understanding.

| mode | what happens | teaches |
|---|---|---|
| **WATCH** | a Manim animation renders and plays in the chat | *shape* — the scale of a gap, a sequence, a proportion |
| **PLAY** | an interactive HTML game opens in the preview rail | *consequence* — what happens when you choose wrong |

## The test

**Ask: is there a decision the learner can get wrong?**

- **Yes → PLAY.** Routing a token, setting a threshold, picking a learning rate,
  spending a search budget. The learner's mistake is the lesson; a video cannot
  deliver it because nothing is at stake.
- **No, but there is a magnitude or an order to see → WATCH.** 16 nodes firing
  against 3. One token at a time against six at once. There is nothing to decide,
  only something to notice — and noticing it takes five seconds of animation
  rather than a paragraph.
- **Both → WATCH, then PLAY.** See the shape, then live inside it. This is the
  strongest sequence and the default for anything on the demo path.

## WATCH first, always

When doing both, the animation comes first. It costs ~40 s of wall clock and
gives the learner a mental picture to play against; the game then has something
to attach to. Reversing it wastes the animation — after playing, they already
know the shape.

## By concept

**WATCH only** — a magnitude or a sequence, nothing to decide:
dense vs MoE parameter counts · autoregressive vs diffusion decoding · CPU vs GPU
core counts · quantized vs full-precision size · batch 1 vs batch 8 utilisation ·
cache hit vs miss latency · sequential vs parallel loading · model size
comparisons · before/after any optimisation

**PLAY only** — a decision with a wrong answer, no interesting magnitude:
attention weights · next-token probability · softmax and temperature · embedding
similarity · exploration vs exploitation · hyperparameter search · A/B testing ·
bandits

**Both** — worth seeing *and* worth doing. **This list is short on purpose:**
`comparison_split` is the only animation template and it shows two grids of
nodes with two counters. A concept earns a WATCH only if that is genuinely its
shape.

| concept | WATCH shows | PLAY makes them do |
|---|---|---|
| moe routing | 16 experts firing vs 3 | route tokens under time pressure |
| kv cache | 16 blocks recomputed vs 3 reused | classify what can be reused |
| gradient descent | a ball settling in the nearest valley | choose the learning rate |
| overfitting | train and validation error separating | slide model complexity |

**Everything else on this page is single-mode**, however tempting a second mode
sounds. Precision vs recall is two curves over a *slider position*, which
neither template draws. Forcing a concept through the wrong engine renders a
picture that contradicts the lesson.

Two animation templates exist and they answer different questions:
`comparison_split` for **how many of these versus those**, `curve_plot` for
**what shape does this take over a range**.

**Neither** — history, naming, why a paper mattered, what a library is called.
Answer in prose. Not everything wants a picture.

**A historical question outranks decomposition.** "Teach me backprop" is a
mechanism, and the update step is a game. "Teach me *the history of* backprop"
is a question about people and dates — answer that first, briefly, and *then*
offer the mechanism. Decomposition exists for concepts that do not map, not as a
way to avoid answering what was asked.

## Delegation patterns

`delegate_task` blocks until every child returns, so it buys concurrency, not
the ability to talk while they work. Teach first, delegate once, present in
order.

### Both modes — one call, two tasks

Send them together. Wall time is the slower child (~45 s), not the sum (~60 s).

| concept | WATCH | PLAY |
|---|---|---|
| moe routing | `comparison_split` | `route_and_sort` |
| kv cache | `comparison_split` | `route_and_sort` |
| gradient descent | `curve_plot` | `parameter_control` |
| overfitting | `curve_plot` | `balance_tradeoff` |

Only two concepts genuinely have both today, because `comparison_split` is the
only animation template. Everything else is single-mode.

### PLAY only — one task

precision vs recall (`balance_tradeoff`) · attention (`predict_and_verify`) ·
next-token probability (`predict_and_verify`) · hyperparameter search
(`explore_grid`) · A/B testing (`explore_grid`)

### WATCH only — one task

**`comparison_split`** — autoregressive vs diffusion decoding · CPU vs GPU cores ·
quantized vs full-precision · batch 1 vs batch 8 · anything that is purely
*this against that* with no decision in it.

**`curve_plot`** — convergence vs divergence · scaling laws · learning-rate
schedules · loss curves over training · any *shape over a range*.

### What does not exist

There are **two** animation templates: `comparison_split` (counts) and
`curve_plot` (shapes over a range). A concept needing an architecture
walkthrough, a denoising sequence or items flowing through stages has no
template, so do not delegate one — use whichever of the two genuinely fits, and
prose otherwise.

## Cached scenes

`scene_data/index.json` lists SCENE_DATA that has been rendered and checked. Use
one verbatim when the topic matches; `render_scene.py --author` falls back to
them automatically when live generation fails.

| topic | file |
|---|---|
| dense vs MoE, expert activation | `dense_vs_moe.json` |
| autoregressive vs diffusion decoding | `ar_vs_diffusion.json` |

## When a concept does not fit

Only one animation template exists: `comparison_split`, and it only does *this
versus that*. A concept with no two-way comparison in it — a single process, a
taxonomy, a proof — has no WATCH mode. Say so and go to PLAY, or to prose.

Do not force a comparison that is not there. Two panels showing the same thing
teaches less than one honest sentence.

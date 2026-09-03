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
Three animation templates exist — `comparison_split` (two grids of nodes with
two counters), `curve_plot` (one or two curves over a range) and `pipeline_flow`
(one item moving through named stages). A concept earns a WATCH only if one of
those is genuinely its shape.

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

Three animation templates exist, answering different questions:
`comparison_split` for **how many of these versus those**, `curve_plot` for
**what shape does this take over a range**, `pipeline_flow` for **what happens
in what order**.

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

Few concepts genuinely have both. Most are single-mode: a shape to see, or a
choice to make, rarely both.

### PLAY only — one task

precision vs recall (`balance_tradeoff`) · attention (`predict_and_verify`) ·
next-token probability (`predict_and_verify`) · hyperparameter search
(`explore_grid`) · A/B testing (`explore_grid`)

### WATCH only — one task

**`comparison_split`** — *how many of these versus those.*
ML: autoregressive vs diffusion decoding · CPU vs GPU cores · quantized vs
full-precision · batch 1 vs batch 8.
Elsewhere: chromosome counts in mitosis vs meiosis · energy per kWh from coal vs
solar · two national budgets · army or population sizes in history · calories in
two meals · before and after any optimisation.

**`pipeline_flow`** — *what happens, in what order, and what it becomes.*
ML: tokenise → embed → attend → predict · a RAG lookup · a training loop ·
a diffusion sampling loop · a data-preprocessing chain.
Elsewhere: the water cycle · photosynthesis · digestion · the rock cycle ·
the nitrogen cycle · protein synthesis (DNA → RNA → protein) · a legislative
bill becoming law · a manufacturing line · order → payment → dispatch.

**`curve_plot`** — *what shape does this take over a range.*
ML: convergence vs divergence · scaling laws · learning-rate schedules · loss
curves over training.
Elsewhere: supply and demand crossing · logistic vs exponential population
growth · radioactive decay · projectile trajectories · enzyme kinetics ·
dose–response curves · compound interest · reaction rate against temperature ·
risk against return.

### What does not exist

There are **three** animation templates: `comparison_split` (counts),
`curve_plot` (shapes over a range) and `pipeline_flow` (a process with stages).
A concept needing a spatial architecture walkthrough or a progressive
denoising reveal still has no template — use whichever of the three genuinely
fits, and prose otherwise.

## Cached scenes

`scene_data/index.json` lists SCENE_DATA that has been rendered and checked. Use
one verbatim when the topic matches; `render_scene.py --author` falls back to
them automatically when live generation fails.

| topic | file |
|---|---|
| dense vs MoE, expert activation | `dense_vs_moe.json` (comparison_split) |
| autoregressive vs diffusion decoding | `ar_vs_diffusion.json` (comparison_split) |
| gradient descent, learning rate, convergence | `gradient_descent_walk.json` (curve_plot) |
| overfitting, train vs validation, bias/variance | `overfitting_curves.json` (curve_plot) |
| how a transformer works, tokenise → predict | `transformer_pipeline.json` (pipeline_flow) |
| the water cycle | `water_cycle.json` (pipeline_flow) |

## When a concept does not fit

The three templates cover counts, curves and sequences. A concept that is none
of those — a spatial architecture, a taxonomy, a proof — has no WATCH mode. Say
so and go to PLAY, or to prose.

Do not force a comparison that is not there. Two panels showing the same thing
teaches less than one honest sentence.

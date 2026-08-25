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

**Both** — worth seeing *and* worth doing:

| concept | WATCH shows | PLAY makes them do |
|---|---|---|
| MoE routing | 16 experts firing vs 3 | route tokens under time pressure |
| precision vs recall | the two metrics moving apart | pick the threshold and eat the errors |
| gradient descent | the ball converging vs diverging | choose the learning rate |
| overfitting | train and test error separating | slide model complexity |
| KV cache | full recompute vs prefix reuse | classify what can be reused |

**Neither** — history, naming, why a paper mattered, what a library is called.
Answer in prose. Not everything wants a picture.

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

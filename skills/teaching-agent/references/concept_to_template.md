# Concept → template

Five engines exist. Pick by **what the player has to do**, not by subject area.

| If understanding the concept means… | template |
|---|---|
| deciding *which* of several specialists should handle each thing | `route_and_sort` |
| turning one knob and living with what it does | `parameter_control` |
| committing to a guess before the truth is revealed | `predict_and_verify` |
| accepting that helping one number hurts another | `balance_tradeoff` |
| spending a limited budget to find something hidden | `explore_grid` |

**The engines are not about machine learning.** Each one is a *shape of
understanding*, and every subject has those shapes. A taxonomy is a routing
problem; a diagnostic threshold is a tradeoff; a dig site is a search under
budget. Pick by the shape, then dress it in the learner's subject.

## Fast lookup

**`route_and_sort`** — *this thing belongs in one of those places.*
ML: MoE / expert routing · load balancing · sharding · cache placement ·
tokenization · triage.
Elsewhere: biological taxonomy (vertebrate classes, kingdoms) · organelles to
their functions · elements to periodic groups · parts of speech · verb tenses ·
rock types · climate zones · blood typing · symptoms to body systems · waste
sorting · library classification · expense categories · instruments to families.

**`parameter_control`** — *one knob, and you live with what it does.*
ML: gradient descent and ascent · learning-rate scheduling · momentum ·
simulated annealing · local vs global optima.
Elsewhere: finding a molecule's lowest-energy shape · a physical system settling
to equilibrium · profit maximisation against price · drug dosage titration ·
tuning a PID gain · a ball in a potential well · any "search for the bottom of
something" in physics, chemistry or economics.

**`balance_tradeoff`** — *helping one number hurts another.*
ML: precision vs recall · overfitting · bias vs variance · regularization ·
quantization · latency vs quality.
Elsewhere: a medical test's sensitivity vs specificity · burden of proof
(wrongful conviction vs wrongful acquittal) · safety factor vs cost in
engineering · strength vs weight in materials · inflation vs unemployment ·
conservation vs development · airport security friction vs risk · speed vs
accuracy in any human task.

**`explore_grid`** — *something is hidden and your budget runs out first.*
ML: exploration vs exploitation · hyperparameter search · bandits · Bayesian
optimization · A/B testing · active learning.
Elsewhere: choosing where to excavate an archaeological site · which compounds
to screen in drug discovery · where to drill · which marketing channels to test ·
an animal choosing foraging patches · which diagnostic tests to order ·
prospecting, polling, and sampling of any kind.

**`predict_and_verify`** — *commit to a guess, then see the truth.*
ML: attention weights · next-token probability · temperature and top-p ·
softmax · logits vs probabilities · calibration · embedding similarity.
Elsewhere: Punnett-square offspring ratios · allele frequencies · dice and card
probabilities · which word most people say next · diagnostic likelihoods given a
symptom · election or weather forecasts · anywhere the lesson is "your intuition
about this distribution is wrong".

## The decision tree

1. Is there a **distribution** the player can be wrong about, where seeing the
   true one is the lesson? → `predict_and_verify`.
1a. Are there **two numbers that cannot both be maximised**? → `balance_tradeoff`.
1b. Is something **hidden**, with a **budget** that runs out before you can
   check everywhere? → `explore_grid`.
2. Is there **one continuous number** whose too-high and too-low behaviour are
   both instructive? → `parameter_control`.
3. Is the concept about **assigning things to places**? → `route_and_sort`.
4. None of the above → **do not force it**. See below.

## Decompose before you refuse

A concept that does not map as a whole often **contains** a piece that does.
Offer that piece rather than falling back to pure prose:

> Diffusion has two halves and I can only game one. The denoising loop I would
> have to just explain — but the Transformer half is attention over image
> patches, and I can put you inside that. Want it?

Backprop → the update step (`parameter_control`). CNNs → routing patches to
feature detectors (`route_and_sort`). RAG → routing a query to chunks
(`route_and_sort`). Diffusion transformers → attention over patches
(`predict_and_verify`). Name honestly which half is a game and which is prose.

## Not everything is a game

`race_algorithm` and `build_and_test` are named in the project plan but **are
not built**. Do not attempt to fake them with an existing engine. If a concept
needs one — sorting races, algorithm comparison, network architecture design —
say so plainly and explain the concept directly instead:

> That one is a tradeoff between two things I can't put in any of the games I
> have. Let me just show you the shape of it.

A clear explanation beats a game that misrepresents the concept. Concepts with
no interactive core at all — the history of a technique, what a library is
called, why a paper mattered — should always be answered in prose.

## Reaching for a cached round

`tested_gamedata/` holds GAME_DATA that has been played and checked. Use one
verbatim when the topic matches:

| topic | file | template |
|---|---|---|
| MoE routing | `moe_routing.json` | `route_and_sort` |
| MoE routing, harder | `moe_routing_hard.json` | `route_and_sort` |
| ticket / email triage | `email_triage.json` | `route_and_sort` |
| gradient descent | `gradient_descent.json` | `parameter_control` |
| policy gradient, reward | `gradient_ascent_reward.json` | `parameter_control` |
| attention | `attention_weights.json` | `predict_and_verify` |
| next-token probability | `next_word_probability.json` | `predict_and_verify` |
| precision vs recall | `precision_recall.json` | `balance_tradeoff` |
| bias vs variance, overfitting | `bias_variance.json` | `balance_tradeoff` |
| hyperparameter search | `hyperparameter_hunt.json` | `explore_grid` |
| A/B testing, bandits | `ab_testing.json` | `explore_grid` |

A cached file is a known-good round. Anything else, you author — see
`gamedata_format_guide.md`.

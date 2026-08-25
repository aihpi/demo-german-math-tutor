# Concept → template

Three engines exist. Pick by **what the player has to do**, not by subject area.

| If understanding the concept means… | template |
|---|---|
| deciding *which* of several specialists should handle each thing | `route_and_sort` |
| turning one knob and living with what it does | `parameter_control` |
| committing to a guess before the truth is revealed | `predict_and_verify` |

## Fast lookup

**`route_and_sort`** — MoE / expert routing · load balancing · sharding and
partitioning · classification into >2 classes · cache placement (L1/L2/RAM/disk)
· scheduling work onto workers · tokenization into vocabulary buckets ·
attention heads specializing · triage of any kind

**`parameter_control`** — gradient descent · gradient ascent and policy gradients
· learning-rate scheduling · momentum · simulated annealing · any optimizer ·
hill climbing · convergence and divergence · local vs global optima

**`predict_and_verify`** — attention weights · next-token probability ·
temperature and top-p sampling · softmax itself · logits vs probabilities ·
calibration and confidence · class scores · embedding similarity · anything
where the lesson is "your intuition about this distribution is wrong"

## The decision tree

1. Is there a **distribution** the player can be wrong about, where seeing the
   true one is the lesson? → `predict_and_verify`.
2. Is there **one continuous number** whose too-high and too-low behaviour are
   both instructive? → `parameter_control`.
3. Is the concept about **assigning things to places**? → `route_and_sort`.
4. None of the above → **do not force it**. See below.

## Not everything is a game

`balance_tradeoff`, `race_algorithm` and `build_and_test` are named in the
project plan but **are not built**. Do not attempt to fake them with an existing
engine. If a concept needs one of these — precision/recall, bias/variance,
quantization, exploration/exploitation, sorting races, network architecture —
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

A cached file is a known-good round. Anything else, you author — see
`gamedata_format_guide.md`.

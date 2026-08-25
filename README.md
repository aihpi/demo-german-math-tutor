<div style="background-color: #ffffff; color: #000000; padding: 10px;">
<img src="00_aisc/img/logo_aisc_bmftr.jpg">
<h1>Math Tutor — a Hermes Agent skill</h1>
</div>

An interactive math tutor that runs inside [Hermes Agent](https://github.com/NousResearch/hermes-agent).
It pulls a word problem from GSM8K, retells it as a story, and then walks the
student through it **one step at a time** — every step is a multiple-choice
question rendered as clickable options, where the wrong answers are real student
misconceptions rather than obvious nonsense.

Built for the NVIDIA Dev Day demo at GTC. Speaks English and German.

## Features

- **Figures that draw themselves.** Geometry renders as SVG whose lines animate
  into place — the two equal sides first, then the base closing underneath.
  Plain CSS inside the SVG, so no video, no renderer, no extra dependency.
- **Watch the problem get written.** The session opens with the raw GSM8K row on
  screen, three worlds to choose from, and the same mathematics retold in the one
  the audience picks — numbers and units intact, everything else invented.
- **You do the arithmetic.** Each step is two asks: pick the approach from the
  buttons, then type the number it gives. The tutor withholds the result until
  you have computed it — a wrong number gets a nudge about what it would have
  meant, never the right answer.
- **Guided solving, not answers.** The tutor never states the result before the
  student has worked through the final step.
- **Distractors that bite.** Wrong options come from misreading a constraint,
  picking the wrong operation, or answering a different question — the kind of
  mistake an audience recognises.
- **Deterministic grading, live reasoning.** The choice strings and the verdict
  live in `tutor_session.py`; every word of explanation is generated fresh. The
  same pick always gets the same verdict — and never the same sentence.
- **Wrong answers get followed through.** Not "incorrect", but what you were
  probably thinking, what number that approach produces, and why that number is
  impossible for this problem.
- **Answer or ask in your own words.** Type into clarify's "Other" row: a
  question ("warum kann ich nicht zuerst teilen?") gets answered and the step
  re-asked; an answer in your own words is mapped onto a choice and graded, so
  you never have to hunt for the matching button. The model does the mapping,
  the script still decides whether it was right.
- **Native choice UI.** Uses the Hermes `clarify` tool: an arrow-key panel in the
  TUI, inline keyboard buttons on Telegram.
- **Bilingual.** `/math-tutor de` runs the whole session in German.
- **Offline dataset.** All 7,473 GSM8K training problems are cached in the repo.

## Setup

### Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed (`~/.hermes`)
- Python 3.10+
- Access to a `gemma-4-31b` endpoint — currently the KISZ LiteLLM proxy at
  `https://api.aisc.hpi.de/`

### Surfaces

|  | clarify | LaTeX | inline diagrams |
|---|---|---|---|
| `hermes chat` | arrow-key panel | no | no — Unicode figures |
| `hermes desktop` | buttons | yes | yes, with `gui` |

The terminal has no image support at all, so geometry falls back to Unicode
figures. The desktop app renders clarify as buttons and typesets LaTeX, but its
markdown renderer rejects `data:` image URIs and its `hermes-media://` scheme
serves audio and video only. The one route left is a loopback http origin, so
`--render svg` writes the diagram to a temp directory and serves it from
`127.0.0.1:8731`, starting the server on first use. Add `gui` to the slash
command there.

### Quick Start

```bash
bash scripts/setup.sh
```

This links `skills/math-tutor` into `~/.hermes/skills/` and builds the dataset
cache if it is missing. Then add the two clarify timeouts from
[`config/hermes_config.yaml`](config/hermes_config.yaml) to `~/.hermes/config.yaml`
— **both** of them; the TUI and the Telegram gateway read different keys, and the
TUI default of 120 seconds will cut a live demo short.

```bash
hermes chat
```

Then in the TUI:

```
/reload-skills
/math-tutor demo
```

## User Guide

| Command | What it does |
|---|---|
| `/math-tutor` | Random problem from the full GSM8K cache |
| `/math-tutor demo` | Random problem from the curated demo set — **use this on stage** |
| `/math-tutor hard` | A random MATH geometry problem — 97 cached, Level 1-3 |
| `/math-tutor hard gui` | Same, with real SVG diagrams — desktop app only |
| `/math-tutor topic:fractions` | `arithmetic`, `fractions`, `percentages`, or `rates` |
| `/math-tutor de` | Whole session in German; combines, e.g. `demo de` |

### Recommendations

Use `demo` when presenting. Those four problems are hand-picked for short
solution paths and a tempting wrong turn on the first step, and each carries a
pre-written German version so the bilingual demo does not depend on live
translation quality.

Run `demo` first, then `hard` — accessible problem, then real difficulty, same
scaffolding. Let the room pick the world in the first step — that is the moment the raw
dataset row becomes a story, live. Then miss a step on purpose: the tutor follows
your wrong approach through to the number it produces and says why that number
is impossible. Those two beats are what separate this from a quiz app.

## Layout

```
skills/math-tutor/SKILL.md          the tutor itself — the actual deliverable
skills/math-tutor/tutor_session.py  session state: serves choices, grades picks
skills/math-tutor/figures.py        draws geometry as animated SVG
skills/math-tutor/gsm8k_loader.py   problem sampling, also usable standalone
data/gsm8k_cache.jsonl              7,473 problems, parsed and topic-tagged
data/math_cache.jsonl               97 MATH geometry problems, diagram-free
data/hard_problems.json             route overlay for the curated MATH problem
data/demo_problems.json             curated set: German text + pre-written routes
scripts/build_gsm8k_cache.py   rebuilds the cache from upstream (run once)
config/hermes_config.yaml      reference config, documents both clarify timeouts
```

## Limitations

- **Not yet offline.** Inference runs through the LiteLLM proxy. Local vLLM on
  the DGX Spark is a TODO (see below), and until then the demo needs network.
- **Only the curated problems ship a written route** (the choice strings, not
  the explanations). For the other 7,469 the model authors the choices once per
  session, so their quality varies with the model. `/math-tutor demo` never does
  this.
- **No visual explanations.** Manim animations were scoped out for now.
- The `hard` track samples 97 MATH geometry problems. That is what survives two
  filters: Level 1-3 (4-5 overrun a demo slot) and no Asymptote diagram — 40% of
  MATH geometry ships a picture that is required to solve it and cannot be
  rendered here. One problem carries a hand-written route; the rest are broken
  into steps by the model at runtime, so their quality varies with the model.
- Figures cover triangles, circles and rectangles, roughly 66% of that set.
  Angle, coordinate and solid problems run without a picture by design.
- **The TUI cannot display images.** No sixel, no kitty protocol — `image_generate`
  only returns a path. For geometry, run the demo in the **desktop app**
  (`hermes desktop`), which renders clarify as buttons and markdown images
  inline, offline. In the terminal the same figures fall back to Unicode.


## TODO

- [ ] Local inference on the DGX Spark (vLLM, `gemma-4-31b`) — swap `base_url`
      in `custom_providers`, nothing else changes
- [ ] Verify the tutor flow on Telegram (inline keyboard buttons)
- [ ] Decide on Manim animations for 2–3 problem types
- [ ] Model swap test against Soofi S

## References

- [GSM8K](https://github.com/openai/grade-school-math) — the dataset
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [KI-Servicezentrum Berlin-Brandenburg](https://hpi.de/kisz)

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements
<img src="00_aisc/img/logo_bmftr_de.png" alt="drawing" style="width:170px;"/>

The [AI Service Centre Berlin Brandenburg](http://hpi.de/kisz) is funded by the [Federal Ministry of Research, Technology and Space](https://www.bmbf.de/) under the funding code 16IS22092.

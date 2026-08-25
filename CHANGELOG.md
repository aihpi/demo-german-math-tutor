# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

## [0.1.0] - 2026-08-24

### Added
- `math-tutor` Hermes skill: guided GSM8K problem solving via the clarify tool,
  English and German.
- GSM8K cache builder and sampling CLI.
- `tutor_session.py`: deterministic session state — the model authors a route
  once, the script serves the choices and grades every pick against them.
- Curated demo problem set with pre-written English and German routes, so the
  demo path generates no choices at all — explanations stay live.
- World picker: the session shows the raw GSM8K text, offers three settings, and
  rewrites the problem into the chosen one. Renamed nouns are substituted into
  the pre-written choices (with German dative forms) so the buttons follow the
  story without becoming model-authored.
- `hard` track: one MATH (Hendrycks) geometry problem, hand-decomposed into a
  three-step route in both languages. Abstract problems set `story: false` and
  skip the world picker rather than being restaged.
- Figures: a route step can carry a per-choice diagram, shown with the verdict.
  The trap pick on the geometry problem draws the degenerate triangle. Terminals
  get Unicode; `--render svg` serves a real SVG from a loopback http origin,
  which is the only image source the desktop app's markdown renderer accepts.
- `hard` track now samples 97 cached MATH geometry problems (Level 1-3,
  diagram-free). Problems shipping prose instead of steps are decomposed by the
  model into 3-5 asks, each with its own calculation; the script still owns the
  choices and the grading.
- `scripts/build_math_cache.py`, with brace-matched `\boxed` extraction so
  nested answers like `\frac{17}{2}` are not truncated.
- `figures.py`: draws triangles, circles and rectangles from their dimensions as a self-animating SVG,
  and refuses to draw an impossible one. The model picks the shape and numbers;
  the script does the geometry.
- Choice order is shuffled per session, seeded by session id. Hand-written
  routes were 28/28 correct-at-position-1 and the model authors the same way;
  now position carries no information. Figures move with their choice.
- Two beats per step: the student picks the approach, then computes the number.
  `compute` grades the arithmetic exactly, withholds the expected value from the
  model until it is answered, and escalates the hint on a second miss. Steps with
  no obvious single result skip the beat rather than ask for an unverifiable one.
- Free-form input: typing into clarify's "Other" row is either answered as a
  question or, with `answer --as N`, mapped onto a choice and graded like a tap
  — so a correct answer typed in your own words advances the step. Mapping is
  the model's job, grading stays the script's.

### Removed
- Unused project-template scaffolding (frontend/backend Dockerfiles,
  `docker-compose.yml`, notebook template).

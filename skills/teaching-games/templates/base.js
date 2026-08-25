/*
  base.js — shared runtime for every teaching-games template.

  Not standalone. generate_game.py inlines it wherever a template writes:

      /*__BASE_JS__* /            (without the space)

  It reads GAME_DATA.customization, fills in defaults for every absent field,
  and exposes one object, TG, that the engines call. An engine must never read
  GAME_DATA.customization directly — go through TG so defaults stay in one place.
*/
const TG = (() => {
  const D = {
    theme: { accent: "#FF7500", secondary: "#4A9EFF", success: "#50C878", error: "#FF4444",
             background: "#1a1a1a", surface: "#252525", particleEffect: "sparks" },
    sounds: { enabled: true, correct: "chirp", wrong: "buzz", complete: "fanfare" },
    difficulty: { mode: "adaptive", startLevel: 1, maxLevel: 5, adaptiveThreshold: 0.8 },
    titleScreen: { emoji: "", flavor: "", instructions: "", showTimer: false, showScore: true, showStreak: true },
    endScreen: { grading: [{ min: 90, emoji: "🏆", label: "Expert!" },
                           { min: 70, emoji: "🎯", label: "Getting there!" },
                           { min: 50, emoji: "💪", label: "Keep practicing!" },
                           { min: 0,  emoji: "🌱", label: "Just getting started!" }],
                 shareText: "", showReplayButton: true, showNewConceptButton: false },
    animations: { speed: "normal", transitions: "slide", itemEntrance: "drop", celebrationIntensity: 3 },
    layout: { canvasWidth: 700, canvasHeight: 450, orientation: "landscape", mobileOptimized: true },
    multiplayer: { enabled: false, mode: "competitive", showLeaderboard: true,
                   players: [], playerColors: ["#FF7500", "#4A9EFF", "#50C878", "#FF4444", "#FFD700"] },
  };

  // Only plain objects merge; arrays and scalars are replaced wholesale, so an
  // author who supplies `grading` replaces the ladder instead of half-patching it.
  const isObj = v => v && typeof v === "object" && !Array.isArray(v);
  const merge = (base, over) => {
    const out = { ...base };
    for (const k in (over || {})) out[k] = isObj(base[k]) && isObj(over[k]) ? merge(base[k], over[k]) : over[k];
    return out;
  };
  const C = merge(D, (typeof GAME_DATA !== "undefined" && GAME_DATA.customization) || {});

  /* ---- theme ---------------------------------------------------------- */
  const applyTheme = () => {
    const r = document.documentElement.style, t = C.theme;
    r.setProperty("--accent", t.accent);   r.setProperty("--blue", t.secondary);
    r.setProperty("--green", t.success);   r.setProperty("--red", t.error);
    r.setProperty("--bg", t.background);   r.setProperty("--panel", t.surface);
    if (C.layout.mobileOptimized) document.documentElement.classList.add("touch");
    document.documentElement.classList.add("anim-" + C.animations.speed);
  };

  /* ---- sound: oscillators only, no assets ------------------------------ */
  let ac = null;
  const VOICES = {
    chirp:   [[880, 0], [1320, .06]],           ding:  [[1568, 0]],
    pop:     [[440, 0], [880, .04]],            chord: [[523, 0], [659, 0], [784, 0]],
    buzz:    [[150, 0], [120, .08]],            thud:  [[90, 0]],
    descend: [[440, 0], [330, .07], [247, .14]],
    fanfare: [[523, 0], [659, .1], [784, .2], [1047, .3]],
    tada:    [[784, 0], [1047, .12]],           calm:  [[392, 0], [523, .18]],
  };
  const tone = (f, at, dur, type) => {
    const o = ac.createOscillator(), g = ac.createGain(), t0 = ac.currentTime + at;
    o.type = type; o.frequency.value = f;
    g.gain.setValueAtTime(0, t0);
    g.gain.linearRampToValueAtTime(.18, t0 + .012);
    g.gain.exponentialRampToValueAtTime(.0001, t0 + dur);
    o.connect(g).connect(ac.destination); o.start(t0); o.stop(t0 + dur + .02);
  };
  const sfx = kind => {
    const name = C.sounds[kind] || kind;
    if (!C.sounds.enabled || !VOICES[name]) return;
    try {
      // Constructed on first play: browsers refuse an AudioContext before a gesture.
      ac = ac || new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === "suspended") ac.resume();
      const wave = /buzz|thud/.test(name) ? "square" : "sine";
      VOICES[name].forEach(([f, at]) => tone(f, at, .16, wave));
    } catch (e) { /* no audio on this surface; never break the game for it */ }
  };

  /* ---- particles ------------------------------------------------------- */
  const burst = (x, y, colour) => {
    const kind = C.theme.particleEffect;
    if (kind === "none" || C.animations.speed === "instant") return;
    const n = { 1: 4, 2: 7, 3: 11, 4: 16, 5: 22 }[C.animations.celebrationIntensity] || 11;
    if (kind === "ripple") {
      const r = document.createElement("div");
      r.className = "tg-ripple";
      r.style.cssText = `left:${x}px;top:${y}px;border-color:${colour || C.theme.accent}`;
      document.body.appendChild(r);
      return setTimeout(() => r.remove(), 620);
    }
    for (let i = 0; i < n; i++) {
      const p = document.createElement("div"), a = Math.random() * 6.28, d = 24 + Math.random() * 46;
      p.className = "tg-spark";
      p.style.cssText = `left:${x}px;top:${y}px;background:${
        kind === "confetti" ? C.multiplayer.playerColors[i % 5] : (colour || C.theme.accent)};`
        + `--dx:${Math.cos(a) * d}px;--dy:${Math.sin(a) * d}px;`
        + (kind === "confetti" ? "width:5px;height:8px;border-radius:1px;" : "");
      document.body.appendChild(p);
      setTimeout(() => p.remove(), 700);
    }
  };

  /* ---- difficulty ------------------------------------------------------ */
  const dif = {
    level: C.difficulty.startLevel,
    // Engines call this after each round/item with their running accuracy.
    report(accuracy, roundsDone) {
      const m = C.difficulty.mode, max = C.difficulty.maxLevel;
      if (m === "fixed") return this.level;
      if (m === "linear") this.level = Math.min(max, C.difficulty.startLevel + roundsDone);
      else if (m === "sudden") this.level = roundsDone >= 1 ? max : C.difficulty.startLevel;
      else if (accuracy >= C.difficulty.adaptiveThreshold) this.level = Math.min(max, this.level + 1);
      else if (accuracy < 0.4) this.level = Math.max(1, this.level - 1);
      return this.level;
    },
    // 1 at level 1 rising to ~2 at maxLevel — engines multiply their own knobs by this.
    scale() { return 1 + (this.level - 1) / Math.max(1, C.difficulty.maxLevel - 1); },
  };

  /* ---- players (local hot-seat) ---------------------------------------- */
  const mp = {
    on: C.multiplayer.enabled,
    names: C.multiplayer.players.length ? C.multiplayer.players.slice()
         : ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5"].slice(0, 2),
    scores: [], i: 0,
    reset() { this.scores = this.names.map(() => 0); this.i = 0; },
    current() { return this.names[this.i]; },
    colour() { return C.multiplayer.playerColors[this.i % C.multiplayer.playerColors.length]; },
    record(s) { this.scores[this.i] = s; },
    next() { this.i++; return this.i < this.names.length; },
    board() { return this.names.map((n, i) => ({ name: n, score: this.scores[i] || 0 }))
                               .sort((a, b) => b.score - a.score); },
  };

  /* ---- screens --------------------------------------------------------- */
  const grade = pct => (C.endScreen.grading.find(g => pct >= g.min) || { emoji: "", label: "" });
  const fill = (tpl, v) => (tpl || "").replace(/\{(\w+)\}/g, (m, k) => k in v ? v[k] : m);

  const title = (overlay, headline, body, onStart) => {
    const t = C.titleScreen;
    overlay.classList.remove("hide");
    overlay.innerHTML =
      (t.emoji ? `<div class="tg-emoji">${t.emoji}</div>` : "") +
      `<h2>${headline}</h2>` +
      (t.flavor ? `<p class="tg-flavor">${t.flavor}</p>` : "") +
      `<p class="insight">${t.instructions || body}</p>` +
      (mp.on ? `<p class="tg-flavor">Hot-seat: ${mp.names.join(" · ")}</p>` : "") +
      `<button class="primary" id="tgStart">Start</button>`;
    overlay.querySelector("#tgStart").onclick = () => { sfx("correct"); onStart(); };
  };

  const end = (overlay, opts) => {
    const { pct = 0, headline, insight, vals = {}, onReplay } = opts;
    const g = grade(pct);
    sfx("complete");
    overlay.classList.remove("hide");
    overlay.innerHTML =
      `<div class="tg-emoji">${g.emoji}</div>` +
      `<h2>${headline}</h2>` +
      (g.label ? `<p class="tg-flavor">${g.label}</p>` : "") +
      (mp.on && C.multiplayer.showLeaderboard
        ? `<table class="tg-board">${mp.board().map((r, i) =>
            `<tr><td>${i + 1}.</td><td>${r.name}</td><td>${r.score}</td></tr>`).join("")}</table>` : "") +
      `<p class="insight">${fill(insight, vals)}</p>` +
      (C.endScreen.shareText ? `<p class="tg-flavor">${fill(C.endScreen.shareText, vals)}</p>` : "") +
      (C.endScreen.showReplayButton ? `<button class="primary" id="tgAgain">Play again</button>` : "");
    const b = overlay.querySelector("#tgAgain");
    if (b) b.onclick = onReplay;
  };

  applyTheme();
  return { cfg: C, sfx, burst, dif, mp, title, end, grade, fill,
           ms: base => base * ({ slow: 1.6, normal: 1, fast: .6, instant: .01 }[C.animations.speed] ?? 1) };
})();

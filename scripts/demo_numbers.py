#!/usr/bin/env python3
"""Re-derive every figure in docs/demo_script.md from the shipped GAME_DATA.

Run after editing any tested_gamedata/*.json, then update the script to match.
"""
import json, math, pathlib

GD = pathlib.Path(__file__).resolve().parent.parent / "skills/teaching-games/tested_gamedata"
load = lambda n: json.loads((GD / n).read_text())

moe, hard = load("moe_routing.json"), load("moe_routing_hard.json")
n = len(moe["destinations"])
print("ROUND 1 — MoE")
print(f"  {n} experts: {', '.join(d['name'] for d in moe['destinations'])}")
print(f"  {moe['roundLength']} tokens/round from a pool of {sum(len(d['items']) for d in moe['destinations'])}")
for avg in (1.0, 1.3, 2.3):
    print(f"    {avg} experts/token -> {round((1 - avg / n) * 100)}% less compute")
amb = sum(1 for d in hard["destinations"] for i in d["items"] if isinstance(i, dict))
print(f"  hard: {hard['roundLength']} tokens, speed {hard['speed']['start']}, {amb} ambiguous")

pr = load("precision_recall.json")
items = [(i["score"], i["positive"]) for i in pr["items"]]
best = (0, 0, 0, 0)
for k in range(201):
    t = pr["param"]["min"] + (pr["param"]["max"] - pr["param"]["min"]) * k / 200
    TP = sum(1 for s, p in items if p and s >= t); FP = sum(1 for s, p in items if not p and s >= t)
    FN = sum(1 for s, p in items if p and s < t)
    prec = TP / (TP + FP) if TP + FP else 0
    rec = TP / (TP + FN) if TP + FN else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    if f1 > best[0]:
        best = (f1, t, prec, rec)
print("\nROUND 2 — precision/recall")
print(f"  {len(items)} emails ({sum(1 for _, p in items if p)} spam / {sum(1 for _, p in items if not p)} real)")
print(f"  best F1 {best[0]:.3f} at threshold {best[1]:.2f} -> precision {best[2]:.0%}, recall {best[3]:.0%}")
assert best[0] < 1.0, "classes separate cleanly — the game would contradict its own lesson"

gd = load("gradient_descent.json"); L = gd["landscape"]
T = {"quad": lambda t, x: 2 * t["a"] * x,
     "sin":  lambda t, x: t["amp"] * t["freq"] * math.cos(t["freq"] * x + t.get("phase", 0))}
df = lambda x: sum(T[t["type"]](t, x) for t in L["terms"])
print("\nROUND 3 — gradient descent")
for lr in (0.001, 0.1, 1.0):
    x, steps = gd["start"], 0
    for _ in range(400):
        nx = x - lr * df(x)
        if not (L["domain"][0] <= nx <= L["domain"][1]):
            x = nx; break
        x, steps = nx, steps + 1
        if abs(df(x)) < L["tolerance"]:
            break
    ok = abs(df(x)) < L["tolerance"]
    print(f"  lr {lr:<6} {'converged to %.3f in %d steps' % (x, steps) if ok else 'never converges (%d steps)' % steps}")

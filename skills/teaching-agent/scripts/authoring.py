"""Live JSON authoring with deterministic retries and a cached fallback.

Shared by generate_game.py (GAME_DATA) and render_scene.py (SCENE_DATA): same
contract, same failure handling, one copy. The caller supplies the guide the
model reads, its own validator, and where the cache lives.
"""
import json
import os
import pathlib
import re
import sys
import urllib.request


def model_config(args):
    """Endpoint from flags, then the Hermes config on this box, then env."""
    base, key, model = args.base_url, args.api_key, args.model
    if not (base and key):
        cfg = pathlib.Path.home() / ".hermes/config.yaml"
        if cfg.exists():
            text = cfg.read_text()
            base = base or (re.search(r"base_url: (\S+)", text) or [None, None])[1]
            key = key or (re.search(r"api_key: (sk-\S+)", text) or [None, None])[1]
            model = model or (re.search(r"default: (\S+)", text) or [None, None])[1]
    return (base or os.environ.get("TEACHING_AGENT_BASE_URL"),
            key or os.environ.get("TEACHING_AGENT_API_KEY"),
            model or os.environ.get("TEACHING_AGENT_MODEL"))


def ask_model(base, key, model, messages, timeout=180):
    body = json.dumps({"model": model, "temperature": 0.2, "max_tokens": 4000,
                       "messages": messages}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions", body,
                                 {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.load(f)["choices"][0]["message"]["content"]


def cached_for(concept: str, folder: pathlib.Path):
    """(template, data, filename) for the first index entry matching `concept`."""
    index = folder / "index.json"
    if not index.exists():
        return None
    needle = concept.lower()
    for e in json.loads(index.read_text())["entries"]:
        if any(m in needle for m in e["match"]):
            path = folder / e["file"]
            if path.exists():
                return e["template"], json.loads(path.read_text()), e["file"]
    return None


def author(concept, template, retries, args, *, guide, validate, cache_dir, ask, unwrap=None):
    """Ask the model, retry with the exact error, then fall back to cache.

    A model that has just emitted broken JSON is the least reliable thing to ask
    for a correction, so the retry is deterministic and lives here rather than in
    the agent loop. Returns (template, data, provenance).
    """
    base, key, model = model_config(args)
    messages = [{"role": "system", "content": guide},
                {"role": "user", "content": ask(concept, template)}]
    last = "no attempt made"

    if base and key and model:
        for attempt in range(retries + 1):
            raw = ""
            try:
                raw = ask_model(base, key, model, messages)
                blob = re.search(r"\{.*\}", raw, re.S)
                if not blob:
                    raise ValueError("no JSON object in the reply")
                obj = json.loads(blob.group(0))
                picked, data = unwrap(obj, template) if unwrap else (template, obj)
                validate(picked, data)
                return picked, data, f"model (attempt {attempt + 1})"
            except Exception as e:  # noqa: BLE001 — any failure is a retry
                last = f"{type(e).__name__}: {e}"
                print(f"authoring attempt {attempt + 1} failed: {last}", file=sys.stderr)
                if attempt == retries:
                    break
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"Your JSON was invalid: {last}. "
                                                "Fix it and return only valid JSON."},
                ]
    else:
        last = "no model endpoint configured"
        print(f"skipping live authoring: {last}", file=sys.stderr)

    fallback = cached_for(concept, cache_dir)
    if not fallback:
        raise ValueError(f"live authoring failed ({last}) and nothing cached matches '{concept}'")
    tpl, data, name = fallback
    print(f"falling back to cached {name} after {retries + 1} attempts", file=sys.stderr)
    return tpl, data, f"cache ({name})"

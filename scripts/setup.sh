#!/usr/bin/env bash
# Link the math-tutor skill into Hermes and make sure the dataset cache exists.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="${HERMES_HOME:-$HOME/.hermes}/skills"

[ -f "$REPO/data/gsm8k_cache.jsonl" ] || python3 "$REPO/scripts/build_gsm8k_cache.py"
[ -f "$REPO/data/math_cache.jsonl" ]  || python3 "$REPO/scripts/build_math_cache.py"

mkdir -p "$SKILLS_DIR"
ln -sfn "$REPO/skills/math-tutor" "$SKILLS_DIR/math-tutor"
echo "linked $SKILLS_DIR/math-tutor -> $REPO/skills/math-tutor"

echo
echo "Set these two keys in ${HERMES_HOME:-$HOME/.hermes}/config.yaml (see config/hermes_config.yaml):"
echo "  clarify.timeout: 900        # TUI"
echo "  agent.clarify_timeout: 900  # Telegram/gateway"
echo
echo "Then: hermes chat  ->  /reload-skills  ->  /math-tutor demo"

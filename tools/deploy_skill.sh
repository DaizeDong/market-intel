#!/usr/bin/env bash
# Sync the repo's skill into the live Claude Code skill dir — ONLY after a refresh PR is merged
# to main and the verify gate is green. Run manually (or from a post-merge hook) after merging.
set -euo pipefail
REPO="$HOME/CodesClaude/market-intel"
LIVE="$HOME/.claude/skills/market-intel"

cd "$REPO"
git checkout main --quiet && git pull --quiet origin main

# Re-run the gate on main before deploying — never deploy an unverified state.
if ! PYTHONIOENCODING=utf-8 python tools/verify_matrix.py --no-net; then
  echo "verify_matrix gate failed on main — refusing to deploy"; exit 1
fi

mkdir -p "$LIVE"
cp -r "$REPO/skills/market-intel/." "$LIVE/"
echo "Deployed market-intel ($(git rev-parse --short HEAD)) to $LIVE"

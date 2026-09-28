#!/usr/bin/env bash
# Baut die Checkpoint-Branches für die Studierenden aus common/ + steps/.
#
# Jeder Branch enthält den kompletten Projektstand eines Checkpoints
# (Daten + Docs aus common/ plus den jeweiligen Code-Stand aus steps/).
# Die Branches liegen auf EINER linearen Historie, sodass
# `git diff vl01-start vl01-solution` die Lerninhalte sichtbar macht.
#
# Nutzung (nur durch Menschen, vgl. Corporate Policy):
#   ./scripts/create-step-branches.sh
#   git push -f origin <alle Steps aus scripts/steps.conf>   # Zeile gibt das Skript am Ende aus
#
# Idempotent: kann nach Änderungen an common/ oder steps/ erneut laufen
# (Branches werden mit -f neu gesetzt). Es nutzt den Arbeitsstand von common/,
# scripts/ und steps/, nicht den letzten Commit. Deshalb vorher committen, damit
# Branches und main zusammenpassen.
#
# Nach dem Push einmal auf einem frischen Klon prüfen, z. B.
#   git clone <repo> /tmp/probe && cd /tmp/probe && git checkout vl06-guardrails
#   python -m pytest -q

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

source "$(dirname "$0")/steps.conf"
BUILD_DIR=.step-build
TMP_BRANCH=_steps-build-tmp

# Aufräumen von früheren Läufen
git worktree remove -f "$BUILD_DIR" 2>/dev/null || true
git branch -D "$TMP_BRANCH" 2>/dev/null || true

git worktree add --detach "$BUILD_DIR"
pushd "$BUILD_DIR" >/dev/null

git switch --orphan "$TMP_BRANCH"

for step in "${STEPS[@]}"; do
  # Arbeitsverzeichnis leeren (außer .git)
  find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

  "../scripts/assemble-step.sh" "$step" .

  git add -A
  git commit -m "Checkpoint: $step" --quiet
  git branch -f "$step" HEAD
  echo "✓ Branch $step gebaut"
done

popd >/dev/null
git worktree remove -f "$BUILD_DIR"
git branch -D "$TMP_BRANCH"

echo
echo "Fertig. Veröffentlichen (alle Checkpoints aus scripts/steps.conf, auch VL 4 und VL 5):"
echo "  git push -f origin ${STEPS[*]}"

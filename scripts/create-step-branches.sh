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
#   git push -f origin vl01-start vl01-solution vl03-llm-client vl03-evaluation \
#                      vl06-guardrails vl08-agent vl09-spec
#
# Idempotent: kann nach Änderungen an common/ oder steps/ erneut laufen
# (Branches werden mit -f neu gesetzt).

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
echo "Fertig. Veröffentlichen mit:"
echo "  git push -f origin ${STEPS[*]}"

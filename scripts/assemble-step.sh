#!/usr/bin/env bash
# Assembliert den kompletten Projektstand für einen Checkpoint.
#
# Reihenfolge:
#   1. common/ (Daten, Knowledge Base, Golden Set, SETUP.md, .gitignore)
#   2. nur die labs/-Ordner aller vorherigen Steps laut steps.conf, damit
#      frühere Anleitungen und Vorlagen im Branch bleiben
#   3. der Ziel-Step komplett
# Jeder Ordner unter steps/ ist deshalb ein vollständiger Code-Stand (src/,
# tests/, requirements.txt, conftest.py). Nur labs/ wird vererbt. Dateien, die
# in mehreren Steps gleich sind, liegen dort als identische Kopien.
#
# Nutzung:
#   ./scripts/assemble-step.sh <step-name> <zielverzeichnis>
#
# Beispiel:
#   ./scripts/assemble-step.sh vl03-evaluation /tmp/test-build

set -euo pipefail

# REPO_ROOT muss auf das QUELL-Repo zeigen, nicht aufs aktuelle Arbeits-
# verzeichnis: create-step-branches.sh ruft dieses Skript aus dem (geleerten)
# Worktree .step-build heraus auf, wo `git rev-parse --show-toplevel` den
# Worktree liefern würde. Daher relativ zum Skript-Pfad auflösen.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/steps.conf"

if [[ $# -ne 2 ]]; then
  echo "Nutzung: $0 <step-name> <zielverzeichnis>" >&2
  exit 1
fi

STEP="$1"
DEST="$2"

# Prüfe ob der Step existiert
found=false
for s in "${STEPS[@]}"; do
  if [[ "$s" == "$STEP" ]]; then
    found=true
    break
  fi
done

if [[ "$found" != true ]]; then
  echo "Fehler: Unbekannter Step '$STEP'" >&2
  echo "Verfügbare Steps: ${STEPS[*]}" >&2
  exit 1
fi

mkdir -p "$DEST"

# 1. common/ als Basis
cp -R "$REPO_ROOT/common/." "$DEST"

# 2. labs/ aus vorherigen Steps sammeln
for s in "${STEPS[@]}"; do
  if [[ "$s" == "$STEP" ]]; then
    break
  fi
  labs_dir="$REPO_ROOT/steps/$s/labs"
  if [[ -d "$labs_dir" ]]; then
    cp -R "$labs_dir/." "$DEST/labs/"
  fi
done

# 3. Ziel-Step komplett kopieren (überschreibt ggf. labs/), ohne venv und ohne
#    lokale Artefakte (Bytecode, pytest-Cache, Coverage-Daten).
#    rsync bevorzugt; falls nicht vorhanden (z. B. schlanke Container) cp-Fallback.
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude='venv' --exclude='.venv' --exclude='__pycache__' \
    --exclude='.pytest_cache' --exclude='.coverage' "$REPO_ROOT/steps/$STEP/" "$DEST"
else
  cp -R "$REPO_ROOT/steps/$STEP/." "$DEST"
  rm -rf "$DEST/venv" "$DEST/.venv" "$DEST/.pytest_cache" "$DEST/.coverage"
fi

# 4. Cleanup
rm -rf "$DEST/common"
rm -rf "$DEST/scripts"
rm -rf "$DEST/steps"
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} +

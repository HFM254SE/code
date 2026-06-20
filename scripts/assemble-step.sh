#!/usr/bin/env bash
# Assembliert den kompletten Projektstand für einen Checkpoint.
#
# Kopiert common/, dann alle vorherigen Steps der Reihe nach,
# dann den Ziel-Step selbst. So baut jeder Checkpoint automatisch
# auf den vorherigen auf – steps/ muss nur noch den eigenen Delta enthalten.
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

# 3. Ziel-Step komplett kopieren (überschreibt ggf. labs/), ohne venv.
#    rsync bevorzugt; falls nicht vorhanden (z. B. schlanke Container) cp-Fallback.
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude='venv' "$REPO_ROOT/steps/$STEP/" "$DEST"
else
  cp -R "$REPO_ROOT/steps/$STEP/." "$DEST"
  rm -rf "$DEST/venv"
fi

#!/usr/bin/env bash
set -euo pipefail

# Prune script: build a pitch-ready subset in ./osiris-pitch
OUT_DIR="${1:-./osiris-pitch}"
mkdir -p "$OUT_DIR"

# Minimal include list (adjust as needed)
INCLUDES=(
  "osiris"
  "osiris-demo"
  "osiris-cli"
  "README_QUICKSTART.md"
  "README_BRIEF.md"
  "LICENSE"
  "pyproject.toml"
  "requirements.txt"
  "docs"
  "documentation"
)

EXCLUDES=(
  "*.zip"
  "*.tar.gz"
  "*.whl"
  "*.egg-info"
  "venv*/"
  ".venv/"
  "osiris-venv/"
  "__pycache__/"
  "*.pyc"
  "node_modules/"
  ".git/"
  "*.egg-info/"
)

RSYNC_EXCLUDES=()
for e in "${EXCLUDES[@]}"; do
  RSYNC_EXCLUDES+=(--exclude="$e")
done

echo "Building pitch subset → $OUT_DIR"

for item in "${INCLUDES[@]}"; do
  if [ -e "$item" ]; then
    echo "Copying: $item"
    rsync -a "${RSYNC_EXCLUDES[@]}" --prune-empty-dirs "$item" "$OUT_DIR/"
  else
    echo "Skipping (not found): $item"
  fi
done

# Print summary
echo "\nSummary for $OUT_DIR:"
du -sh "$OUT_DIR" 2>/dev/null || true
find "$OUT_DIR" -maxdepth 2 -type f | wc -l | xargs -I{} echo "Files copied (top 2 levels): {}"

echo "Pitch subset ready in: $OUT_DIR"

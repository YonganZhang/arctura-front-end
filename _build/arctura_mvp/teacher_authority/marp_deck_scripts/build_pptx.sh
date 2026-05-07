#!/usr/bin/env bash
# build_pptx.sh — Convert all decks/*.md in an MVP folder to PPTX (and optionally PDF/HTML)
# Usage: build_pptx.sh <mvp-folder> [--pdf] [--html]
#
# ⚠ CANONICAL COPY lives at:
#     /Users/kaku/Desktop/Work/StartUP-Building/.claude/skills/marp-deck/scripts/build_pptx.sh
# A mirror also exists at CLI-Anything/.claude/skills/marp-deck/scripts/build_pptx.sh.
# When editing, update both copies (or symlink). Last verified identical: 2026-04-21.
set -e

# Check marp is available
command -v marp >/dev/null 2>&1 || { echo "ERROR: marp not found in PATH. Install with: npm i -g @marp-team/marp-cli"; exit 1; }

MVP_DIR="${1:-.}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_FILE="$SKILL_DIR/theme/studio.css"
DECKS_DIR="$MVP_DIR/decks"

EXTRA_FORMATS=()
for arg in "$@"; do
  case "$arg" in
    --pdf)  EXTRA_FORMATS+=("pdf") ;;
    --html) EXTRA_FORMATS+=("html") ;;
  esac
done

if [ ! -d "$DECKS_DIR" ]; then
  echo "ERROR: $DECKS_DIR does not exist. Run sub-agents to generate deck-*.md first."
  exit 1
fi

cd "$MVP_DIR"

count=0
for md in decks/deck-*.md; do
  [ -f "$md" ] || continue
  base="${md%.md}"
  echo "→ $md"
  # Try --pptx-editable first (experimental in marp 4.x), fall back to standard --pptx
  marp --theme-set "$THEME_FILE" --pptx --pptx-editable --allow-local-files "$md" -o "${base}.pptx" 2>/dev/null \
    || marp --theme-set "$THEME_FILE" --pptx --allow-local-files "$md" -o "${base}.pptx"
  for fmt in "${EXTRA_FORMATS[@]}"; do
    case "$fmt" in
      pdf)  marp --theme-set "$THEME_FILE" --pdf  --allow-local-files "$md" -o "${base}.pdf" ;;
      html) marp --theme-set "$THEME_FILE" --html --allow-local-files "$md" -o "${base}.html" ;;
    esac
  done
  count=$((count+1))
done

echo ""
echo "✅ Converted $count deck(s) to PPTX in $DECKS_DIR/"
ls -lh decks/*.pptx 2>/dev/null

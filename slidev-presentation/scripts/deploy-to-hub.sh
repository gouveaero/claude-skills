#!/usr/bin/env bash
# deploy-to-hub.sh — deploy de um deck Slidev pro slides-hub.
# Uso: ./deploy-to-hub.sh <slug> [path-do-deck]
#
# Faz:
# 1. slidev build --base /$slug/ no path do deck
# 2. Sync dist/ pra $SLIDES_HUB_DIR/decks/$slug/
# 3. git add/commit/push no slides-hub
# 4. Aguarda Coolify redeploy (poll)
# 5. Verifica URL pública (curl 200)

set -euo pipefail

slug="${1:-}"
deck_path="${2:-$(pwd)}"
hub_dir="${SLIDES_HUB_DIR:-$HOME/.slides-hub}"
public_url="https://slides.gabrielgouvea.com.br/$slug/"

if [[ -z "$slug" ]]; then
  echo "Usage: $0 <slug> [deck-path]" >&2
  exit 1
fi

if [[ ! -d "$hub_dir" ]]; then
  echo "Slides hub not initialized. Run scripts/setup-hub.sh first." >&2
  exit 2
fi

if [[ ! -f "$deck_path/slides.md" ]]; then
  echo "No slides.md in $deck_path — not a Slidev deck." >&2
  exit 3
fi

echo ">>> 1/5  Building $slug from $deck_path"
(cd "$deck_path" && npm run build -- --base "/$slug/")

if [[ ! -d "$deck_path/dist" ]]; then
  echo "Build did not produce dist/. Aborting." >&2
  exit 4
fi

echo ">>> 2/5  Syncing dist/ → $hub_dir/decks/$slug/"
mkdir -p "$hub_dir/decks"
rm -rf "$hub_dir/decks/$slug"
cp -r "$deck_path/dist" "$hub_dir/decks/$slug"

echo ">>> 2.5/5  Regenerating hub index.html"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node "$script_dir/regen-hub-index.mjs" "$hub_dir"

echo ">>> 3/5  Committing and pushing to slides-hub"
(
  cd "$hub_dir"
  git add "decks/$slug/" index.html
  if git diff --cached --quiet; then
    echo "  No changes to commit (deck identical to last deploy)."
  else
    git commit -m "deploy: $slug"
    git push origin main
  fi
)

echo ">>> 4/5  Waiting for Coolify to redeploy (up to 180s)..."
# Coolify auto-deploys on push via GitHub App webhook.
# Poll the public URL until it returns 200 or timeout.
end=$(( $(date +%s) + 180 ))
while [[ $(date +%s) -lt $end ]]; do
  if curl -sf -o /dev/null -w "%{http_code}" "$public_url" | grep -q "^200$"; then
    echo "  Deploy live."
    break
  fi
  sleep 5
done

echo ">>> 5/5  Verifying public URL"
if curl -sfI "$public_url" >/dev/null 2>&1; then
  echo "✓ Deck live at $public_url"
else
  echo "⚠ Deploy may still be propagating. Check Coolify dashboard." >&2
  echo "  URL: $public_url"
  exit 5
fi

#!/usr/bin/env bash
# check-slug-collision.sh — verifica se já existe deck com esse slug no slides-hub.
# Uso: ./check-slug-collision.sh <slug>
# Exit code: 0 = livre, 1 = colide, 2 = hub não existe

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <slug>" >&2
  exit 1
fi

slug="$1"
hub_dir="${SLIDES_HUB_DIR:-$HOME/.slides-hub}"

if [[ ! -d "$hub_dir" ]]; then
  echo "Slides hub not initialized at $hub_dir" >&2
  echo "Run scripts/setup-hub.sh first" >&2
  exit 2
fi

# Refresca o repo pra pegar estado atual
(cd "$hub_dir" && git fetch --quiet origin && git pull --quiet --ff-only origin main 2>/dev/null) || true

if [[ -d "$hub_dir/decks/$slug" ]]; then
  echo "COLLISION: deck '$slug' already exists at $hub_dir/decks/$slug" >&2
  exit 1
fi

echo "Free: slug '$slug' is available"
exit 0

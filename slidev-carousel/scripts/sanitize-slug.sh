#!/usr/bin/env bash
# sanitize-slug.sh — converte um título em slug ASCII-safe.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"<title>\"" >&2
  exit 1
fi

slug=$(echo "$1" \
  | iconv -f utf-8 -t ascii//TRANSLIT//IGNORE 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/-+/-/g' \
  | sed -E 's/^-//; s/-$//')

[[ -z "$slug" ]] && { echo "Empty slug" >&2; exit 1; }
echo "$slug"

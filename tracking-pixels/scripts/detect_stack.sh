#!/usr/bin/env bash
# detect_stack.sh — figure out which template a site repo wants.
#
# Usage:   detect_stack.sh /path/to/site
# Outputs: nextjs-app-router | vite-react-spa | unknown
# Exit:    0 on success (even if "unknown"), 1 on bad input.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <site_path>" >&2
  exit 1
fi

SITE="$1"
PKG="$SITE/package.json"

if [[ ! -f "$PKG" ]]; then
  echo "unknown"
  exit 0
fi

# Read deps in one shot
DEPS=$(jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' "$PKG" 2>/dev/null || echo "")

has() { echo "$DEPS" | grep -qx "$1"; }

# Next.js takes precedence if both somehow exist
if has "next"; then
  # Distinguish App Router (app/ dir) from Pages Router (pages/ dir)
  if [[ -d "$SITE/app" || -d "$SITE/src/app" ]]; then
    echo "nextjs-app-router"
  else
    # Pages router not supported in V1
    echo "unknown"
  fi
  exit 0
fi

if has "vite" && has "react"; then
  echo "vite-react-spa"
  exit 0
fi

echo "unknown"

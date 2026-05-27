#!/usr/bin/env bash
# verify-png-dimensions.sh — valida que todos os PNGs em uma pasta têm as dimensões esperadas.
# Uso: ./verify-png-dimensions.sh <pasta> <largura> <altura>
# Exit 0 = todos ok. Exit 1 = ao menos 1 divergente.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <folder> <expected-width> <expected-height>" >&2
  exit 1
fi

folder="$1"
exp_w="$2"
exp_h="$3"

if [[ ! -d "$folder" ]]; then
  echo "Pasta não existe: $folder" >&2
  exit 2
fi

if ! command -v sips &>/dev/null; then
  echo "sips (macOS) não encontrado. Esse script só roda em macOS." >&2
  exit 3
fi

bad=0
total=0
for png in "$folder"/*.png; do
  [[ -e "$png" ]] || continue
  total=$((total + 1))
  w=$(sips -g pixelWidth "$png" 2>/dev/null | awk '/pixelWidth/ {print $2}')
  h=$(sips -g pixelHeight "$png" 2>/dev/null | awk '/pixelHeight/ {print $2}')
  if [[ "$w" != "$exp_w" || "$h" != "$exp_h" ]]; then
    echo "✗ $(basename "$png"): ${w}x${h} (esperado ${exp_w}x${exp_h})" >&2
    bad=$((bad + 1))
  fi
done

if [[ $total -eq 0 ]]; then
  echo "Nenhum PNG encontrado em $folder" >&2
  exit 4
fi

if [[ $bad -gt 0 ]]; then
  echo "" >&2
  echo "$bad/$total PNGs com dimensão errada." >&2
  exit 1
fi

echo "✓ $total PNGs ok em ${exp_w}x${exp_h}"

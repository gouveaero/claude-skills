#!/usr/bin/env bash
# export-carousel.sh — exporta carrossel pra PNGs e verifica dimensões.
# Uso: ./export-carousel.sh <projeto-folder> [aspect]
#   aspect: portrait (default, 1080x1350), square (1080x1080), story (1080x1920)

set -euo pipefail

project_path="${1:-$(pwd)}"
aspect="${2:-portrait}"

case "$aspect" in
  portrait) exp_w=1080; exp_h=1350 ;;
  square)   exp_w=1080; exp_h=1080 ;;
  story)    exp_w=1080; exp_h=1920 ;;
  *) echo "aspect inválido: portrait|square|story" >&2; exit 1 ;;
esac

if [[ ! -f "$project_path/slides.md" ]]; then
  echo "slides.md não encontrado em $project_path" >&2
  exit 2
fi

echo ">>> Validando regra de 12 palavras por slide"
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
"$script_dir/count-words-per-slide.sh" "$project_path/slides.md"

echo ""
echo ">>> Exportando para PNG ($aspect = ${exp_w}x${exp_h})"
cd "$project_path"
rm -rf ./exports
npm run export -- --format png --output ./exports/

echo ""
echo ">>> Verificando dimensões"
"$script_dir/verify-png-dimensions.sh" "$project_path/exports" "$exp_w" "$exp_h"

echo ""
echo "✓ Carrossel exportado: $project_path/exports/"
ls -1 "$project_path/exports/"

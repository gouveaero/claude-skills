#!/usr/bin/env bash
# sanitize-slug.sh — converte um título em slug ASCII-safe.
# Uso: ./sanitize-slug.sh "Meu Título com Acentuação"
# Saída: meu-titulo-com-acentuacao

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"<title>\"" >&2
  exit 1
fi

input="$1"

# 1) Normaliza acentos via iconv (NFD + ASCII transliteration)
# 2) Lowercase
# 3) Trim, troca tudo que não for [a-z0-9] por hyphen
# 4) Colapsa hyphens duplicados
# 5) Remove hyphens das pontas
slug=$(echo "$input" \
  | iconv -f utf-8 -t ascii//TRANSLIT//IGNORE 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g' \
  | sed -E 's/-+/-/g' \
  | sed -E 's/^-//; s/-$//')

if [[ -z "$slug" ]]; then
  echo "Error: sanitization resulted in empty slug" >&2
  exit 1
fi

echo "$slug"

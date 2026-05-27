#!/usr/bin/env bash
# count-words-per-slide.sh — valida regra de ≤12 palavras por slide.
# Uso: ./count-words-per-slide.sh <path-do-slides.md>
# Exit 0 = todos os slides ok. Exit 1 = encontrou violação.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <slides.md>" >&2
  exit 1
fi

slides_file="$1"
max_words=12
violations=0
slide_idx=0
in_frontmatter=false
current_slide_words=0
current_slide_first_line=""
buffer=""

while IFS= read -r line || [[ -n "$line" ]]; do
  # Separador de slide ---
  if [[ "$line" == "---" ]]; then
    if [[ $slide_idx -eq 0 && "$in_frontmatter" == "false" ]]; then
      # Início do frontmatter global
      in_frontmatter=true
      continue
    fi

    if [[ "$in_frontmatter" == "true" ]]; then
      # Fechando frontmatter ou frontmatter de slide
      in_frontmatter=false
      continue
    fi

    # Fim de slide — avalia
    if [[ $slide_idx -gt 0 ]]; then
      # Limpa HTML, tags Vue, código, comentários
      cleaned=$(echo "$buffer" | sed -E \
        -e 's/<[^>]*>//g' \
        -e 's/^[[:space:]]*<!--.*-->[[:space:]]*$//' \
        -e 's/^[[:space:]]*```.*$//' \
        -e 's/:[a-zA-Z-]+=\"[^\"]*\"//g' \
        -e 's/[\{\}\(\)]//g')
      words=$(echo "$cleaned" | wc -w | tr -d ' ')
      if [[ $words -gt $max_words ]]; then
        echo "✗ Slide $slide_idx: $words palavras (cap: $max_words)" >&2
        echo "  Primeira linha: $current_slide_first_line" >&2
        violations=$((violations + 1))
      fi
    fi

    slide_idx=$((slide_idx + 1))
    buffer=""
    current_slide_first_line=""
    in_frontmatter=true
    continue
  fi

  if [[ "$in_frontmatter" == "true" ]]; then
    continue
  fi

  [[ -z "$current_slide_first_line" && -n "$line" ]] && current_slide_first_line="$line"
  buffer="$buffer
$line"
done < "$slides_file"

# Última seção
if [[ $slide_idx -gt 0 && -n "$buffer" ]]; then
  cleaned=$(echo "$buffer" | sed -E \
    -e 's/<[^>]*>//g' \
    -e 's/^[[:space:]]*<!--.*-->[[:space:]]*$//' \
    -e 's/^[[:space:]]*```.*$//' \
    -e 's/:[a-zA-Z-]+=\"[^\"]*\"//g' \
    -e 's/[\{\}\(\)]//g')
  words=$(echo "$cleaned" | wc -w | tr -d ' ')
  if [[ $words -gt $max_words ]]; then
    echo "✗ Slide $slide_idx: $words palavras (cap: $max_words)" >&2
    echo "  Primeira linha: $current_slide_first_line" >&2
    violations=$((violations + 1))
  fi
fi

if [[ $violations -gt 0 ]]; then
  echo "" >&2
  echo "$violations slide(s) violando cap de $max_words palavras." >&2
  exit 1
fi

echo "✓ Todos os $slide_idx slides dentro do cap ($max_words palavras)."

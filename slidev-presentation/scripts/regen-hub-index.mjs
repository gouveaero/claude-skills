#!/usr/bin/env node
// regen-hub-index.mjs — Regenera o index.html raiz do slides-hub
// listando todos os decks publicados em decks/*.
//
// Uso: node regen-hub-index.mjs [hub-dir]
// Default hub-dir: $SLIDES_HUB_DIR ou ~/.slides-hub
//
// Estratégia:
// 1. Lê todas as subpastas de <hub-dir>/decks/ que tenham index.html.
// 2. Extrai o <title> de cada index.html da deck (limpa o sufixo " - Slidev").
// 3. Gera <li><a href="/<slug>/">{title}</a></li> ordenado por mtime descendente.
// 4. Substitui o bloco <ul id="decks">...</ul> no <hub-dir>/index.html.

import { readFileSync, writeFileSync, readdirSync, existsSync, statSync } from 'node:fs'
import { join, basename } from 'node:path'
import { homedir } from 'node:os'

const args = process.argv.slice(2)
const hubDir = args[0] || process.env.SLIDES_HUB_DIR || join(homedir(), '.slides-hub')

if (!existsSync(hubDir)) {
  console.error(`Hub directory not found: ${hubDir}`)
  process.exit(1)
}

const decksDir = join(hubDir, 'decks')
const indexPath = join(hubDir, 'index.html')

if (!existsSync(decksDir)) {
  console.error(`No decks/ subdirectory in ${hubDir}`)
  process.exit(1)
}

if (!existsSync(indexPath)) {
  console.error(`No index.html in ${hubDir}`)
  process.exit(1)
}

// Collect decks
const decks = []
for (const entry of readdirSync(decksDir)) {
  const deckPath = join(decksDir, entry)
  const deckIndex = join(deckPath, 'index.html')
  if (!existsSync(deckIndex)) continue
  const stat = statSync(deckPath)
  if (!stat.isDirectory()) continue

  const html = readFileSync(deckIndex, 'utf8')
  const titleMatch = html.match(/<title>([^<]+)<\/title>/i)
  let title = titleMatch ? titleMatch[1].trim() : entry
  // Strip Slidev's " - Slidev" suffix
  title = title.replace(/\s*[-—]\s*Slidev\s*$/i, '')
  // Strip placeholder
  if (title === '{{TITLE}}') title = entry
  // Decode common HTML entities
  title = title
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')

  decks.push({
    slug: entry,
    title,
    mtime: stat.mtimeMs,
  })
}

// Sort by mtime descending (recent decks first)
decks.sort((a, b) => b.mtime - a.mtime)

// Build new <ul> content
const items = decks.length === 0
  ? `    <li><em>Nenhum deck publicado ainda.</em></li>`
  : decks.map(d => {
      const escapedTitle = d.title
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
      return `    <li><a href="/${d.slug}/">${escapedTitle}</a></li>`
    }).join('\n')

// Replace block in index.html
const indexHtml = readFileSync(indexPath, 'utf8')
const newHtml = indexHtml.replace(
  /<ul id="decks">[\s\S]*?<\/ul>/,
  `<ul id="decks">\n${items}\n  </ul>`,
)

if (newHtml === indexHtml) {
  console.error('Could not locate <ul id="decks">...</ul> block in index.html — file structure changed?')
  process.exit(2)
}

writeFileSync(indexPath, newHtml)

console.log(`✓ Regenerated ${indexPath}`)
console.log(`  ${decks.length} deck${decks.length === 1 ? '' : 's'} listed:`)
for (const d of decks) {
  console.log(`    • ${d.slug} — ${d.title}`)
}

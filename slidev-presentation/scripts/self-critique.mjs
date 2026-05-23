#!/usr/bin/env node
// self-critique.mjs — auditoria objetiva de deck Slidev
// Uso: node self-critique.mjs <projeto-dir> [--visual] [--url <http://...>]
//
// Roda checks estáticos no slides.md + checks visuais opcionais via Playwright.
// Exit 0 = PASS, exit 1 = FAIL (algum check hard rule). WARN não bloqueia.

import { readFileSync, existsSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { argv, exit } from 'node:process'

const args = argv.slice(2)
if (args.length < 1 || args[0] === '--help') {
  console.log('Uso: node self-critique.mjs <projeto-dir> [--visual] [--url <url>]')
  exit(0)
}

const projectDir = resolve(args[0])
const visual = args.includes('--visual')
const urlIdx = args.indexOf('--url')
const url = urlIdx >= 0 ? args[urlIdx + 1] : null

const slidesPath = join(projectDir, 'slides.md')
if (!existsSync(slidesPath)) {
  console.error(`✗ slides.md not found at ${slidesPath}`)
  exit(2)
}

const raw = readFileSync(slidesPath, 'utf8')

// ────────────────────────────────────────────────────────────
// Parsing: split por separadores `---` (que delimitam slides)
// ────────────────────────────────────────────────────────────

function splitSlides(content) {
  // Slidev usa `---` em 3 contextos:
  //   1. Global frontmatter (primeiro bloco do arquivo)
  //   2. Frontmatter de slide específico (opcional, no início de cada slide)
  //   3. Separador entre slides
  //
  // Estratégia: skip global frontmatter; split em chunks por `---`;
  // chunks que são "puro frontmatter" (só key:value) viram metadados do próximo slide real.

  const lines = content.split('\n')
  let body = content
  if (lines[0]?.trim() === '---') {
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === '---') {
        body = lines.slice(i + 1).join('\n')
        break
      }
    }
  }

  const re = /^---\s*$/m
  const rawChunks = body.split(re).map(c => c.trim()).filter(c => c.length > 0)

  const isFrontmatterChunk = (c) => {
    // ignora linhas vazias e comentários HTML
    const lns = c.split('\n')
      .map(l => l.trim())
      .filter(l => l && !l.startsWith('<!--') && !l.startsWith('//'))
    if (lns.length === 0 || lns.length > 12) return false // frontmatter slide é curto
    // Cada linha precisa ser key: value OU continuação YAML (indented) OU lista (- item) OU comentário
    return lns.every(l =>
      /^[a-zA-Z_][\w-]*\s*:/.test(l) ||  // key: value
      /^-\s/.test(l) ||                   // - item
      /^[|>]/.test(l) ||                  // YAML block scalar
      /^\s+\S/.test(l)                    // indented continuation
    )
  }

  const slides = []
  let pending = null
  for (const c of rawChunks) {
    if (isFrontmatterChunk(c) && pending === null) {
      pending = c
    } else {
      const raw = (pending ? pending + '\n---\n' : '') + c
      slides.push({ idx: slides.length + 1, raw, frontmatter: pending })
      pending = null
    }
  }
  if (pending) {
    // frontmatter no fim sem body: trata como slide standalone (raro)
    slides.push({ idx: slides.length + 1, raw: pending, frontmatter: pending })
  }
  return slides
}

const slides = splitSlides(raw)

// ────────────────────────────────────────────────────────────
// Resultado: lista de issues com severity
// ────────────────────────────────────────────────────────────

const issues = []
function add(severity, slideIdx, code, msg, hint) {
  issues.push({ severity, slideIdx, code, msg, hint })
}

// ────────────────────────────────────────────────────────────
// CHECKS ESTÁTICOS
// ────────────────────────────────────────────────────────────

// 1. Slide count
if (slides.length < 5) {
  add('WARN', null, 'slide-count-low', `Deck tem ${slides.length} slides — geralmente <5 é insuficiente pra narrativa.`, 'Considere expandir o arco. Hooks + transição + climax + CTA mínimo.')
}
if (slides.length > 40) {
  add('WARN', null, 'slide-count-high', `Deck tem ${slides.length} slides — geralmente >40 perde atenção.`, 'Considere consolidar slides redundantes ou separar em sessões.')
}

// 2. Layout variety
const layoutPattern = /^layout:\s*(\S+)/m
const layoutCounts = {}
let slidesWithExplicitLayout = 0
for (const s of slides) {
  const m = s.raw.match(layoutPattern)
  if (m) {
    slidesWithExplicitLayout++
    const lay = m[1].replace(/['"]/g, '').trim()
    layoutCounts[lay] = (layoutCounts[lay] || 0) + 1
  } else {
    // sem layout = default
    layoutCounts['default'] = (layoutCounts['default'] || 0) + 1
  }
}
const defaultLikeCount = (layoutCounts['default'] || 0) + (layoutCounts['center'] || 0)
const defaultRatio = defaultLikeCount / slides.length
if (defaultRatio > 0.6) {
  add('WARN', null, 'layout-monoculture', `${Math.round(defaultRatio * 100)}% dos slides usam default/center. Slidev tem 17+ layouts.`, 'Map slide-tipo → layout: estatística → fact, citação → quote, separador → section, capa → cover, manifesto → statement.')
}

// 3. Gradient text count
const gradientHits = []
slides.forEach(s => {
  // Procurar classes com gradient text (climax-line, gradient, etc.) ou background-clip: text inline
  const climaxMatches = s.raw.match(/class="[^"]*\b(climax-line|gradient-text|text-gradient)\b[^"]*"/g) || []
  const bgClipMatches = s.raw.match(/background-clip:\s*text/g) || []
  if (climaxMatches.length > 0 || bgClipMatches.length > 0) {
    gradientHits.push(s.idx)
  }
})
if (gradientHits.length > 1) {
  add('FAIL', null, 'gradient-text-overused', `Gradient text aparece em ${gradientHits.length} slides (${gradientHits.join(', ')}). Reserve para 1 slide (climax/tese).`, 'Trocar todos exceto o climax para solid color. Gradient é decoração — só funciona quando é raro.')
}

// 4. Em-dash usage
const emDashSlides = slides.filter(s => (s.raw.match(/—/g) || []).length >= 3)
if (emDashSlides.length > 2) {
  add('WARN', null, 'em-dash-overuse', `Em-dashes (—) abundantes em ${emDashSlides.length} slides. AI slop signature.`, 'Trocar por vírgulas, dois-pontos, ou ponto-final. Em-dash só quando a frase precisa dele.')
}

// 5. Per-slide checks
slides.forEach(s => {
  // Word count: aproximação removendo HTML/markdown
  const stripped = s.raw
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/^\s*\w+:.*/gm, '') // frontmatter
    .replace(/[#*_`\[\]]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  const wordCount = stripped.split(/\s+/).filter(Boolean).length
  if (wordCount > 60) {
    add('WARN', s.idx, 'word-count', `Slide tem ~${wordCount} palavras. Cap recomendado: 40 (denso) / 25 (médio) / 12 (hook).`, 'Quebrar em 2 slides ou usar componente custom (MetricGrid, Timeline) ao invés de texto.')
  }

  // H1 count: linhas que começam com `# ` ou `<h1` (não dentro de style/script)
  const h1Lines = (s.raw.match(/^#\s+/gm) || []).length + (s.raw.match(/<h1[\s>]/g) || []).length
  if (h1Lines > 2) {
    add('WARN', s.idx, 'h1-count', `Slide tem ${h1Lines} headings h1.`, 'Usar 1 h1 principal + sub-headings em h2/h3 ou divs estilizadas.')
  }

  // Side-stripe borders
  const stripeMatches = s.raw.match(/border-(left|right):\s*(\d+)px/g) || []
  for (const m of stripeMatches) {
    const px = parseInt(m.match(/(\d+)px/)[1])
    if (px > 1) {
      add('FAIL', s.idx, 'side-stripe', `Side-stripe border detected: ${m}. Banimento absoluto.`, 'Trocar por full border 1px, background tint, leading number/icon, ou nada.')
      break
    }
  }

  // Pure #000 / #fff usage
  if (/#000(\b|;|"|\s)/i.test(s.raw) || /#fff(\b|;|"|\s)/i.test(s.raw)) {
    add('WARN', s.idx, 'pure-black-white', `Pure #000 ou #fff detectado.`, 'Tinte para a hue da marca: #fefefe / #050816, etc.')
  }

  // Identical card grids: 4+ divs com mesma classe principal
  const cardClasses = (s.raw.match(/class="[^"]*\b(card|metric|kpi|tile)\b[^"]*"/g) || [])
  if (cardClasses.length >= 6) {
    add('WARN', s.idx, 'card-grid', `Slide tem ${cardClasses.length} cards detectados. Acima de 4–5 vira template SaaS.`, 'Variar tamanhos, usar Timeline/Mermaid, ou quebrar em 2 slides.')
  }

  // Glassmorphism overuse
  const blurMatches = (s.raw.match(/backdrop-filter:\s*blur/g) || []).length
  if (blurMatches > 2) {
    add('WARN', s.idx, 'glassmorphism', `${blurMatches} usos de backdrop-filter: blur. Glassmorphism decorativo banido.`, 'Reservar para 1 elemento com propósito (overlay sobre vídeo).')
  }
})

// 6. Font count global
const allFonts = new Set()
const fontFamilyRe = /font-family:\s*['"]?([^'"\n,;]+)/g
let match
while ((match = fontFamilyRe.exec(raw)) !== null) {
  const f = match[1].trim()
  if (!['sans-serif', 'serif', 'monospace', 'system-ui', 'inherit', 'initial'].includes(f.toLowerCase())) {
    allFonts.add(f)
  }
}
if (allFonts.size > 4) {
  add('WARN', null, 'font-count', `${allFonts.size} fontes distintas detectadas (${[...allFonts].slice(0, 6).join(', ')}...). Manter ≤ 3.`, 'Display + body + meta = 3. Mais que isso = caos tipográfico.')
}

// 7. Feature showcase: ao menos 1 premium feature
const features = {
  'magic-move': /```\s*magic-move|magic-move\s/,
  'mermaid': /```\s*mermaid/,
  'twoslash': /```ts\s+twoslash|```typescript\s+twoslash/,
  'latex': /\$\$[\s\S]+?\$\$/,
  'mermaid-component': /<Mermaid/,
  'InteractivePoll': /<InteractivePoll/,
  'ROICalculator': /<ROICalculator/,
  'Monaco': /\{monaco/,
  'Iconify': /<(mdi|heroicons|carbon|lucide)-[a-z-]+/,
  'v-motion': /v-motion/,
}
const found = Object.entries(features).filter(([_k, re]) => re.test(raw)).map(([k]) => k)
if (found.length === 0) {
  add('WARN', null, 'no-premium-features', 'Deck não usa nenhuma feature premium do Slidev (magic-move, mermaid, latex, InteractivePoll, ROICalculator, Iconify, v-motion).', 'Slidev tem ~60 features documentadas. Usar 0 reduz o deck a Markdown formatado. Ver references/code-features.md, references/diagrams.md, references/interactive.md.')
} else if (found.length === 1 && found[0] === 'v-motion') {
  add('WARN', null, 'low-feature-usage', `Só v-motion usado. Considere adicionar 1 feature mais expressiva.`, 'Magic Move pra código, Mermaid pra arquitetura, InteractivePoll pra audiência, Iconify pra ícones.')
}

// ────────────────────────────────────────────────────────────
// CHECKS VISUAIS (opcional, requer Playwright)
// ────────────────────────────────────────────────────────────

async function visualChecks(targetUrl, slideCount) {
  let chromium
  try {
    ;({ chromium } = await import(join(projectDir, 'node_modules', 'playwright-chromium')))
  } catch (e) {
    try {
      ;({ chromium } = await import('playwright-chromium'))
    } catch (e2) {
      console.error('⚠ playwright-chromium not found. Run `npm install playwright-chromium --save-dev` in the project, or skip --visual.')
      return
    }
  }
  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } })
  const page = await ctx.newPage()

  for (let i = 1; i <= slideCount; i++) {
    const slideUrl = `${targetUrl.replace(/\/$/, '')}/${i}?clicks=99`
    try {
      await page.goto(slideUrl, { waitUntil: 'networkidle', timeout: 15000 })
      await page.waitForTimeout(500)
      const overflow = await page.evaluate(() => {
        const slide = document.querySelector('.slidev-page, .slidev-layout')
        if (!slide) return null
        const slideRect = slide.getBoundingClientRect()
        const problems = []
        slide.querySelectorAll('h1, h2, h3, p, div, span').forEach(el => {
          const r = el.getBoundingClientRect()
          if (r.width === 0 || r.height === 0) return
          if (r.right > slideRect.right + 2 || r.left < slideRect.left - 2 ||
              r.bottom > slideRect.bottom + 2 || r.top < slideRect.top - 2) {
            const tag = el.tagName.toLowerCase()
            const cls = el.className?.toString().slice(0, 40)
            const txt = el.textContent?.trim().slice(0, 50)
            problems.push({ tag, cls, txt, overflowX: Math.max(0, r.right - slideRect.right, slideRect.left - r.left), overflowY: Math.max(0, r.bottom - slideRect.bottom, slideRect.top - r.top) })
          }
        })
        return problems
      })
      if (overflow && overflow.length > 0) {
        const worst = overflow.sort((a, b) => (b.overflowX + b.overflowY) - (a.overflowX + a.overflowY))[0]
        add('FAIL', i, 'visual-overflow', `Element clips outside slide bounds: <${worst.tag} class="${worst.cls}">"${worst.txt}" overflow x=${Math.round(worst.overflowX)}px y=${Math.round(worst.overflowY)}px`, 'Reduzir font-size com clamp(), aplicar text-wrap: balance, ou aumentar max-width.')
      }

      // Color count per slide
      const colorCount = await page.evaluate(() => {
        const slide = document.querySelector('.slidev-page, .slidev-layout')
        if (!slide) return 0
        const colors = new Set()
        slide.querySelectorAll('*').forEach(el => {
          const cs = getComputedStyle(el)
          const c = cs.color
          const bg = cs.backgroundColor
          if (c && c !== 'rgba(0, 0, 0, 0)') colors.add(c)
          if (bg && bg !== 'rgba(0, 0, 0, 0)') colors.add(bg)
        })
        return colors.size
      })
      if (colorCount > 12) {
        add('WARN', i, 'color-count', `Slide tem ${colorCount} cores distintas computed. >10 é geralmente ruído.`, 'Consolidar para color strategy (Restrained, Committed, Full palette, Drenched).')
      }
    } catch (e) {
      add('WARN', i, 'visual-error', `Could not visually check slide: ${e.message.slice(0, 80)}`, null)
    }
  }
  await browser.close()
}

// ────────────────────────────────────────────────────────────
// EXECUÇÃO
// ────────────────────────────────────────────────────────────

if (visual && url) {
  await visualChecks(url, slides.length)
} else if (visual && !url) {
  console.error('⚠ --visual requires --url <http://localhost:3030> or deploy URL')
}

// ────────────────────────────────────────────────────────────
// REPORT
// ────────────────────────────────────────────────────────────

const fails = issues.filter(i => i.severity === 'FAIL')
const warns = issues.filter(i => i.severity === 'WARN')

console.log('\n━━━ Slidev Self-Critique ━━━')
console.log(`Deck: ${projectDir}`)
console.log(`Slides: ${slides.length}`)
console.log(`Premium features: ${found.join(', ') || 'none'}`)
console.log(`Layouts: ${Object.entries(layoutCounts).map(([k, v]) => `${k}(${v})`).join(', ')}`)
console.log('')

if (fails.length === 0 && warns.length === 0) {
  console.log('✓ PASS — todos os checks objetivos passaram.')
  console.log('  Restam os checks subjetivos: color strategy, hierarquia visível, AI slop test (ver references/design-quality.md §"Checklist Phase 4").')
  exit(0)
}

if (fails.length > 0) {
  console.log(`✗ ${fails.length} FAIL${fails.length > 1 ? 's' : ''}:`)
  fails.forEach(f => {
    const where = f.slideIdx ? `slide ${f.slideIdx}` : 'deck'
    console.log(`  [${f.code}] (${where}) ${f.msg}`)
    if (f.hint) console.log(`    → ${f.hint}`)
  })
  console.log('')
}

if (warns.length > 0) {
  console.log(`⚠ ${warns.length} WARN${warns.length > 1 ? 's' : ''}:`)
  warns.forEach(w => {
    const where = w.slideIdx ? `slide ${w.slideIdx}` : 'deck'
    console.log(`  [${w.code}] (${where}) ${w.msg}`)
    if (w.hint) console.log(`    → ${w.hint}`)
  })
  console.log('')
}

if (fails.length > 0) {
  console.log('🛑 Corrija os FAILs antes de declarar pronto. WARNs são opcionais mas revisão recomendada.')
  exit(1)
} else {
  console.log('✓ Sem FAILs. WARNs acima são opcionais — revise se vale ajustar.')
  exit(0)
}

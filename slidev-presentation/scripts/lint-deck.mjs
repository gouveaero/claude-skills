#!/usr/bin/env node
// lint-deck.mjs — Validação técnica de uma deck Slidev.
//
// Uso: node lint-deck.mjs <deck-path> [--no-build]
//
// Checa 9 categorias de erros que quebram decks em produção:
//   1. Caminhos de imagem inválidos (path absoluto para arquivo inexistente)
//   2. Componentes Vue usados sem o arquivo correspondente
//   3. Tags Iconify (<mdi-*>, <lucide-*>) sem o @iconify-json/<set> em deps
//   4. Layout inválido (não está nos 19 built-ins nem em layouts/*.vue)
//   5. CSS variables var(--foo) sem declaração correspondente
//   6. <v-clicks> / <v-click> components abertos sem fechamento
//   7. mdc: legacy no headmatter (renomeado pra comark: em v52.14)
//   8. Frontmatter com keys não-reconhecidas
//   9. npm run build dry-run (se --no-build passado, pula)
//
// Exit 0 = sem FAILs (WARNs OK).
// Exit 1 = FAILs encontrados.

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs'
import { join, resolve, relative } from 'node:path'
import { execSync } from 'node:child_process'

const BUILTIN_LAYOUTS = new Set([
  'center', 'cover', 'default', 'end', 'fact', 'full',
  'iframe', 'iframe-left', 'iframe-right',
  'image', 'image-left', 'image-right',
  'intro', 'none', 'quote', 'section', 'statement',
  'two-cols', 'two-cols-header',
])

const BUILTIN_COMPONENTS = new Set([
  // Click / reveal
  'VClick', 'VClicks', 'VAfter', 'VSwitch',
  // Layout / text
  'AutoFitText', 'Transform', 'Toc', 'Link', 'TitleRenderer',
  'SlideCurrentNo', 'SlidesTotal', 'LightOrDark',
  // Media
  'SlidevVideo', 'Youtube', 'Tweet', 'BlueSky',
  // Misc
  'RenderWhen', 'Arrow', 'PoweredBySlidev',
  // Drag
  'VDrag', 'VDragArrow',
])

// Headmatter / per-slide frontmatter keys reconhecidas
const KNOWN_HEADMATTER_KEYS = new Set([
  'theme', 'title', 'info', 'author', 'keywords',
  'transition', 'clickAnimation', 'mdc', 'comark',
  'fonts', 'colorSchema', 'aspectRatio', 'canvasWidth',
  'lineNumbers', 'monaco', 'htmlAttrs', 'download',
  'exportFilename', 'seoMeta', 'defaults', 'addons',
  'routerMode', 'selectable', 'presenter', 'record',
  'contextMenu', 'highlighter', 'drawings', 'shikiOptions',
  'features', 'remoteAssets', 'browserExporter',
  // Per-slide
  'layout', 'class', 'clicks', 'clicksStart',
  'level', 'hideInToc', 'routeAlias', 'zoom',
  'background', 'disabled', 'src', 'preload',
  // Layout-specific
  'image', 'url', 'backgroundSize',
])

// ANSI colors
const RED = '\x1b[31m'
const YELLOW = '\x1b[33m'
const GREEN = '\x1b[32m'
const DIM = '\x1b[2m'
const RESET = '\x1b[0m'

const fails = []
const warns = []

function fail(check, msg, hint = '') {
  fails.push({ check, msg, hint })
}
function warn(check, msg, hint = '') {
  warns.push({ check, msg, hint })
}

// ---------------------------------------------------------------------------
// Entry
// ---------------------------------------------------------------------------

const args = process.argv.slice(2)
const deckPath = resolve(args.find(a => !a.startsWith('--')) || '.')
const skipBuild = args.includes('--no-build')

if (!existsSync(deckPath)) {
  console.error(`${RED}Deck path not found: ${deckPath}${RESET}`)
  process.exit(2)
}

const slidesPath = join(deckPath, 'slides.md')
const packageJsonPath = join(deckPath, 'package.json')
const componentsDir = join(deckPath, 'components')
const layoutsDir = join(deckPath, 'layouts')
const stylesIndex = join(deckPath, 'styles', 'index.css')
const publicDir = join(deckPath, 'public')
const assetsDir = join(deckPath, 'assets')

if (!existsSync(slidesPath)) {
  console.error(`${RED}No slides.md in ${deckPath}${RESET}`)
  process.exit(2)
}

const slides = readFileSync(slidesPath, 'utf8')
const pkg = existsSync(packageJsonPath)
  ? JSON.parse(readFileSync(packageJsonPath, 'utf8'))
  : { dependencies: {}, devDependencies: {} }
const allDeps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) }

// Split slides by `---` separator. Each slide has optional frontmatter + body.
const rawSlides = slides.split(/^---\s*$/m)

// First chunk is empty (before initial ---), second is headmatter, third+ alternate frontmatter/body.
// Normalize: build a list of { frontmatter, body } per slide.
const parsedSlides = []
let i = 0
// Skip leading empty chunk
if (rawSlides.length > 0 && rawSlides[0].trim() === '') i = 1

// First "slide" is headmatter + first body
let headmatterText = ''
let firstBody = ''
if (i < rawSlides.length) {
  headmatterText = rawSlides[i]
  i++
  if (i < rawSlides.length) {
    firstBody = rawSlides[i]
    i++
  }
}
parsedSlides.push({ frontmatter: headmatterText, body: firstBody, isHeadmatter: true })

while (i + 1 < rawSlides.length) {
  parsedSlides.push({
    frontmatter: rawSlides[i],
    body: rawSlides[i + 1],
    isHeadmatter: false,
  })
  i += 2
}
// Trailing slide without explicit frontmatter
if (i < rawSlides.length) {
  parsedSlides.push({ frontmatter: '', body: rawSlides[i], isHeadmatter: false })
}

// ---------------------------------------------------------------------------
// Check 1: image paths
// ---------------------------------------------------------------------------

function checkImagePaths() {
  // Match <img src="..."> and ![alt](path)
  const imgTagRe = /<img\s+[^>]*src=["']([^"']+)["']/g
  const mdImgRe = /!\[[^\]]*\]\(([^)\s]+)/g
  const frontmatterImageRe = /^(?:image|background|url):\s*["']?([^\s"'\n]+)/gm

  const allMatches = [
    ...slides.matchAll(imgTagRe),
    ...slides.matchAll(mdImgRe),
    ...slides.matchAll(frontmatterImageRe),
  ]

  for (const m of allMatches) {
    const src = m[1]
    if (!src) continue
    // External / data URLs OK
    if (/^(https?:|data:|\/\/|mailto:)/i.test(src)) continue
    // /foo.png → must exist in public/
    if (src.startsWith('/')) {
      const target = join(publicDir, src.slice(1).split('?')[0])
      if (!existsSync(target)) {
        fail(
          'image-paths',
          `<img src="${src}"> referenced but ${relative(deckPath, target)} does not exist`,
          `Either move the file to public/ or use ./assets/<file> with the file in assets/.`,
        )
      }
      continue
    }
    // ./foo.png ou ~/foo.png ou relative
    let candidates = []
    if (src.startsWith('./')) {
      candidates.push(join(deckPath, src.slice(2).split('?')[0]))
    } else if (src.startsWith('~/')) {
      candidates.push(join(deckPath, src.slice(2).split('?')[0]))
    } else if (!src.startsWith('@')) {
      candidates.push(join(deckPath, src.split('?')[0]))
    }
    if (candidates.length > 0 && !candidates.some(c => existsSync(c))) {
      fail(
        'image-paths',
        `Image src="${src}" — file not found at ${candidates.map(c => relative(deckPath, c)).join(' or ')}`,
      )
    }
  }
}

// ---------------------------------------------------------------------------
// Check 2: components used vs available
// ---------------------------------------------------------------------------

function checkComponents() {
  // Match all tags. Vue/Slidev: PascalCase (e.g., <StatNumber>) or kebab-case (e.g., <stat-number>).
  // We're conservative — only flag PascalCase tags (kebab-case can be HTML).
  const tagRe = /<([A-Z][A-Za-z0-9]*)\b/g
  const used = new Set()
  for (const m of slides.matchAll(tagRe)) {
    used.add(m[1])
  }

  // Read components/*.vue
  let available = new Set()
  if (existsSync(componentsDir)) {
    for (const file of readdirSync(componentsDir)) {
      if (file.endsWith('.vue')) {
        const name = file.replace(/\.vue$/, '')
        available.add(name)
      }
    }
  }

  for (const tag of used) {
    if (BUILTIN_COMPONENTS.has(tag)) continue
    if (available.has(tag)) continue
    fail(
      'components',
      `<${tag}> used in slides.md but no components/${tag}.vue found and not a Slidev built-in`,
      `Create components/${tag}.vue (Phase 4 copies templates/components/ — make sure it ran).`,
    )
  }
}

// ---------------------------------------------------------------------------
// Check 3: Iconify deps
// ---------------------------------------------------------------------------

function checkIconify() {
  // Match <prefix-name /> patterns — likely Iconify.
  // Common Iconify prefixes: mdi, lucide, heroicons, carbon, tabler, phosphor, ph, fluent, material-symbols, etc.
  const tagRe = /<([a-z][a-z0-9]*)-[a-z][a-z0-9-]*(?:\s|\/|>)/g
  const prefixes = new Set()
  for (const m of slides.matchAll(tagRe)) {
    prefixes.add(m[1])
  }
  // Filter out known HTML tags and Vue directives
  const NON_ICONIFY = new Set(['v', 'data', 'web', 'svg', 'g', 'is'])
  for (const p of prefixes) {
    if (NON_ICONIFY.has(p)) continue
    const depName = `@iconify-json/${p}`
    if (!allDeps[depName]) {
      fail(
        'iconify',
        `Tag <${p}-*> used (Iconify-style) but ${depName} not in package.json`,
        `Run: npm i -D ${depName}`,
      )
    }
  }
}

// ---------------------------------------------------------------------------
// Check 4: layouts
// ---------------------------------------------------------------------------

function checkLayouts() {
  // Custom layouts available
  const customLayouts = new Set()
  if (existsSync(layoutsDir)) {
    for (const file of readdirSync(layoutsDir)) {
      if (file.endsWith('.vue')) {
        const name = file.replace(/\.vue$/, '')
        // Slidev resolves CamelCase ↔ kebab-case
        customLayouts.add(name)
        customLayouts.add(name.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase())
      }
    }
  }

  for (const [idx, slide] of parsedSlides.entries()) {
    const fm = slide.frontmatter
    const m = fm.match(/^layout:\s*([\w-]+)/m)
    if (!m) continue
    const layout = m[1].trim()
    if (BUILTIN_LAYOUTS.has(layout)) continue
    if (customLayouts.has(layout)) continue
    fail(
      'layouts',
      `Slide ${idx} uses layout: "${layout}" which is not a built-in (19 known) and no layouts/${layout}.vue found`,
      `Available built-ins: ${[...BUILTIN_LAYOUTS].sort().join(', ')}. Or create layouts/${layout}.vue.`,
    )
  }
}

// ---------------------------------------------------------------------------
// Check 5: CSS variables
// ---------------------------------------------------------------------------

function checkCssVars() {
  // Find all var(--foo) references
  const useRe = /var\(\s*(--[a-zA-Z0-9_-]+)/g
  const used = new Set()
  for (const m of slides.matchAll(useRe)) {
    used.add(m[1])
  }
  if (existsSync(stylesIndex)) {
    for (const m of readFileSync(stylesIndex, 'utf8').matchAll(useRe)) {
      used.add(m[1])
    }
  }

  // Find all declarations --foo: ...
  const declRe = /(--[a-zA-Z0-9_-]+)\s*:/g
  const declared = new Set()

  // Theme vars commonly available (rough heuristic — we trust them)
  const THEME_VARS = new Set([
    '--slidev-theme-primary', '--slidev-theme-bg',
    '--slidev-mdc-prose-h1-color', '--slidev-mdc-prose-h2-color',
    '--slidev-code-background', '--slidev-code-foreground',
    // Common Tailwind reset CSS vars
    '--tw-content', '--tw-border-spacing-x', '--tw-translate-x',
  ])

  // Declarations in styles/index.css
  if (existsSync(stylesIndex)) {
    for (const m of readFileSync(stylesIndex, 'utf8').matchAll(declRe)) {
      declared.add(m[1])
    }
  }
  // Declarations inside <style> blocks in slides.md
  for (const m of slides.matchAll(declRe)) {
    declared.add(m[1])
  }

  for (const v of used) {
    if (declared.has(v)) continue
    if (THEME_VARS.has(v)) continue
    if (v.startsWith('--slidev-')) continue // Slidev's own internal vars
    if (v.startsWith('--tw-') || v.startsWith('--un-')) continue // Tailwind / UnoCSS
    fail(
      'css-vars',
      `var(${v}) referenced but ${v}: never declared (not in styles/index.css :root nor in any <style> block)`,
      `Add to :root in styles/index.css: ${v}: <color>;`,
    )
  }
}

// ---------------------------------------------------------------------------
// Check 6: <v-clicks> / <v-click> component balance
// ---------------------------------------------------------------------------

function checkClickBalance() {
  for (const [idx, slide] of parsedSlides.entries()) {
    const body = slide.body
    // Count component-style usage (not directive). Tags only, not in code blocks.
    // Strip code fences first.
    const stripped = body.replace(/```[\s\S]*?```/g, '').replace(/`[^`]*`/g, '')

    const openClicks = (stripped.match(/<v-clicks(?:\s|>)/g) || []).length
    const closeClicks = (stripped.match(/<\/v-clicks>/g) || []).length
    const openClick = (stripped.match(/<v-click(?:\s|>)/g) || []).length
    const closeClick = (stripped.match(/<\/v-click>/g) || []).length

    if (openClicks !== closeClicks) {
      fail(
        'click-balance',
        `Slide ${idx}: <v-clicks> open=${openClicks} close=${closeClicks} (mismatched)`,
        `Make sure every <v-clicks> has matching </v-clicks>.`,
      )
    }
    if (openClick !== closeClick) {
      fail(
        'click-balance',
        `Slide ${idx}: <v-click> component open=${openClick} close=${closeClick} (mismatched)`,
        `Make sure every <v-click>...</v-click> closes. (directive <div v-click> is fine.)`,
      )
    }
  }
}

// ---------------------------------------------------------------------------
// Check 7: mdc: legacy
// ---------------------------------------------------------------------------

function checkMdcLegacy() {
  const headmatter = parsedSlides[0]?.frontmatter || ''
  if (/^mdc:\s*true/m.test(headmatter)) {
    warn(
      'mdc-legacy',
      `Headmatter has "mdc: true" — renamed to "comark: true" in v52.14`,
      `Replace with comark: true (or remove if you don't need MDC features).`,
    )
  }
}

// ---------------------------------------------------------------------------
// Check 8: frontmatter keys
// ---------------------------------------------------------------------------

function checkFrontmatterKeys() {
  for (const [idx, slide] of parsedSlides.entries()) {
    const fm = slide.frontmatter
    // Match top-level keys (not indented)
    const keyRe = /^([a-zA-Z][\w-]*)\s*:/gm
    for (const m of fm.matchAll(keyRe)) {
      const key = m[1]
      if (KNOWN_HEADMATTER_KEYS.has(key)) continue
      warn(
        'frontmatter-keys',
        `Slide ${idx}: frontmatter key "${key}" not recognized as standard Slidev key`,
        `Common typos: clickAnimation vs clickanimation. Check spelling against references/v52-features.md.`,
      )
    }
  }
}

// ---------------------------------------------------------------------------
// Check 9: build dry-run
// ---------------------------------------------------------------------------

function checkBuild() {
  if (skipBuild) return
  if (!existsSync(join(deckPath, 'node_modules'))) {
    warn(
      'build',
      `node_modules not found — skipping build dry-run. Run npm install first if you want this check.`,
    )
    return
  }
  try {
    execSync(`npm run build -- --base /LINT_TEST/`, {
      cwd: deckPath,
      stdio: 'pipe',
      timeout: 120_000,
    })
  } catch (e) {
    const out = (e.stdout?.toString() || '') + (e.stderr?.toString() || '')
    const tail = out.split('\n').slice(-15).join('\n')
    fail(
      'build',
      `npm run build failed — see error below`,
      tail,
    )
  }
}

// ---------------------------------------------------------------------------
// Run all checks
// ---------------------------------------------------------------------------

checkImagePaths()
checkComponents()
checkIconify()
checkLayouts()
checkCssVars()
checkClickBalance()
checkMdcLegacy()
checkFrontmatterKeys()
checkBuild()

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

console.log(`\n${DIM}lint-deck.mjs — ${relative(process.cwd(), deckPath) || '.'}${RESET}\n`)

if (fails.length === 0 && warns.length === 0) {
  console.log(`${GREEN}✓ All checks passed.${RESET}`)
  process.exit(0)
}

if (fails.length > 0) {
  console.log(`${RED}✗ ${fails.length} FAIL${fails.length === 1 ? '' : 's'}${RESET}\n`)
  for (const f of fails) {
    console.log(`  ${RED}[${f.check}]${RESET} ${f.msg}`)
    if (f.hint) console.log(`     ${DIM}→ ${f.hint}${RESET}`)
  }
  console.log()
}

if (warns.length > 0) {
  console.log(`${YELLOW}⚠ ${warns.length} warning${warns.length === 1 ? '' : 's'}${RESET}\n`)
  for (const w of warns) {
    console.log(`  ${YELLOW}[${w.check}]${RESET} ${w.msg}`)
    if (w.hint) console.log(`     ${DIM}→ ${w.hint}${RESET}`)
  }
  console.log()
}

process.exit(fails.length > 0 ? 1 : 0)

---
name: slidev-carousel
description: Use when the user wants Instagram carousels with animated reveals, cinematic motion, Mermaid diagrams, or any visual richness beyond static HTML. Covers feed posts (4:5 portrait, 1080×1350, recommended), square (1:1), and Instagram/TikTok story (9:16). Triggers "carrossel", "carrossel Instagram", "IG carousel", "carrossel animado", "post carrossel", "slides Instagram", "thread visual", "carousel para LinkedIn"; also triggers when `/carousel-generator` (static HTML+Playwright) feels too flat for the content — e.g. user mentions "preciso de algo cinematográfico", "quero animação", "tipo Magic Move", or wants reveal sequences. Output: editable Slidev source in `<project>/presentations/<slug>/` + numbered PNG exports in `exports/` subfolder. NO deploy — output is for Instagram upload. Bakes in AIDA structure (hook→educate→CTA), ≤12 words/slide cap, 6–13 slides count, panoramic continuity via global layer. Use this even when the user doesn't say "Slidev" — if the request is for an animated/cinematic carousel, this beats `/carousel-generator`.
argument-hint: [file-path | topic-description]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion
---

# Slidev Carousel — Cinematic Instagram Carousels

## Goal

Produce an Instagram carousel (or LinkedIn / TikTok / story variant) as a Slidev project. The final deliverable is a folder `<project>/presentations/<slug>/` containing `slides.md` + the pre-wired carousel component library, plus an `exports/` subfolder with numbered PNGs (`01.png`…`NN.png`) at the chosen aspect ratio, ready for upload.

## Why this skill exists

Static HTML carousels (`/carousel-generator`) hit a ceiling fast: no reveals, no motion choreography, no diagrams, no AutoFitText. Slidev gives you the entire animation engine, and the PNG exporter captures the final frame of each slide — so reveal-style sequences, Mermaid diagrams, Iconify, and panoramic continuity all survive into the export. This skill bakes Instagram 2026 best practices (AIDA, ≤12 words/slide, 6–13 slide cap, pattern interrupters, panoramic continuity) directly into the briefing and outline phases, so the generated carousel publishes well by default. For the full Slidev feature surface, see `slidev-presentation`'s `references/` — this skill curates the subset that survives PNG export.

---

## The 5 phases (mandatory order)

### Phase 1 — Intake

Read any file referenced by `$ARGUMENTS` (use Read / Glob). Identify in 3–4 bullets:

- **Topic / thesis** in one line
- **Existing material** (article, transcript, raw notes, outline?)
- **Tone signals** (didático, provocativo, técnico, comercial)
- **Language** of the source (default PT-BR, match input)

### Phase 2 — Discovery

Batch the clarifying questions into a single `AskUserQuestion` call. Skip any question Phase 1 already answered.

Question bank (carousel-specific additions in bold):

1. **Tema central** — qual a tese / mensagem em uma frase?
2. **Público** — devs, founders, gestores, audiência ampla?
3. **Takeaway** — o que a pessoa salva / faz depois?
4. **Tom** — didático, provocativo, conversational, formal?
5. **Aspect ratio** — `4/5` portrait 1080×1350 (default, recomendado IG feed), `1/1` square 1080×1080, ou `9/16` story 1080×1920?
6. **Handle do CTA** — default `@gouveaero`. Confirma ou troca?
7. **Cores da marca** — usar paleta default (high-contrast teal/indigo/pink) ou usuário tem brand colors?
8. **Idioma** — PT ou EN?
9. **Pasta de destino** — default `<projeto-atual>/presentations/<slug>/`. Slug sugerido derivado do título.

Confirme em uma frase curta o que entendeu antes de ir pro outline. **Não pergunte sobre deploy** — carrossel não deploya.

### Phase 3 — Outline approval

Produza uma tabela slide-a-slide aplicando **AIDA**:

| # | Tipo | Função AIDA | Layout | Componente | Palavras |
|---|------|-------------|--------|------------|----------|
| 1 | Hook | Attention | `cover` | `<HookSlide>` | ≤12 |
| 2 | Curiosity | Interest | `quote` ou `statement` | `<QuoteReveal>` ou `<CalloutBadge>` | ≤12 |
| 3 | Stakes | Interest | `fact` | `<StatNumber>` ou `<CalloutBadge>` | ≤12 |
| 4 | Step 1 | Desire | `default` | `<StepCard>` | ≤12 |
| 5 | Step 2 | Desire | `default` | `<StepCard>` | ≤12 |
| 6 | Pattern interrupter | Desire | `statement` | `<CalloutBadge>` (pulse) | ≤12 |
| 7 | CTA | Action | `end` | `<CTASlide>` | ≤12 |

**Enforce ANTES de pedir aprovação:**

- **6 ≤ slide count ≤ 13** → se fora, ajuste e explique. Curto demais perde narrativa; longo demais mata engajamento.
- **≤12 palavras por slide** → conte. Se algum estourou, reescreva. Razão: <0.7s read time per IG research (Hootsuite 2025, Pano).
- **AIDA presente:** slide 1 hook, último slide CTA, pelo menos 1 pattern interrupter no meio.
- **Continuidade panorâmica:** proponha o elemento visual que atravessa os slides (linha que cresce, número que sobe, persona andando, gráfico que se completa) — implementado via `global-bottom.vue`.

**Se alguma regra falhou**, REJEITE o outline com a razão explícita. Não peça aprovação até estar conforme.

Detalhes em `references/carousel-patterns.md`.

Termine com a pergunta literal: **"Aprova esse outline? Posso gerar o carrossel?"** Não gere sem aprovação.

### Phase 4 — Generation

1. **Confirme o destino** — default `<projeto>/presentations/<slug>/`. Se existe e não está vazio, pergunte antes de sobrescrever.
2. **Copie templates**: `cp -r "<SKILL_DIR>/templates/." "<TARGET>/"` (Bash).
3. **Escreva `slides.md`** expandindo o outline. Para cada slide:
   - 1 ideia central, ≤12 palavras.
   - Componente carousel-específico quando o outline indicar.
   - Notas do apresentador em `<!-- -->` (úteis pra revisão, ignoradas no export).
   - `transition:` per-slide só pra dev preview — PNG export não captura transição.
4. **Atualize `package.json`**: `"name"` = `<slug>`.
5. **Ajuste headmatter de `slides.md`** com o aspect ratio escolhido:
   - 4:5 portrait → `aspectRatio: '4/5'`, `canvasWidth: 1080` (default no template)
   - 1:1 square → `aspectRatio: '1/1'`, `canvasWidth: 1080`
   - 9:16 story → `aspectRatio: '9/16'`, `canvasWidth: 1080`
6. **Anti-goto-panel CSS já vem em `styles/index.css`**.
7. **Instale deps em background**: `cd <TARGET> && npm install` (run_in_background).
8. **Valide contagem de palavras**: rode `<SKILL_DIR>/scripts/count-words-per-slide.sh <TARGET>/slides.md`. Se exit 1, corrija antes de seguir.
9. **Suba o dev server em background**: `cd <TARGET> && npm run dev`. Capture URL (geralmente `http://localhost:3030`).
10. **Verificação visual com Chrome DevTools MCP**: `navigate_page` + `take_screenshot` slide-a-slide. Checklist: ≤12 palavras visíveis, foco único por slide, contraste OK, panoramic element aparecendo. Corrija antes de seguir.

### Phase 5 — Export

1. **Rode** `<SKILL_DIR>/scripts/export-carousel.sh <TARGET>`. O script:
   - Detecta aspect ratio do headmatter de `slides.md` (4/5, 1/1, 9/16).
   - Roda `slidev export --format png --output ./exports/`.
   - Verifica dimensões de cada PNG via `sips`. Aborta se divergente.
   - Renomeia para `01.png`, `02.png`, ... `NN.png` (já sai assim do slidev export, script só valida).
2. Reporte ao usuário:
   - Caminho da pasta `exports/`.
   - Quantos PNGs gerados.
   - Dimensões confirmadas.
   - Instrução de upload (Instagram → novo post → selecionar múltiplas imagens na ordem).
3. **Não deploya nada.** Carrossel termina no PNG.

---

## Feature surface — quais features sobrevivem ao PNG export

Slidev export pega 1 frame final por slide. Isso muda o que vale a pena usar:

| Quando o slide é... | Use | Sobrevive PNG? | Docs |
|---|---|---|---|
| Hook com texto que precisa caber | `<HookSlide>` (usa `<AutoFitText>`) | ✅ | `references/components.md` |
| Passo numerado | `<StepCard>` com `v-motion` stagger | ✅ (frame final) | `references/components.md` |
| Estatística protagonista | `<StatNumber>` + layout `fact` | ✅ | `references/components.md` |
| Citação ou linha provocativa | `<QuoteReveal>` (`autoPlay`) + layout `quote` | ✅ (frame final) | `references/components.md` |
| Badge "alerta" / "destaque" | `<CalloutBadge>` (pulse animation) | ✅ | `references/components.md` |
| CTA final | `<CTASlide>` (handle + framing) | ✅ | `references/components.md` |
| Continuidade visual entre slides | `<PanoramicElement>` via `global-bottom.vue` | ✅ **CRÍTICO** | `references/components.md` |
| Diagrama (flowchart, decision tree, sequence) | Mermaid (`````mermaid `) | ✅ | `slidev-presentation/references/diagrams.md` |
| Ícone vetorial | Iconify (`<mdi-arrow-right />`, `<heroicons-bolt-solid />`) | ✅ | `slidev-presentation/references/components.md` |
| Reveal staged dentro do slide | **NÃO** — cada estágio vira slide separado no carrossel | ⚠️ | `references/animations.md` |
| Magic Move de código | **NÃO** — cada estado vira slide separado | ⚠️ | `references/animations.md` |
| Vue form reativa, Monaco editor, `v-drag` | Não use | ❌ | `references/feature-matrix.md` |

Tabela completa em `references/feature-matrix.md`.

### Layouts (curado pra carrossel)

| Slide é... | Layout |
|---|---|
| Hook (slide 1) | `cover` + `<HookSlide>` |
| Estatística que prende | `fact` + `<StatNumber>` |
| Citação ou linha provocativa | `quote` + `<QuoteReveal>` |
| Manifesto / CTA grande / pattern interrupter | `statement` |
| Passo numerado | `default` + `<StepCard>` |
| Imagem dominante | `image` |
| Final / CTA | `end` + `<CTASlide>` |
| Default catch-all | `default` |

Detalhes + layouts a evitar em `references/layouts.md`.

---

## Hard rules

- **NEVER skip** Discovery (Phase 2) nem Outline approval (Phase 3).
- **NEVER aprove um outline com slide >12 palavras** — conta antes, rejeita e reescreve.
- **NEVER gere carrossel com <6 ou >13 slides** — fora do ótimo.
- **NEVER use** `<v-drag>`, Monaco, Vue forms reativas, Twoslash hover — interatividade morre no PNG.
- **NEVER pule** o script `count-words-per-slide.sh` na Phase 4.
- **Idioma**: default PT-BR. Match o idioma do input quando diferente.

## Rationalization closure

| Tentação | Realidade | Faça |
|---|---|---|
| "Vou colocar 20 palavras nesse slide pra dar contexto" | Cap rígido é 12 — read time <0.7s per IG research (Hootsuite 2025) | Quebre em 2 slides ou corte |
| "Carrossel pode ter 15 slides, mais conteúdo é melhor" | 6–13 é o ótimo; >13 derruba engajamento (FlowShorts 2026) | Cortar até 13, ou virar 2 carrosséis |
| "Animation? Carrossel é PNG, não rola" | `v-motion` + `v-click` capturam o frame FINAL — composição visual ainda ganha profundidade | Use animação pelo enquadramento final, ver `references/animations.md` |
| "Vou pular o pattern interrupter pra ficar mais limpo" | Sem quebra, engajamento despenca — 1-2 slides surpresa duplicam saves | Force ao menos 1 (`<CalloutBadge>`, pergunta provocativa, contraintuitivo) |
| "Continuidade panorâmica é detalhe estético" | É o que faz a sequência parecer 1 narrativa contínua ao invés de 7 cards soltos | Sempre proponha o elemento no outline + implementa em `global-bottom.vue` |
| "Magic Move funciona, faço refactoring de código" | PNG export captura 1 frame por slide — animação se perde | Cada estado vira slide separado |

## Red flags — pare e releia as references/

- "Vou colocar mais de 12 palavras nesse slide" → `references/carousel-patterns.md` §"Cap rígido"
- "Vou fazer 15 slides porque o tema é denso" → `references/carousel-patterns.md` §"Slide count"
- "Pulei o hook, fui direto pro conteúdo" → `references/carousel-patterns.md` §"AIDA"
- "Cada slide é uma ilha, sem continuidade" → `references/components.md` §"PanoramicElement"
- "Vou usar magic-move / v-drag / Vue form" → `references/feature-matrix.md`

---

## Output ao final da Phase 5

Reporte:

1. Caminho da pasta gerada (`<projeto>/presentations/<slug>/`).
2. Caminho dos PNGs (`<projeto>/presentations/<slug>/exports/01.png`…`NN.png`).
3. Dimensões confirmadas (1080×1350 / 1080×1080 / 1080×1920).
4. Quantidade de slides + features-chave usadas (ex: "8 slides, 1 hook + 4 steps + 1 pattern interrupter + 1 CTA, panoramic line growing").
5. Instrução de upload: Instagram → Novo post → Selecionar múltiplas → PNGs na ordem `01` → `NN`.
6. "Quer ajustar o hook, trocar o pattern interrupter, ou iterar em algum slide específico?"

## Iteração

- Mudar conteúdo → `Edit` em `slides.md` → re-rodar `export-carousel.sh`.
- Adicionar slide → respeitar cap 13; rodar `count-words-per-slide.sh`.
- Trocar aspect ratio → editar headmatter (`aspectRatio`, `canvasWidth`) → re-export.
- Brand color → editar `styles/index.css` `:root` variables.
- Handle / CTA wording → prop em `<CTASlide handle="..." cta-text="..." />`.

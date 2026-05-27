---
name: slidev-presentation
description: Use when the user wants to build a presentation, slides, deck, palestra, pitch, keynote, talk, dev conference apresentação, demo deck, sales pitch, conference talk, or anything beyond a vanilla bullet list — including animated technical talks, code walkthroughs with Shiki Magic Move, Mermaid/PlantUML diagrams, LaTeX equations, Vue 3 reactive polls/calculators embedded in slides, and Iconify icons. Triggers include "apresentação", "slides", "deck", "pitch", "keynote", "palestra", "talk", "apresentar", "evento", "conferência", "demo", or any mention of cinematic transitions, animated reveals, dev-conference style, or "preciso mostrar X pro time/cliente/banca". Auto-deploys decks to `slides.gabrielgouvea.com.br/<slug>` when the user wants to share the URL. Use this even when the user doesn't say "Slidev" — if they need slides cinematográficos with code + diagramas + animações, or anything where `canva-presentation` would feel too static, this is the right skill. Do NOT use for Instagram carousels (use `slidev-carousel`) or Canva-hosted decks (use `canva-presentation`).
argument-hint: [file-path | topic-description]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, WebFetch
---

# Slidev Technical Presentation — Cinematic Dev Decks

## Goal

Produce a cinematic, animated presentation as a Slidev project. The final deliverable is a folder (`<project>/presentations/<slug>/`) containing `slides.md`, the pre-wired component library, a running local dev preview, and — optionally — a deployed URL at `slides.gabrielgouvea.com.br/<slug>`.

## Why this skill exists

Slidev is a powerful presentation framework with ~60 documented features (animations, code-transitions, diagrams, interactive Vue components, layouts). Vanilla decks use about 5 of them. This skill encodes the full surface so every deck reaches the visual ceiling Slidev offers, while keeping authoring markdown-first.

When in doubt, **lean on Slidev natives over hand-rolled CSS**. The native `transition: slide-left`, `v-motion`, `magic-move`, `<AutoFitText>`, and `<Toc>` are battle-tested and integrate with Slidev's click system.

---

## The 5 phases (mandatory order)

### Phase 1 — Intake

Read any file referenced by `$ARGUMENTS` (use Read / Glob). Identify in 3–4 bullets:

- **Domain** (web, ML, infra, aviação, marketing, acadêmico, ...)
- **Existing structure** (outline? transcript? raw notes? article?)
- **Tone signals** (formal/casual, didático/provocativo, técnico/comercial)
- **Technical artifacts** (snippets, dados, diagramas, fórmulas, links)
- **Language** of the source

### Phase 2 — Discovery

Batch the clarifying questions into a single `AskUserQuestion` call. Skip any question whose answer Phase 1 already revealed.

Question bank:

1. **Tema central** — qual a tese/mensagem principal em uma frase?
2. **Público** — devs, gestores, banca acadêmica, audiência mista?
3. **Duração** — minutos de fala + Q&A?
4. **Takeaway** — o que o público lembra/faz depois?
5. **Tom** — formal, casual, provocativo, didático, inspiracional?
6. **Estética** — minimalista, cinematográfico, corporativo, editorial, brutalist? Referências (links/imagens)?
7. **Código/dados** — quais snippets, números, diagramas devem aparecer?
8. **Idioma** — PT ou EN?
9. **Pasta de destino** — default: `<projeto-atual>/presentations/<slug>/`. Slug sugerido derivado do título.
10. **Deploy** — esse deck vai pro ar em `slides.gabrielgouvea.com.br/<slug>`? Se sim, confirma o slug ou pede outro.

Confirme em uma frase curta o que entendeu antes de ir pro outline.

### Phase 3 — Outline approval

Produza uma tabela slide-a-slide. **Número de slides é função do tempo de fala e da densidade** — não há template fixo. Use um dos 3 shapes abaixo como ponto de partida e ajuste.

#### Shape A — Curto (5–7 slides, 5–12 min)

Pitch rápido, demo, comunicado interno, anúncio.

| # | Propósito | Layout | Feature destaque |
|---|---|---|---|
| 1 | Hook + tese em 1 frase | `cover` | `<AutoFitText>` |
| 2 | Problema | `fact` ou `statement` | `<StatNumber>` |
| 3 | Solução | `default` ou `two-cols` | Imagem ou Mermaid |
| 4 | Como funciona | `default` | Magic Move ou Mermaid |
| 5 | Resultado | `fact` | `<StatNumber>` + `<v-clicks>` |
| 6 | CTA | `statement` | `<v-clicks>` + Iconify |
| 7 | (opcional) Obrigado/contato | `end` | — |

#### Shape B — Médio (8–12 slides, 15–25 min)

Palestra técnica de meetup, aula de bootcamp, sales pitch B2B.

| # | Propósito | Layout sugerido | Feature destaque |
|---|---|---|---|
| 1 | Hook | `cover` | `<AutoFitText>` |
| 2 | Bio rápida | `intro` | — |
| 3 | Tese / por que importa | `quote` ou `statement` | `<QuoteReveal>` |
| 4 | Estado atual / problema | `fact` | `<StatNumber>` |
| 5 | Mergulho técnico A | `default` | Magic Move ou snippet `<<<` |
| 6 | Diagrama de arquitetura | `default` | Mermaid |
| 7 | Mergulho técnico B | `two-cols` ou `image-right` | Comparison ou print |
| 8 | Resultado / métricas | `default` | `<MetricGrid>` |
| 9 | Lições / takeaways | `statement` | `<v-clicks>` |
| 10 | Próximos passos / CTA | `default` | `<v-clicks>` + Iconify |
| 11 | Obrigado + contato | `end` | `<QuoteReveal>` |

#### Shape C — Longo (13–20 slides, 30–60 min)

Keynote, workshop, defesa acadêmica, deep-dive interno.

Estrutura recomendada (capítulos):
- Abertura (1–2): cover + intro
- Setup do problema (2–3): quote/fact + statement + dados
- **Section break** (`layout: section`) entre capítulos
- Conteúdo principal em 2–3 capítulos de 3–5 slides cada
- Demo ou interatividade (1–2): `<InteractivePoll>`, `<ROICalculator>`, iframe live
- Síntese e takeaways (1–2): statement + Toc
- Encerramento (1): end

Guidelines de ritmo:
- Alterne slides densos com slides "respiro" (1 imagem grande, 1 frase, 1 número).
- **Variar layouts** — se >60% do deck for `default` ou `center`, está sub-utilizando os 17 outros. Use 5+ layouts diferentes por deck.
- **Variar transições com intenção** — headmatter `transition: slide-left | slide-right` + `clickAnimation: up` define o tom; quebre só em pontos narrativos (section break = `fade`, fact de impacto = `zoom`, comparação A→B no mesmo frame = `view-transition`).
- **Coerência > novidade** — um deck inteiro com mesmo estilo de reveal (`up`) parece intencional; um deck com 5 estilos diferentes parece bagunçado.

Termine com a pergunta literal: **"Aprova esse outline? Posso gerar a apresentação?"** Não gere sem aprovação explícita.

### Phase 4 — Generation

1. **Confirme o destino** — default `<projeto>/presentations/<slug>/`. Se a pasta já existe e não está vazia, pergunte antes de sobrescrever.
2. **Copie templates**: `cp -r "<SKILL_DIR>/templates/." "<TARGET>/"` (Bash, não Glob).
3. **Escreva `slides.md`** expandindo o outline. Para cada slide:
   - Título + subtítulo curto.
   - 1 ideia central; usar `<v-clicks>` / componente custom para reveal progressivo.
   - Quando o outline indicou um componente, use com props realistas.
   - Notas do apresentador em `<!-- ... -->` ao final.
   - `transition:` per-slide só quando muda o ritmo deliberadamente.
   - Indentação de `<v-click>`: 0 ou 2 espaços (ver `references/animations.md` §"v-click pitfalls").
4. **Atualize `package.json`**: `"name"` = `<slug>`.
5. **Anti-goto-panel CSS já vem em `styles/index.css`** (regra `.autocomplete-list { display: none !important; }`).
6. **Instale deps em background**: `cd <TARGET> && npm install` (run_in_background).
7. **Suba o dev server em background**: `cd <TARGET> && npm run dev`. Capture a URL (geralmente `http://localhost:3030`).
8. **Verificação visual slide a slide (OBRIGATÓRIO antes de reportar ao usuário)** — Chrome DevTools MCP:
   - `navigate_page → http://localhost:3030/1` → `take_screenshot` → ver
   - Repetir para todos os slides
   - Checklist por slide: título não aparece como "undefined" no sidebar; conteúdo de primeiro nível visível; nenhum overflow; componentes custom renderizam.
   - **Se algo falhar, corrija antes de reportar.** Bugs conhecidos em `references/components.md` §"Pitfalls".

### Phase 4.5 — Validação (obrigatório antes de declarar pronto)

Dois checks complementares, ambos precisam passar (exit 0) antes da Phase 5 ou de reportar pronto.

#### Phase 4.5a — `lint-deck.mjs` (correção técnica)

Checa problemas que quebram a deck em produção. Roda **primeiro** (sem dev server, rápido).

```bash
node "<SKILL_DIR>/scripts/lint-deck.mjs" "<TARGET>"
```

Cobre:
- Caminhos de imagem inválidos (`<img src="/foo">` sem `public/foo` correspondente).
- Componentes usados sem o arquivo `components/*.vue` correspondente.
- Iconify tags (`<mdi-*>`, `<lucide-*>`) sem `@iconify-json/<set>` em deps.
- Layouts inválidos (não está nos 19 built-ins nem em `layouts/*.vue`).
- `var(--foo)` referenciada sem `--foo:` declarado em algum `:root` ou `<style>` do mesmo slide.
- `<v-clicks>` / `<v-click>` (component) abertos sem fechamento correspondente.
- `mdc:` legacy no headmatter (WARN — sugere migrar para `comark:`).
- `npm run build --base /TEST/` dry-run (FAIL se quebrar).

Saída: relatório markdown com FAILs (bloqueiam) e WARNs (informam). Sem FAIL → exit 0.

#### Phase 4.5b — `self-critique.mjs` (qualidade estética)

Roda **depois** do lint, opcionalmente com dev server up para checks visuais.

```bash
node "<SKILL_DIR>/scripts/self-critique.mjs" "<TARGET>" --visual --url http://localhost:3030/<slug>
# Ou sem visual (só estático, mais rápido):
node "<SKILL_DIR>/scripts/self-critique.mjs" "<TARGET>"
```

Cobre estética:
- Word count, H1 count, layout monoculture, gradient text, em-dash overuse, side-stripe borders, pure #000/#fff, identical card grids, glassmorphism overuse, font count, premium features uso.
- Com `--visual`: element overflow do slide bounds, color count por slide.

**Hard rule**: ambos exit 0 (sem FAILs) é pré-requisito pra reportar pronto.

Workflow ordenado:
1. Após escrever `slides.md` → rodar `lint-deck.mjs`. FAILs aqui são **estruturais** (imports, paths, layouts inválidos) — corrigir.
2. Re-rodar `lint-deck.mjs` até exit 0.
3. Rodar `self-critique.mjs` estático.
4. Subir dev server (`npm run dev` background).
5. Rodar `self-critique.mjs --visual --url <localhost>/<slug>`.
6. Corrigir FAILs visuais.
7. Sweep manual no Chrome DevTools MCP (Phase 4 §8) — checks subjetivos.

Os checks **subjetivos** (color strategy commitida, hierarquia visível, AI slop test, register brand-vs-product) ficam pra você durante Phase 4 — leia `references/design-quality.md` antes de gerar slides.md. Os critiques automáticos são safety net, não substituto do julgamento.

### Phase 5 — Deploy (condicional — só se Phase 2 confirmou)

Se o usuário pediu deploy:

1. Build estático: `cd <TARGET> && npm run build -- --base /<slug>/`
2. Executar `<SKILL_DIR>/scripts/deploy-to-hub.sh <slug>` — esse script faz todo o resto:
   - Verifica se `slides-hub` repo existe local; se não, clona ou cria via `setup-hub.sh`.
   - Copia `dist/` → `slides-hub/decks/<slug>/`.
   - `git add/commit/push`. Coolify detecta e redeploy automaticamente.
   - Poll Coolify API até deploy completar.
   - `curl -I https://slides.gabrielgouvea.com.br/<slug>/` → confirma 200.
3. Reporte ao usuário a URL pública.

Detalhes do fluxo em `references/deploy.md`. Setup único do hub em `references/setup-hub.md`.

---

## Feature surface — sempre consulte antes de gerar

Slidev oferece muito mais que `v-click` + Shiki. Para qualquer slide, primeiro avalie se uma feature mais expressiva cabe.

**Versão atual** (set/2024 → mai/2026): mudanças em v0.48+ (sistema de clicks reescrito, presets nomeados, alerts nativos, `comark:` renamed de `mdc:`) estão em `references/v52-features.md`. **Sempre consulte** antes de gerar — features ali são frequentemente as que distinguem uma deck cinematográfica de uma deck plana.

**Design quality (LEIA ANTES DE ESCREVER SLIDES.md)**: `references/design-quality.md` — princípios curados de UI/UX adaptados para deck (register brand/product, color strategy 4 níveis, tipografia em slides, banimentos absolutos, AI slop test, checklist Phase 4). Os checks objetivos rodam automaticamente em Phase 4.5, mas os subjetivos (color strategy, hierarquia, AI slop) só você consegue julgar — interna-los antes de escrever evita iterações.

| Quando o slide é... | Use | Documentado em |
|---|---|---|
| Reveal de uma lista, parágrafo, ou step | `<v-click>`, `<v-clicks>`, `<v-after>`, presets `.scale` / `.fade.right` / `.up` | `references/animations.md` |
| Callout inline em texto (note, warning, etc.) | `> [!NOTE]`, `> [!WARNING]`, `> [!TIP]` (v52.15+) | `references/v52-features.md` |
| Migrar deck antiga com `mdc: true` | Trocar para `comark: true` (renamed v52.14) | `references/v52-features.md` |
| Embed de post BlueSky | `<BlueSky post="...">` (v52.15+) | `references/v52-features.md` |
| Movimento posicional / stagger / scale-bounce | `v-motion` (com `@vueuse/motion`) | `references/animations.md` |
| Alternar estado A → B (problema vs solução, antes vs depois) | `<v-switch>` ou `<ComparisonSplit>` | `references/animations.md` + `references/components.md` |
| Antes/depois de código com transição animada | **Shiki Magic Move** (bloco `````magic-move`) | `references/code-features.md` |
| Tipos TS inline + erros de compilação como pop-ups | Twoslash (` ```ts twoslash `) | `references/code-features.md` |
| Bloco de código editável ao vivo (demo interativa) | Monaco editor (`{monaco}`) ou runner (`{monaco-run}`) | `references/code-features.md` |
| Código real do projeto (não duplicar nos slides) | Import snippet `<<< @/snippets/file.ts {2-5}` | `references/code-features.md` |
| Diagrama de arquitetura, sequência, ER, state | **Mermaid** (`````mermaid {theme: 'neutral'}`) | `references/diagrams.md` |
| UML formal, ArchiMate, BPMN | PlantUML / Kroki | `references/diagrams.md` |
| Fórmula matemática, equação, química | LaTeX `$$ ... $$ {1\|3\|all}` (KaTeX + mhchem) | `references/diagrams.md` |
| Elemento reposicionável durante apresentação ao vivo | `<v-drag>`, `<v-drag-arrow>` | `references/interactive.md` |
| Slide interativo (poll, calculadora ao vivo, slider reativo) | Vue 3 `<script setup>` + `<InteractivePoll>` / `<ROICalculator>` | `references/interactive.md` |
| 150k+ ícones vetoriais | Iconify `<mdi-arrow-right />`, `<heroicons-bolt-solid />` | `references/components.md` |
| Texto que precisa caber em uma caixa específica | `<AutoFitText>` | `references/components.md` |
| Embed de vídeo, YouTube, tweet, Bluesky | `<SlidevVideo>`, `<Youtube>`, `<Tweet>`, `<BlueSky>` | `references/components.md` |
| Slide muito denso que não cabe sem reescrever | `zoom: 0.8` no frontmatter | `references/interactive.md` |
| Background animado persistente, watermark contínuo | Global layers (`global-top.vue`, `global-bottom.vue`) | `references/styling.md` |
| CSS isolado por slide, sem poluir o resto | `<style scoped>` dentro do slide | `references/styling.md` |
| Notas que só o apresentador vê | `<RenderWhen context="presenter">...</RenderWhen>` + notas em `<!-- -->` | `references/components.md` |

### Layouts (19 built-in, mapeados em `references/layouts.md`)

Lista canônica dos 19 (verificada em `slidevjs/slidev/packages/client/layouts/`):
`center`, `cover`, `default`, `end`, `fact`, `full`, `iframe`, `iframe-left`, `iframe-right`, `image`, `image-left`, `image-right`, `intro`, `none`, `quote`, `section`, `statement`, `two-cols`, `two-cols-header`.

| Slide é... | Layout |
|---|---|
| Capa formal com título grande | `cover` |
| Apresentação do autor / contexto inicial | `intro` |
| Separador de capítulo | `section` |
| Citação destacada | `quote` |
| Afirmação grande (manifesto) | `statement` |
| Número/estatística protagonista | `fact` |
| Imagem como conteúdo principal | `image` |
| Split com imagem à esquerda/direita | `image-left` / `image-right` |
| Embed de web page durante demo | `iframe` / `iframe-left` / `iframe-right` |
| 2 colunas balanceadas | `two-cols` (slot default + `::right::`, **nunca** `::left::` em `two-cols` — slot inexistente) |
| Header full-width + 2 colunas abaixo | `two-cols-header` (aqui `::left::` e `::right::` ambos funcionam) |
| Padding zero, slide preenche viewport | `full` |
| Encerramento | `end` |
| Conteúdo geral / default | `default` |
| Sem estilização, layout livre | `none` |
| Conteúdo centrado vertical e horizontalmente | `center` |

**Se precisar de layout que não está nessa lista, crie custom em `layouts/<Nome>.vue` da deck** — não invente nome de built-in. Slidev fallback silencioso quando layout não existe. Ver `references/layouts.md` § "Custom layouts".

### Componentes custom (em `templates/components/`)

| Componente | Quando usar |
|---|---|
| `<CodeReveal>` | Walkthrough passo-a-passo de código com nota lateral |
| `<StatNumber>` | Counter animado 0→target (uptime, ROI, deploys/dia) |
| `<ArchitectureFlow>` | Diagrama SVG com coordenadas precisas (reveal nó-a-nó) |
| `<TerminalDemo>` | Sessão CLI simulada com typing |
| `<QuoteReveal>` | Citação revelada palavra-por-palavra |
| `<MetricGrid>` | Grid 2×2 ou 3×1 de KPIs (substitui múltiplos `<StatNumber>` soltos) |
| `<Timeline>` | Linha do tempo horizontal/vertical com v-motion stagger |
| `<ComparisonSplit>` | Split antes/depois com v-switch |
| `<CalloutBadge>` | Badge animado ("novo", "destaque", "live", "alerta") |
| `<InteractivePoll>` | Quiz/poll Vue 3 reactive — clica opção, contador sobe ao vivo |
| `<ROICalculator>` | Calculadora reativa (slider input → output computed) |

Full API em `references/components.md`.

---

## Hard rules

Cada regra com pareamento "do this instead". Quando hesitar, leia o "why" — quase todas vêm de bugs reais que se repetiram em decks antigas.

### Processo

- **Skip Discovery (Phase 2) ou Outline approval (Phase 3) é proibido**, mesmo com prompt rico. Faça as perguntas que sobraram após Phase 1 e confirme outline antes de gerar. **Why**: o slug, o deploy, e o público são quase nunca explícitos no prompt inicial; gerar sem perguntar costuma exigir rework completo.

### Animações e clicks

- **Não misture `v-click` directive com `<v-click>` component no mesmo slide.** Escolha um padrão. **Why**: ambos funcionam mas confundem a contagem visual de clicks. **Do**: directive (`<div v-click>`) pra HTML simples; component (`<v-click>`) só quando precisar envolver markdown bruto que precisa de parsing.
- **`v-click` sem valor = `'+1'` (próximo click), não "todos juntos".** 3 elementos com `<div v-click>` revelam em 1, 2, 3 — em sequência. **Do**: pra revelar 2+ no mesmo click, use `<v-after>` ou `v-click="N"` absoluto. Ver `references/animations.md`.
- **Não use `v-after` ou `v-click.hide` para disparar `@keyframes` na primeira visualização.** **Why**: keyframes rodam quando o elemento monta no DOM, não no click. **Do**: separar em DOIS slides — splash no slide N, animação no slide N+1.
- **Defina a estética de animação no headmatter** (`transition: slide-left | slide-right` + `clickAnimation: up`) e quebre só com intenção narrativa. **Why**: decks que decidem transição caso a caso ficam visualmente incoerentes.

### Layouts

- **Use só layouts da lista canônica de 19** (em `references/layouts.md`) ou crie custom em `layouts/<Nome>.vue` da deck. **Why**: layouts inventados (ex: imaginar que existe `two-cols-with-header-and-sidebar`) sofrem fallback silencioso. **Do**: se nada da lista cabe, criar custom — 10 linhas em Vue resolvem.
- **Em `layout: two-cols`, NUNCA use `::left::`** — slot não existe; conteúdo some silenciosamente. Coluna esquerda vai no slot default; direita em `::right::`. **Em `two-cols-header`**, `::left::` e `::right::` ambos funcionam (slot default vira o header).
- **Layout default precisa de** `padding-bottom: 2.5rem+` no `.slidev-layout`. Padding inferior padrão (1.5–2rem) corta insights/conclusões em projetores com aspect ratios diferentes.

### Imagens e assets

- **Nunca use `<img src="/Users/...">` (path absoluto local) nem `<img src="../../../algo.png">` (relativo subindo).** **Do**: coloque o arquivo em `public/<nome>.png` da deck → referencie `<img src="/<nome>.png">`. Vite resolve `--base` corretamente. Ver `references/styling.md` § "Assets".

### Componentes e Iconify

- **Toda tag PascalCase (`<StatNumber>`, `<QuoteReveal>`) referenciada precisa do arquivo `components/StatNumber.vue` no projeto da deck.** **Do**: Phase 4 §2 copia `templates/components/*.vue` inteiro; se criar componente novo, crie em `components/` no momento que escrever a tag. **Why**: sem o arquivo, Vue não acha; tag renderiza literal e o slide quebra visualmente.
- **Toda tag Iconify (`<mdi-*>`, `<lucide-*>`, `<heroicons-*>`) precisa de `@iconify-json/<set>` em `devDependencies`.** Template já vem com `mdi`, `lucide`, `heroicons`, `carbon`. Se usar outro set (`tabler-*`, `phosphor-*`), `npm i -D @iconify-json/<set>` antes de declarar pronto.

### CSS

- **Toda `var(--foo)` referenciada precisa de declaração `--foo:` em `:root` de `styles/index.css` ou em `<style>` do mesmo slide.** **Why**: temas Slidev expõem ~10 vars apenas; usar `var(--gold)` sem declarar é silencioso (fallback) e visualmente quebrado.
- **`<style>` em slide é sempre scoped (implícito), sem opt-out.** Combinators de filho (`.a > .b`) silently break porque o atributo `[data-v-hash]` não chega no filho. **Do**: aplicar classes diretamente, ou usar `:deep(.child)`.
- **Não coloque `<style>` entre o frontmatter global e o slide 1** — vira parte do YAML e corrompe o parsing.

### Markdown + Vue

- **Indentação ≥4 espaços vira bloco de código no CommonMark.** **Do**: 0 ou 2 espaços para wrappers `<v-click>`, `<div>`, etc.
- **Wrappers Vue de bloco (`<v-clicks>`, `<v-click>` component, `<template #right>`) precisam de linha em branco antes E depois do markdown interno.** Sem isso, markdown-it pula e tudo vira HTML literal.
- **`<div>` puro envolvendo markdown NÃO deve ter linhas em branco internas** — markdown trata como fim de bloco e quebra. (Regra oposta da anterior; depende se é wrapper Vue ou HTML puro.)
- **Não use `<!-- comentário -->` dentro de blocos `<div>` extensos em markdown** — fecha o bloco no comentário, resto renderiza como código literal. **Do**: comentário CSS dentro de `<style>` scoped, ou apague.

### Físico — viewport

- **Slides com 5+ cards verticais** correm risco de cortar o último em viewports não-16:9. Padding vertical dos cards ≤0.55rem cada para 5 itens caberem com folga. Sempre teste em `?clicks=99`.

### Idioma & verificação

- **Idioma**: default PT-BR. Match o idioma do input quando diferente.
- **Verificação obrigatória** antes de reportar concluído: Phase 4.5a (`lint-deck.mjs`) + Phase 4.5b (`self-critique.mjs`) + sweep Chrome DevTools MCP (Phase 4 §8).

## Rationalization closure

Cenários onde o LLM tende a racionalizar e o que fazer:

| Tentação | Realidade | Faça |
|---|---|---|
| "Vou usar só `default` e `center` pra ficar seguro" | Layouts existem porque `fact` enquadra estatística como protagonista em 1s; `default` dilui em layout genérico. Sub-uso = deck visualmente plano. | Consultar `references/layouts.md` decision-tree pra cada slide |
| "Vou mostrar o antes/depois do código com 2 blocos lado a lado" | Magic Move é Keynote-grade — o cérebro do espectador acompanha a transformação granular ao invés de comparar duas imagens estáticas | Use `````magic-move` (`references/code-features.md`) |
| "Vou desenhar o diagrama com SVG na mão / ArchitectureFlow" | Mermaid renderiza nativo, semântico, mantém estilo do tema. Reserve ArchitectureFlow só pra coordenadas precisas. | Default = Mermaid (`references/diagrams.md`) |
| "Slidev é Markdown puro, não vou usar Vue 3" | Vue `<script setup>` em slides.md habilita polls live, calculadoras, sliders — exatamente o que distingue um deck cinematográfico de um deck plano | Considere `<InteractivePoll>` / `<ROICalculator>` quando o slide pede interatividade |
| "Vou desenhar uma seta com `→` no texto" | Iconify tem 150k+ icons — `<mdi-arrow-right />` renderiza vetorialmente, escala perfeito | Use Iconify (`references/components.md`) |
| "Pular Discovery porque o prompt do user é detalhado" | A pergunta de deploy não aparece no prompt; o slug precisa ser confirmado. | Sempre rodar Phase 2 |

## Red flags — pare e releia as references/

Se você está pensando algum destes, PARE e leia o doc relevante antes de gerar:

- "Só vou usar `default` e `center`" → `references/layouts.md`
- "Animação? Só `v-clicks` então" → `references/animations.md`
- "Código? Bloco normal com ` ```ts ` " → `references/code-features.md` (especialmente magic-move)
- "Diagrama? Vou escrever SVG/ASCII" → `references/diagrams.md`
- "Interatividade? Não dá em Slidev" → `references/interactive.md`
- "Vou pular o passo de deploy" → confirme com o usuário antes de pular
- "Vou usar `v-after` para revelar o conteúdo principal" → as `@keyframes` CSS já rodam ao montar. Separe em dois slides.
- "Vou deixar um `<!-- comentário -->` aqui dentro do HTML pra documentar" → vai quebrar o parsing MDC. Mova pro `<style scoped>` ou apague.
- "Vou deixar uma linha em branco aqui pra organizar o HTML" → markdown trata como break de bloco. Una tudo em linhas contíguas.
- "Verifiquei só o slide 1, os outros devem estar OK" → sempre faça sweep dos slides com 5+ itens verticais e dos que rodam animação no primeiro reveal.

---

## Output ao final da Phase 4 (ou Phase 5 se houve deploy)

Reporte:

1. Caminho da pasta gerada.
2. URL do dev preview local.
3. **URL pública** (se houve deploy).
4. Total de slides + features novas usadas (ex: "Magic Move em 2 slides, Mermaid em 1, Vue 3 poll em 1").
5. Comandos de export: `npm run export` (PDF), `npm run build` (SPA), `npm run export -- --format pptx`.
6. "Quer ajustar o ritmo de algum slide, trocar tema, ou iterar em alguma animação?"

## Iteração

- Mudanças de conteúdo → `Edit` em `slides.md`.
- Novo componente custom necessário → criar em `components/` seguindo o padrão dos existentes; ver `references/components.md` §"Authoring custom components".
- Trocar tema → ajuste `theme:` no frontmatter (`seriph`, `apple-basic`, `bricks`, `default`, ou tema da gallery).
- Ritmo → props (`duration`, `speed`, `autoPlay`) ou reorganizar `v-click`s.
- Redeploy → re-rodar `scripts/deploy-to-hub.sh <slug>` (overwrite seguro do conteúdo).

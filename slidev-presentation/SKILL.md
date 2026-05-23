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

Produza uma tabela slide-a-slide:

| # | Título | Propósito | Layout | Componente / Feature destaque |
|---|--------|-----------|--------|-------------------------------|
| 1 | Hook | abertura provocativa | `cover` | `<AutoFitText>` + transição `view-transition` |
| 2 | Por que isso importa | gancho emocional | `quote` | `<QuoteReveal>` |
| 3 | Estado atual | retrato do problema | `fact` | `<StatNumber>` + `<CalloutBadge>` |
| 4 | Antes/depois código | refactoring story | `default` | **Shiki Magic Move** (3 estados) |
| 5 | Arquitetura | sistema em fluxo | `default` | Mermaid sequence diagram |
| 6 | Métricas | KPIs medidos | `default` | `<MetricGrid>` |
| 7 | Roadmap | timeline visual | `default` | `<Timeline>` + `v-motion` stagger |
| 8 | Pergunta pra audiência | interatividade | `default` | `<InteractivePoll>` |
| 9 | Cálculo de ROI ao vivo | manipulação reativa | `default` | `<ROICalculator>` |
| 10 | Próximos passos | CTA | `statement` | `<v-clicks>` + Iconify icons |
| 11 | Obrigado | encerramento | `end` | `<QuoteReveal>` final |

Guidelines:
- 8–15 slides para 20–30 min. Ajuste proporcional.
- Alterne slides densos com slides "respiro" (1 imagem ou frase grande).
- **Variar layouts.** Se mais de 60% do deck for `default` ou `center`, está sub-utilizando os outros 17.
- **Variar transições.** `view-transition` global + per-slide `slide-left` / `slide-up` / `fade` quando a mudança de ritmo for intencional.

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

### Phase 4.5 — Self-critique (obrigatório antes de declarar pronto)

Antes de declarar o deck pronto ou rodar Phase 5 (Deploy), execute o critique automático:

```bash
node "<SKILL_DIR>/scripts/self-critique.mjs" "<TARGET>" --visual --url http://localhost:3030/gabriel-trajetoria
# Ou sem visual (só estático, mais rápido):
node "<SKILL_DIR>/scripts/self-critique.mjs" "<TARGET>"
```

O script checa **objetivamente**:

- Word count por slide (>60 = WARN)
- H1 count por slide (>2 = WARN)
- Layout monoculture (>60% default/center = WARN)
- Gradient text overuse (>1 slide com gradient = FAIL)
- Em-dash overuse (≥3 em ≥3 slides = WARN)
- Side-stripe borders (border-left/right >1px = FAIL)
- Pure #000/#fff (WARN)
- Identical card grids (≥6 cards iguais = WARN)
- Glassmorphism overuse (>2 backdrop-filter por slide = WARN)
- Font count global (>4 fontes = WARN)
- Premium feature usage (0 features Slidev premium = WARN)
- (com --visual) Element overflow do slide bounds (FAIL)
- (com --visual) Color count por slide (>12 cores = WARN)

**Hard rule**: exit code 0 (sem FAILs) é pré-requisito pra reportar deck pronto.

Workflow:
1. Rodar `self-critique.mjs` em modo estático após escrever slides.md.
2. Se FAIL → corrigir e re-rodar até passar.
3. WARNs revisar: muitos são opcionais (slide-count, word-count denso), mas leia cada um.
4. Rodar dev server.
5. Rodar `--visual --url http://localhost:3030/<slug>` pra pegar overflow e color count.
6. Corrigir FAILs visuais. Re-rodar até passar.

Os checks **subjetivos** (color strategy commitida, hierarquia visível, AI slop test, register brand-vs-product) ficam pra você durante Phase 4 — leia `references/design-quality.md` antes de gerar slides.md. O critique automático é safety net, não substituto do julgamento.

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

**Design quality (LEIA ANTES DE ESCREVER SLIDES.md)**: `references/design-quality.md` — princípios curados de UI/UX adaptados para deck (register brand/product, color strategy 4 níveis, tipografia em slides, banimentos absolutos, AI slop test, checklist Phase 4). Os checks objetivos rodam automaticamente em Phase 4.5, mas os subjetivos (color strategy, hierarquia, AI slop) só você consegue julgar — interna-los antes de escrever evita iterações.

| Quando o slide é... | Use | Documentado em |
|---|---|---|
| Reveal de uma lista, parágrafo, ou step | `<v-click>`, `<v-clicks>`, `<v-after>`, presets `.scale` / `.fade.right` / `.up` | `references/animations.md` |
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
| 2 colunas balanceadas | `two-cols` (slot default + `::right::`, **nunca** `::left::` — bug conhecido) |
| Header full-width + 2 colunas abaixo | `two-cols-header` |
| Padding zero, slide preenche viewport | `full` |
| Encerramento | `end` |
| Conteúdo geral / default | `default` |
| Sem estilização, layout livre | `none` |
| Conteúdo centrado vertical e horizontalmente | `center` |

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

- **NEVER skip** Discovery (Phase 2) nem Outline approval (Phase 3). Mesmo que o prompt do usuário seja rico, confirme antes de gerar.
- **NEVER use** `::left::` no layout `two-cols` — slot inexistente, conteúdo some silenciosamente. Coluna esquerda vai no slot default, direita em `::right::`.
- **NEVER coloque** `<style>` entre o frontmatter global e o slide 1 — vira parte do YAML e corrompe o parsing.
- **NEVER indente** `<v-click>` com 4+ espaços do início da linha — markdown CommonMark interpreta como bloco de código.
- **NEVER use** comentários HTML `<!-- -->` dentro de blocos `<div>` extensos em markdown — o parser MDC fecha o bloco no comentário e o resto renderiza como código literal. Use comentário CSS dentro de `<style>` scoped, ou remova de vez.
- **NEVER deixe linhas em branco** dentro de um bloco HTML multi-elemento (ex: `<div class="grid"> ... \n\n ... </div>`) — markdown trata como quebra de bloco e estoura o parsing. Compacte tudo em uma linha contínua ou use indentação contínua sem linhas vazias.
- **NEVER use** `v-after` / `v-click.hide` para disparar animações CSS na PRIMEIRA visualização. As `@keyframes` rodam quando o elemento monta no DOM, não no click — então a primeira vez não anima. Fix: **separar em DOIS slides distintos** (splash em slide 1, animação em slide 2) — assim a animação dispara naturalmente ao montar o slide 2.
- **Layout default precisa de** `padding-bottom: 2.5rem+` no `.slidev-layout`. Padding inferior padrão (1.5–2rem) corta insights/conclusões em projetores com aspect ratios diferentes.
- **Slides com 5+ cards verticais** correm risco de cortar o último item em viewports não-16:9. Padding vertical dos cards deve ser ≤ 0.55rem cada para 5 itens caberem com folga. Sempre teste em `?clicks=99` para ver o estado final.
- **Idioma**: default PT-BR. Match o idioma do input quando diferente.
- **Sempre verifique** com Chrome DevTools MCP antes de reportar concluído (Phase 4 §8).

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

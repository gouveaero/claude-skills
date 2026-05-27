# Components — Reference completa

Quatro categorias: **componentes Slidev built-in** (~20, auto-registrados), **componentes custom desta skill** (em `templates/components/`, auto-registrados pelo Slidev quando estão na pasta `components/`), **componentes Iconify** (150k icons via classes `<mdi-*>`, `<heroicons-*>`, `<carbon-*>`), e **componentes Vue do usuário** (criar novos em `components/`).

---

## Regra de ouro do auto-import

Slidev auto-registra **automaticamente** qualquer arquivo `*.vue` em:

- `components/` — auto-import por nome do arquivo (PascalCase ↔ kebab-case).
- `layouts/` — auto-import como `layout:` value.
- `pages/` (raro) — slides parciais.

**Se você usar `<StatNumber>` no `slides.md`, o arquivo `components/StatNumber.vue` PRECISA existir no projeto da deck.** Sem isso, Vue não acha o componente e renderiza tag literal (`<statnumber>` em lowercase no DOM) — visualmente quebrado.

A skill resolve isso copiando `templates/components/*.vue` inteiro para a deck na Phase 4 §2. Se você criar componente novo durante a Phase 4, **coloque em `components/` no momento que escrever a tag no `slides.md`**, não depois.

### Iconify components

Iconify expõe ícones como tags Vue auto-importadas via plugin. Mas precisa do **dataset** instalado:

```bash
# Para usar <mdi-arrow-right />
npm i -D @iconify-json/mdi

# Para usar <lucide-cooking-pot />
npm i -D @iconify-json/lucide

# Para usar <heroicons-bolt-solid />
npm i -D @iconify-json/heroicons

# Para usar <carbon-rocket />
npm i -D @iconify-json/carbon
```

Sem o dataset, a tag renderiza vazia (ícone não aparece). O template da skill já vem com `@iconify-json/mdi`, `@iconify-json/lucide`, `@iconify-json/heroicons`, `@iconify-json/carbon` em `devDependencies` — esses cobrem 95% dos usos. Se precisar de outro set (Tabler, Phosphor, etc.), adicione `@iconify-json/<set>` ao `package.json`.

O `lint-deck.mjs` (Phase 4.5b) checa: pra cada `<prefixo-nome>` (que parece tag Iconify), confirma que `@iconify-json/<prefixo>` está em deps. Faltando = FAIL com sugestão exata de comando.

---

## Slidev built-in components

### Reveal e click

#### `<v-click>`, `<v-clicks>`, `<v-after>`, `<v-switch>`

Ver [animations.md](./animations.md) para a documentação completa do sistema de clicks.

### Texto e layout

#### `<AutoFitText>` — texto que cabe sozinho

Ajusta o `font-size` automaticamente para o texto caber na caixa. Use em hooks de carrossel, slides de capa, manchetes de stat.

```md
<AutoFitText :max="200" :min="40" modelValue="Texto que vai escalar conforme o tamanho do container" />
```

#### `<Transform>` — escalar/transladar elemento

Aplica `transform: scale/translate/rotate` num bloco. Útil para zoom cinematográfico.

```md
<Transform :scale="0.6" origin="top center">
<YourComponent />
</Transform>
```

### Navegação

#### `<Toc>` — table of contents auto-gerado

```md
<Toc columns="2" maxDepth="2" />
```

#### `<Link>` — link interno entre slides

```md
<Link to="14">Pular para conclusão</Link>
```

#### `<TitleRenderer no="42" />` — insere o título de um slide específico inline

#### `<SlideCurrentNo />` e `<SlidesTotal />` — número do slide atual / total

### Mídia

#### `<SlidevVideo>` — embed de vídeo com controles

```md
<SlidevVideo autoplay controls>
  <source src="/demo.mp4" type="video/mp4" />
</SlidevVideo>
```

#### `<Youtube id="LUOMHJH-XCQ" />` — embed de YouTube

#### `<Tweet id="20" />` — embed de tweet

#### `<BlueSky uri="https://bsky.app/profile/.../post/..." />` — embed de post Bluesky

### Arrows e drag

#### `<Arrow x1="10" y1="20" x2="100" y2="200" />` — seta anotando algo

#### `<VDragArrow x1="..." y1="..." x2="..." y2="..." />` — seta arrastável durante apresentação

#### `<VDrag>` — wraps elemento e torna posicionável; ver [interactive.md](./interactive.md).

### Condicional

#### `<LightOrDark>` — variar conteúdo entre temas claro/escuro

```md
<LightOrDark>
<template #dark><img src="/logo-white.svg" /></template>
<template #light><img src="/logo-dark.svg" /></template>
</LightOrDark>
```

#### `<RenderWhen context="presenter">...</RenderWhen>` — só renderiza no modo presenter

Use para notas/cues que só o palestrante vê. Combina com notas em `<!-- ... -->` no final do slide.

### Atribuição

#### `<PoweredBySlidev />` — badge do Slidev

---

## Componentes custom da skill

Todos em [templates/components/](../templates/components/), auto-registrados pelo Slidev (basta usar `<NomeDoComponent />` em qualquer slide). Usam `useSlideContext()` para integração com o sistema de clicks.

### `<CodeReveal>` — walkthrough passo-a-passo de código

| Prop | Tipo | Descrição |
|------|------|-----------|
| `code` | `string` | Código multiline completo |
| `lang` | `string` | Identificador de linguagem |
| `steps` | `Array<{lines: number[], note?: string}>` | 1-indexed lines por step + nota lateral |

```md
<CodeReveal
  lang="ts"
  :code="`function handler(req) {
  const token = req.headers.get('auth')
  if (!token) return unauthorized()
  return json({ user: verify(token) })
}`"
  :steps="[
    { lines: [1], note: 'Entry point HTTP' },
    { lines: [2], note: 'Lê token' },
    { lines: [3], note: 'Aborta com 401 se ausente' },
    { lines: [4], note: 'Caso ok, valida e retorna' }
  ]"
/>
```

Cada step consome 1 click. Para **antes/depois** de código (refactoring story), prefira [Shiki Magic Move](./code-features.md) em vez de `CodeReveal`.

### `<StatNumber>` — counter animado 0→target

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `value` | `number` | — | Valor final |
| `prefix` | `string` | `''` | Ex: `'R$'`, `'+'` |
| `suffix` | `string` | `''` | Ex: `'%'`, `'x'` |
| `label` | `string` | — | Texto abaixo |
| `duration` | `number` | `1.6` | Segundos da animação |
| `decimals` | `number` | `0` | Casas decimais |

```md
<div class="flex gap-16 justify-center">
  <StatNumber :value="99.9" suffix="%" label="uptime" :decimals="1" />
  <StatNumber :value="3.2" suffix="x" label="mais rápido" :decimals="1" />
  <StatNumber :value="420" prefix="+" label="deploys/dia" />
</div>
```

Para múltiplos KPIs com reveal escalonado, use [`<MetricGrid>`](#metricgrid).

### `<ArchitectureFlow>` — diagrama SVG com coordenadas precisas

| Prop | Tipo | Descrição |
|------|------|-----------|
| `nodes` | `Node[]` | `{id, label, x, y, w?, h?}` |
| `edges` | `Edge[]` | `{from, to, label?}` |
| `width` | `number` | viewBox width (800) |
| `height` | `number` | viewBox height (400) |
| `showAll` | `boolean` | Exibe tudo imediatamente |

Reserve para diagramas onde coordenadas exatas importam. Para diagramas padrão (sequence, flowchart, state, ER), **prefira Mermaid** (ver [diagrams.md](./diagrams.md)) — mais semântico, escala correto, mantém estilo do tema.

### `<TerminalDemo>` — terminal simulado

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `lines` | `Array<{type, text, delay?}>` | — | Sequência de linhas (`cmd` ou `out`) |
| `prompt` | `string` | `'$'` | Prompt visual |
| `speed` | `number` | `30` | ms por caractere |

### `<QuoteReveal>` — citação reveal palavra-por-palavra

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `text` | `string` | — | A frase |
| `author` | `string` | — | Atribuição opcional |
| `autoPlay` | `boolean` | `false` | Anima sozinho com stagger; se false, avança por click |

### `<MetricGrid>` — grid de KPIs com reveal escalonado

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `items` | `Metric[]` | — | `{value, label, prefix?, suffix?, icon?}` |
| `cols` | `number` | `2` | Colunas da grade |
| `revealOnClick` | `boolean` | `true` | Cada item entra com click |

```md
<MetricGrid :cols="2" :items="[
  { value: '99.9', suffix: '%', label: 'uptime' },
  { value: '3.2', suffix: 'x', label: 'mais rápido' },
  { value: '420', prefix: '+', label: 'deploys/dia' },
  { value: '12k', label: 'usuários' }
]" />
```

### `<Timeline>` — timeline horizontal ou vertical

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `items` | `TimelineItem[]` | — | `{date?, title, body?, icon?}` |
| `orientation` | `'horizontal'\|'vertical'` | `'horizontal'` | |
| `revealOnClick` | `boolean` | `true` | Nós entram um a um |

### `<ComparisonSplit>` — split antes/depois com reveal lado direito por click

```md
<ComparisonSplit beforeTitle="Antes" afterTitle="Depois" :reveal-after-on-click="true">
<template #before>
- 4h pra processar lote
- Resultado consistente
</template>
<template #after>
- 12min pra processar lote
- Mesma consistência
</template>
</ComparisonSplit>
```

### `<CalloutBadge>` — badge animado

```md
<CalloutBadge variant="live" text="ao vivo" />
<CalloutBadge variant="new">novo</CalloutBadge>
```

Variantes: `new`, `live`, `alert`, `highlight`.

### `<InteractivePoll>` — poll Vue 3 reactive

Usuário clica em uma opção, contador sobe ao vivo. Estado mantido em `ref` Vue.

```md
<InteractivePoll
  question="Qual stack você usa hoje?"
  :options="[
    { id: 'react', label: 'React' },
    { id: 'vue', label: 'Vue' },
    { id: 'svelte', label: 'Svelte' },
    { id: 'other', label: 'Outro' }
  ]"
/>
```

### `<ROICalculator>` — calculadora reativa

Sliders alteram inputs, fórmula recalcula output em real-time.

```md
<ROICalculator
  :inputs="[
    { id: 'leads', label: 'Leads/mês', min: 50, max: 1000, default: 200 },
    { id: 'conv', label: 'Conversão', min: 1, max: 30, default: 8, suffix: '%' },
    { id: 'ticket', label: 'Ticket médio', min: 100, max: 5000, default: 800, prefix: 'R$ ' }
  ]"
  :formula="(v) => (v.leads * v.conv / 100) * v.ticket"
  resultLabel="Receita projetada"
  resultPrefix="R$ "
/>
```

---

## Iconify — 150k+ ícones

Coleções já instaladas: `@iconify-json/mdi`, `@iconify-json/heroicons`, `@iconify-json/carbon`. Outras: instalar via `npm i @iconify-json/<collection>`.

Uso inline:

```md
<mdi-arrow-right class="text-3xl text-teal-400" />
<heroicons-bolt-solid class="text-amber-400" />
<carbon-cloud-monitoring />
```

Catálogo completo: <https://icon-sets.iconify.design/>.

---

## Authoring novos componentes custom

Padrão:

```vue
<script setup lang="ts">
import { useSlideContext } from '@slidev/client'

const { $clicks } = useSlideContext()
// ... props e lógica
</script>

<template>
  <!-- markup, reagindo a $clicks.value para reveal por click -->
</template>

<style scoped>
/* CSS isolado por componente */
</style>
```

Colocar arquivo em `components/MyComponent.vue` no projeto Slidev — auto-registra como `<MyComponent />`.

---

## Pitfalls (bugs conhecidos)

### Bug 1 — Slide 1 interpretado como YAML (crítico)

Não insira `<style>` entre o frontmatter global e o conteúdo do slide 1; o bloco vira parte do YAML e corrompe o parsing. Estilos custom vão em `styles/index.css`.

### Bug 2 — Slides com `<h1>` dentro de `<div>` mostram "undefined" no sidebar

Slidev extrai o título do primeiro `# heading` markdown ou do campo `title:` do frontmatter. Se o `<h1>` está dentro de um `<div>`, sempre adicione `title:` no frontmatter do slide:

```md
---
layout: center
title: Nome do Slide
---
```

### Bug 3 — ArchitectureFlow invisível sem cliques

Use `:show-all="true"` em slides onde o diagrama deve aparecer completo desde o início.

### Bug 4 — ArchitectureFlow escala gigante em viewport largo

Slidev aplica `transform: scale()` no canvas; SVG com `width: 100%` herda essa escala. Para diagramas de fluxo simples, **prefira HTML/Tailwind**:

```html
<div class="flex items-center justify-center gap-4">
  <div class="px-4 py-3 border border-teal-400 rounded-xl text-sm">Entrada</div>
  <span class="text-gray-500 text-xl">→</span>
  <div class="px-4 py-3 border-2 border-amber-500 rounded-xl text-sm">Processamento</div>
  <span class="text-gray-500 text-xl">→</span>
  <div class="px-4 py-3 border border-green-500 rounded-xl text-sm">Saída</div>
</div>
```

Reserve `ArchitectureFlow` só para diagramas técnicos complexos com coordenadas precisas. Em qualquer outro caso, considere Mermaid.

### Bug 5 — `<v-click>` com indentação de 4 espaços vira bloco de código

Markdown CommonMark interpreta 4 espaços no início de linha como `<pre><code>`, mesmo quando o conteúdo está dentro de tag HTML. Refatore para que `<v-click>` fique a 0 ou 2 espaços do início da linha.

### Bug 6 — Goto panel aparece no preview

Adicione em `styles/index.css`:

```css
.autocomplete-list { display: none !important; }
```

(Já está incluído no template default da skill.)

### Bug 7 — `::left::` não é slot válido em `two-cols`

O layout `two-cols` tem slot default + `::right::`. **Nunca** use `::left::` — conteúdo é descartado silenciosamente. Coluna esquerda vai no slot padrão (logo após o frontmatter), direita em `::right::`.

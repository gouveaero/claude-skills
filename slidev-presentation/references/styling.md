# Styling — Reference

4 camadas: **styles/index.css** (global do deck), **slide-scoped `<style>`** (isolado por slide), **global layers** (background/foreground persistente entre slides), **themes** + **addons** (estilo geral do deck).

---

## Global CSS — `styles/index.css`

Já criado pelo template. Define paleta, tipografia, regras base.

Estrutura padrão:

```css
:root {
  --accent: #5eead4;
  --accent-2: #818cf8;
  --accent-3: #f472b6;
  --ink: #e2e8f0;
  --muted: #94a3b8;
  --bg: #0b1020;
}

.slidev-layout h1 { letter-spacing: -0.02em; font-weight: 700; }
.slidev-layout h2 { color: var(--muted); font-weight: 500; }

/* Tabular numerics em todo o deck */
.slidev-layout { font-variant-numeric: tabular-nums; }

/* Anti-goto-panel — esconde painel de navegação `g` no preview */
.autocomplete-list { display: none !important; }
```

Para custom transitions:

```css
.my-blur-enter-active, .my-blur-leave-active {
  transition: opacity 0.5s ease, filter 0.5s ease;
}
.my-blur-enter-from, .my-blur-leave-to {
  opacity: 0; filter: blur(8px);
}
```

Use no slide:

```md
---
transition:
  name: my-blur
---
```

---

## Slide-scoped CSS

Encapsulado por slide — não vaza pro resto do deck.

```md
---
layout: default
---

# Esse slide

Conteúdo customizado

<style scoped>
h1 { color: var(--accent); font-size: 5rem; }
p { font-style: italic; }
</style>
```

Suporta UnoCSS classes inline + PostCSS no `<style>`.

Útil pra slides one-off (capa especial, slide de transição com efeito único) sem poluir o `styles/index.css`.

---

## Global layers — background/foreground persistente

Slidev procura por arquivos `global-top.vue` e `global-bottom.vue` na raiz do projeto. Eles renderizam **em todos os slides**, atrás (`global-bottom`) ou à frente (`global-top`) do conteúdo.

### Use cases

- Watermark / brand line constante
- **Continuidade panorâmica** (linha que cresce, gráfico que se completa, persona que caminha entre slides — feature CRÍTICA pra carrosséis Instagram)
- Background animado (gradiente que move, partículas)
- Logo do tema sempre visível

### Exemplo — linha que cresce conforme avança o slide

```vue
<!-- global-bottom.vue -->
<script setup>
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
const progress = computed(() => (currentPage.value / total.value) * 100)
</script>

<template>
  <div class="fixed bottom-0 left-0 right-0 h-1 bg-gray-800 pointer-events-none">
    <div
      class="h-full bg-gradient-to-r from-teal-400 to-indigo-400 transition-all duration-700"
      :style="{ width: progress + '%' }"
    />
  </div>
</template>
```

### Exemplo — watermark

```vue
<!-- global-bottom.vue -->
<template>
  <div class="fixed bottom-3 right-3 text-xs text-gray-500 pointer-events-none opacity-50">
    @gouveaero · {{ new Date().getFullYear() }}
  </div>
</template>
```

---

## Themes

Configurar no frontmatter:

```md
---
theme: seriph
---
```

### Oficiais

- `default` — clean, minimalista
- `seriph` — tipografia serifada, vibe acadêmica/editorial
- `apple-basic` — estilo Apple keynote
- `bricks` — colorido, vibrante
- `penguin` — illustrative

Instalar: `npm i @slidev/theme-<nome>`. Já vem `seriph` + `default` no template.

### Gallery

<https://sli.dev/resources/theme-gallery> — temas community-contributed.

---

## Addons

Estendem funcionalidade. Frontmatter:

```md
---
addons:
  - excalidraw
  - '@slidev/plugin-notes'
---
```

Instalar: `npm i <addon-package>`.

Addons úteis:
- `excalidraw` — embed de quadros Excalidraw
- `@slidev/plugin-notes` — notas avançadas
- `slidev-addon-rabbit` — barra de progresso visual

Gallery: <https://sli.dev/resources/addons>.

---

## Font configuration

Frontmatter:

```md
---
fonts:
  sans: 'Inter'
  serif: 'Playfair Display'
  mono: 'JetBrains Mono'
  provider: google  # default; também 'none', 'coollabs'
  italic: true
  weights: '400,500,700'
  fallbacks: false  # se true, adiciona sans-serif/serif/monospace fallbacks
---
```

Slidev baixa fontes Google automaticamente em build. Pra fontes próprias, copiar TTF/WOFF pra `public/fonts/` e referenciar no `styles/index.css`:

```css
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}
```

---

## Configuração Shiki (syntax highlighting)

Headmatter:

```md
---
highlighter: shiki
shikiOptions:
  themes:
    dark: vitesse-dark
    light: vitesse-light
  langs:
    - typescript
    - vue
    - bash
---
```

Temas: <https://shiki.style/themes>.

---

## Cheatsheet

| Quero... | Lugar |
|---|---|
| Mudar paleta global | `styles/index.css` |
| Estilizar 1 slide específico | `<style scoped>` no slide |
| Background/watermark persistente | `global-bottom.vue` |
| Linha de progresso animada | `global-bottom.vue` com `useNav()` |
| Tipografia diferente | `fonts:` no frontmatter global |
| Tema visual completo (cores + fonts + spacings) | `theme:` no frontmatter |
| Extender com plugin | `addons:` no frontmatter |
| Custom transition | `styles/index.css` + nome no `transition:` |
| Custom CSS variables | `:root` em `styles/index.css` |

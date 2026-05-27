# Layouts — Reference + decision tree

Slidev oferece **19 layouts built-in** (verificado em `slidevjs/slidev/packages/client/layouts/` em main). A skill antiga usa apenas 3 (`default`, `center`, `two-cols`); cada deck nova deve variar entre 5+ layouts diferentes — o impacto visual de cada slide vem do enquadramento que o layout dá.

Aplicar via frontmatter:

```md
---
layout: cover
---
```

Fonte canônica: https://sli.dev/builtin/layouts

---

## Lista canônica dos 19 built-ins

| Layout | Propósito | Frontmatter relevante |
|---|---|---|
| `center` | Conteúdo centralizado vert+horiz, frase única | — |
| `cover` | Capa formal com título grande, autor | `background:`, `class:` |
| `default` | Catch-all bullets/parágrafos | — |
| `end` | Encerramento da deck | — |
| `fact` | Estatística como protagonista (1 número grande) | — |
| `full` | Padding zero, conteúdo livre full-screen | — |
| `iframe` | Embed full-screen de URL | `url:` |
| `iframe-left` | Iframe + texto à direita | `url:` |
| `iframe-right` | Texto + iframe à direita | `url:` |
| `image` | Imagem como conteúdo principal | `image:`, `backgroundSize:` |
| `image-left` | Imagem à esquerda, texto à direita | `image:`, `backgroundSize:`, `class:` |
| `image-right` | Texto à esquerda, imagem à direita | `image:`, `backgroundSize:`, `class:` |
| `intro` | Sobre o autor / contexto inicial | — |
| `none` | Sem qualquer estilização (tela em branco) | — |
| `quote` | Citação destacada com atribuição | — |
| `section` | Separador de capítulo no meio | — |
| `statement` | Manifesto / 1 frase com peso | — |
| `two-cols` | 2 colunas balanceadas | slot default + `::right::` |
| `two-cols-header` | Header full-width + 2 colunas abaixo | slot default (header) + `::left::` + `::right::` |

**Não inventar nomes**. Layout desconhecido → fallback silencioso ou erro. Se precisa de algo que não existe, **crie um layout custom** (ver § "Custom layouts" abaixo).

---

## Decision tree — qual layout escolher

| Slide é... | Layout | Por quê |
|---|---|---|
| Capa formal com título grande, autor, contexto inicial | `cover` | "Tela cheia de filme" — Slidev posiciona texto centralizado com hierarquia tipográfica grande |
| Apresentação do autor / sobre a palestra | `intro` | Espaço para foto + bio + descrição em coluna lateral |
| Separador de capítulo no meio | `section` | Quebra visual, sinaliza nova parte sem ser final |
| Citação destacada | `quote` | Tipografia maior, atribuição em rodapé |
| Manifesto / 1 frase que carrega o slide | `statement` | Tipografia ultra-grande, sem distração lateral |
| Estatística como protagonista | `fact` | O número fica em primeiro plano |
| Imagem dominante full-width | `image` | Imagem ocupa toda a área, texto opcional sobreposto |
| Texto + imagem lado-a-lado | `image-left` ou `image-right` | Decide qual lado a imagem ocupa |
| Embed de página web durante demo | `iframe` | `url:` no frontmatter |
| Embed + texto | `iframe-left` ou `iframe-right` | |
| 2 colunas balanceadas | `two-cols` | Slot default + `::right::`, **NUNCA `::left::`** (bug — slot inexistente) |
| Header + 2 colunas abaixo | `two-cols-header` | Slot default (header) + `::left::` + `::right::` |
| Conteúdo livre, full-screen | `full` | Tela cheia raw |
| Sem nada (controle total) | `none` | Tela em branco total |
| Encerramento | `end` | Última slide |
| 1 frase no meio da tela | `center` | Centralizado vert+horiz |
| Default catch-all | `default` | Bullets/parágrafos genéricos |

---

## Especificações por layout

### `cover`

```md
---
layout: cover
background: https://images.unsplash.com/.../slide-bg.jpg
---

# Título da palestra

Subtítulo curto

<div class="opacity-70 mt-8">
@gouveaero · 19 maio 2026
</div>
```

### `intro`

```md
---
layout: intro
---

# Slidev Cinematográfico
## Como construir decks que não parecem um Powerpoint

Gabriel Gouvêa — Engenheiro Aerospacial UFMG, cofundador Exos
```

### `section`

```md
---
layout: section
---

# Parte 2 — Animações
```

### `quote`

```md
---
layout: quote
---

# "A melhor arquitetura é aquela que pode ser refeita."

Martin Fowler
```

### `statement`

```md
---
layout: statement
---

# Slidev é Vue 3 disfarçado de markdown.
```

### `fact`

```md
---
layout: fact
---

# 1.9×

mais alcance que post único — carrosséis no Instagram em 2026
```

Combine com `<StatNumber>` (counter animado) ou `<CalloutBadge>` (badge lateral).

### `image`

```md
---
layout: image
image: /full-screenshot.png
backgroundSize: contain
---
```

### `image-left` / `image-right`

```md
---
layout: image-left
image: /screenshot.png
---

# Antes da refatoração

3 contextos misturados num único componente
```

### `iframe` / `iframe-left` / `iframe-right`

```md
---
layout: iframe
url: https://slides.gabrielgouvea.com.br/teste-deploy/
---
```

### `two-cols` — atenção ao bug `::left::`

```md
---
layout: two-cols
---

# Antes

- Build manual no servidor
- Deploy via SSH
- Sem rollback

::right::

# Depois

- Build no GitHub Actions
- Deploy via Coolify
- Rollback git revert
```

**Erro comum**: usar `::left::`. Esse slot **não existe** em `two-cols`; conteúdo entre `::left::` e `::right::` some silenciosamente. Coluna esquerda vai no slot default (sem marcador). 

Em **`two-cols-header`** o `::left::` existe (slot é definido explicitamente — slot default vira o header):

### `two-cols-header`

```md
---
layout: two-cols-header
---

# Header full-width acima das colunas

::left::

Coluna esquerda

::right::

Coluna direita
```

### `full` e `none`

`full` aplica fonts/background do tema; `none` é tela em branco total. Use quando precisa do canvas inteiro sem constraint do tema.

### `end`

```md
---
layout: end
---
```

Combine com `<QuoteReveal>` ou CTA discreto.

### `center` e `default`

Catch-all. `center` para frase única que cabe no meio; `default` para qualquer conteúdo regular.

---

## Custom layouts

Para layouts que não cobrem 100% do caso, **crie um arquivo Vue em `layouts/`** da deck. Slidev auto-importa por nome de arquivo.

### Exemplo: layout "split-with-aside" custom

`layouts/SplitWithAside.vue`:

```vue
<template>
  <div class="grid grid-cols-[2fr_1fr] gap-8 h-full p-12">
    <div class="main">
      <slot />
    </div>
    <aside class="border-l-2 pl-6">
      <slot name="aside" />
    </aside>
  </div>
</template>
```

Uso:

```md
---
layout: split-with-aside
---

# Conteúdo principal

Lista, parágrafos, etc.

::aside::

Sidebar opcional
```

Slidev resolve `split-with-aside` → `layouts/SplitWithAside.vue` (kebab-case ↔ PascalCase). Slot named via `::aside::` em markdown.

### Quando criar custom

- Precisa de header + 3 colunas (nenhum built-in faz isso).
- Precisa de overlay específico (logo no canto + watermark + conteúdo).
- Layout repetido em 5+ slides com mesma estrutura — DRY.

Para 1 slide só, prefira HTML/CSS inline no slide direto.

---

## Anti-pattern: layout monoculture

Se 60%+ da deck for `default` ou `center`, **revise**. Cada layout existe porque enquadra o conteúdo de forma diferente; uma deck de 12 slides deve variar entre 5–7 layouts. Slides "respiro" (1 imagem ou frase grande) em `image`, `fact`, ou `statement` quebram o ritmo.

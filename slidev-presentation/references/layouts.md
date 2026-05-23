# Layouts — Reference + decision tree

Slidev oferece 19 layouts built-in. A skill antiga usa apenas 3 (`default`, `center`, `two-cols`); cada deck novo deve variar entre pelo menos 5 layouts diferentes — o impacto visual de cada slide vem em parte do enquadramento que o layout dá.

Aplicar layout via frontmatter do slide:

```md
---
layout: cover
---
```

---

## Decision tree — qual layout escolher

| Slide é... | Layout | Por quê |
|---|---|---|
| Capa formal com título grande, autor, contexto inicial | `cover` | É o "tela cheia de filme" — Slidev posiciona texto centralizado com hierarquia tipográfica grande |
| Apresentação do autor / sobre a palestra | `intro` | Espaço para foto + bio + descrição em coluna lateral |
| Separador de capítulo no meio de uma palestra longa | `section` | Quebra visual, sinaliza nova parte sem ser final |
| Citação destacada | `quote` | Tipografia maior, atribuição em rodapé, padding correto pra "respirar" |
| Manifesto / afirmação grande / 1 frase que carrega o slide | `statement` | Tipografia ultra-grande, sem distração lateral |
| Estatística como protagonista (1 número grande, 1 label) | `fact` | O número fica em primeiro plano; texto auxiliar fica sutil |
| Imagem dominante (foto, gráfico, screenshot full-width) | `image` | Imagem ocupa toda a área, texto opcional sobreposto |
| Texto + imagem lado-a-lado (split 50/50) | `image-left` ou `image-right` | Decide qual lado a imagem ocupa |
| Embed de página web durante demo | `iframe` | URL no frontmatter (`url:`) carrega iframe full-screen |
| Embed + texto | `iframe-left` ou `iframe-right` | |
| 2 colunas balanceadas (comparação, lista dupla) | `two-cols` | **Slot default + `::right::`**, NUNCA `::left::` |
| Header full-width acima de 2 colunas | `two-cols-header` | Para slides com título grande + comparação abaixo |
| Conteúdo livre, sem padding | `full` | Tela cheia raw, você controla tudo |
| Encerramento da apresentação | `end` | Última slide, geralmente em branco ou com CTA discreto |
| Sem layout (sem estilização default) | `none` | Quando você quer renderizar HTML livre sem nenhum reset |
| Conteúdo centralizado vertical+horizontal, generic | `center` | Default para "1 frase no meio da tela" |
| Default catch-all | `default` | Bullet list, parágrafo, qualquer coisa sem necessidade especial |

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

Separador entre capítulos. Tipografia grande, geralmente fundo distinto.

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

# Slidev é vue 3 disfarçado de markdown.
```

### `fact`

```md
---
layout: fact
---

# 1.9×

mais alcance que post único — carrosséis no Instagram em 2026
```

Combine com `<StatNumber>` para counter animado, ou `<CalloutBadge>` na lateral.

### `image-left` / `image-right`

```md
---
layout: image-left
image: /screenshot.png
---

# Antes da refatoração

3 contextos misturados num único componente
```

### `image`

```md
---
layout: image
image: /full-screenshot.png
---
```

### `iframe`

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

**Erro comum**: usar `::left::`. Esse slot não existe; conteúdo entre `::left::` e `::right::` desaparece silenciosamente. Coluna esquerda fica no slot default (sem marcador).

### `two-cols-header`

```md
---
layout: two-cols-header
---

# Comparação completa

::left::

Coluna esquerda

::right::

Coluna direita
```

(Aqui `::left::` funciona porque o layout o define explicitamente.)

### `full` e `none`

Use quando você precisa do canvas inteiro sem nenhum constraint do tema. `full` ainda aplica fonts/background; `none` é tela em branco total.

### `end`

```md
---
layout: end
---
```

Geralmente combina com `<QuoteReveal>` ou um CTA discreto.

### `center` e `default`

Catch-all. Use `center` quando o conteúdo é uma frase única que cabe no meio; `default` para qualquer conteúdo regular.

---

## Anti-pattern

Se 60%+ do deck for `default` ou `center`, **revise** — você está sub-utilizando os outros 17 layouts. Cada layout existe porque enquadra o conteúdo de forma diferente; um deck de 12 slides deve variar entre 5–7 layouts.

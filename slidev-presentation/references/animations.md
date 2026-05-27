# Animations — Reference (v0.48+ semantics)

Slidev tem **4 sistemas de animação distintos** que se compõem:

1. **Click** — revelações controladas pelo clicker (`<v-click>`, `<v-clicks>`, `<v-after>`).
2. **Motion** — transformações geométricas (`v-motion` via @vueuse/motion).
3. **Slide transition** — transição entre slides (`transition:` no frontmatter).
4. **Click animation preset** — estilo da entrada de cada `v-click` (`.fade.right`, `.up`, `.scale`, ou global via `clickAnimation:`).

A diferença entre eles é importante: **click = quando**, **motion = como move**, **transition = ponte entre slides**, **preset = como aparece**. Misturar conceitos é a causa #1 de "animações incoerentes" — escolha o sistema certo para a intenção.

---

## A regra fundamental dos clicks (memorize)

Slidev reescreveu o sistema de clicks em v0.48. A regra que resolve 80% dos bugs de contagem cabe em 3 linhas:

1. **`v-click` sem valor = `'+1'`** (relativo: aparece 1 click depois do anterior).
2. **String com `'+'` ou `'-'` = relativo**: `v-click="'+2'"`, `v-click="'-1'"`.
3. **Número literal ou string sem sinal = absoluto**: `v-click="3"` ou `v-click="'3'"` = no click 3.

**Consequência prática (a fonte das animações incoerentes):**

```md
<div v-click>Primeiro</div>   <!-- click 1 (-> +1 do click 0) -->
<div v-click>Segundo</div>    <!-- click 2 -->
<div v-click>Terceiro</div>   <!-- click 3 -->
```

NÃO é "todos aparecem no click 1". É 1, 2, 3 — em sequência. Quando você quer **todos no mesmo click**, use `<v-after>` ou `v-click="N"` absoluto:

```md
<div v-click>Primeiro</div>           <!-- click 1 -->
<div v-after>Junto com o primeiro</div>  <!-- também click 1 -->
<div v-after>E mais um junto</div>      <!-- também click 1 -->
```

---

## Decision table — qual primitivo usar

| Intenção | Use | Por quê |
|---|---|---|
| Lista revelada item por item, em ordem | `<v-clicks>` wrapper | Auto-numera os filhos; semântica clara; menos erro |
| Reveal aninhado nível-a-nível | `<v-clicks depth="2">` | Revela nível 1, depois nível 2 |
| Grupo de N itens revelados juntos | `<v-clicks every="3">` | Chunked reveal |
| Item específico fora da ordem natural | `v-click="N"` (absoluto) | Independente de quantos `v-click` vieram antes |
| 2+ elementos no MESMO click | `<v-after>` no segundo+ | Mais limpo que repetir `at="+0"` |
| Esconder elemento após reveal | `v-click.hide="N"` ou `v-click="[N, M]"` | `.hide` inverte; `[N,M]` = visível só nesse range |
| Alternar A→B→C no mesmo lugar | `<v-switch>` com `<template #N>` | Slot-based estado |
| Animação posicional (mover, girar, escalar geométrico) | `v-motion` | Click só liga/desliga; motion é outra dimensão |
| Estilo de entrada do reveal (fade, slide-in, scale) | `.fade.right` / `.up` / `.scale` no `v-click`, ou `clickAnimation:` global | Presets v52.15+ — substituem CSS custom |
| Travar o total de clicks do slide | `clicks: N` no frontmatter | Garante que Slidev não avança antes de N clicks |

---

## Padrão prescrito para "animações coerentes"

A causa raiz de "animações incoerentes" é **decidir caso a caso sem padrão deck-level**. A solução é definir uma estética uma vez no headmatter e quebrar só por intenção narrativa.

### Headmatter de referência

```md
---
theme: seriph
transition: slide-left | slide-right
clickAnimation: up
mdc: true
---
```

- `transition: slide-left | slide-right` — sintaxe pipe: forward = slide-left, backward = slide-right. Sensação natural de "avançar" vs "voltar".
- `clickAnimation: up` — todo `<v-click>` faz slide-up sutil ao aparecer (a menos que tenha modificador próprio). Coerência automática.

### Quebrar o padrão **só** com intenção narrativa

| Intenção | Transição | Quando |
|---|---|---|
| Mudança de capítulo (`layout: section`) | `transition: fade` | Sinaliza "novo bloco" |
| Reveal de impacto (1 número grande, 1 frase) | `transition: zoom` | Foco visual |
| Comparação A→B no MESMO frame | `transition: view-transition` | Magic morphing entre elementos com mesmo `view-transition-name` |

### Dentro do slide

- **Lista/parágrafos em ordem natural** → `<v-clicks>`.
- **Ordem não-natural intencional** → `v-click="N"` absoluto.
- **Nunca misture `<v-click>` (component) e `v-click` (directive) no mesmo slide.** Escolha um. Recomendado: directive (`<div v-click>`) para casos simples, component (`<v-click>`) só quando o filho não é um único elemento.

---

## `<v-click>` — sintaxe completa

### Forma directive (preferida)

```md
<div v-click>Aparece no próximo click</div>
<div v-click="3">Aparece no click 3 (absoluto)</div>
<div v-click="'+2'">2 clicks depois do anterior (relativo)</div>
<div v-click="[2, 4]">Visível entre clicks 2 e 3 (range)</div>
<div v-click.hide>Some no próximo click</div>
<div v-click.fade.right>Aparece com fade-in da direita</div>
<div v-click.scale>Aparece escalando de 0.9 → 1</div>
<div v-click.up>Aparece deslizando de baixo</div>
```

### Forma component (quando precisa envolver markdown bruto)

```md
<v-click>

# Título revelado

Parágrafo com **bold** dentro do reveal.

</v-click>
```

Note as **linhas em branco** ao redor do markdown interno — sem elas, o markdown-it pula o parsing e renderiza como HTML literal. Isso vale pra **todo wrapper de bloco** (`<v-clicks>`, `<template #right>`, `<div>` envolvendo markdown).

---

## `<v-clicks>` — wrapper para listas

```md
<v-clicks>

- Item 1 (click 1)
- Item 2 (click 2)
- Item 3 (click 3)

</v-clicks>
```

### `depth` — revelação por nível

```md
<v-clicks depth="2">

- Pai 1
  - Filho 1.1
  - Filho 1.2
- Pai 2

</v-clicks>
```

`depth=2` revela nível 1 inteiro no click 1, depois nível 2.

### `every` — chunks de N

```md
<v-clicks every="2">

- Item A
- Item B
- Item C
- Item D

</v-clicks>
```

Cada click revela 2 itens.

---

## `<v-after>` — sincronizar com o anterior

```md
<v-click>O que aconteceu</v-click>
<v-after>Por isso é importante</v-after>  <!-- aparece junto com o v-click acima -->
```

Equivalente a `v-click="'+0'"` mas mais legível.

---

## `<v-switch>` — alternar A→B→C

```md
<v-switch>
<template #1>Problema: deploy demora 20min</template>
<template #2>Solução: CI builda no GitHub Actions</template>
<template #3>Resultado: deploy em 2min</template>
</v-switch>
```

Cada click avança para o próximo template, substituindo o anterior no mesmo lugar.

---

## Click animation presets (v52.15+)

Substituem CSS custom para entradas estilizadas.

```md
<div v-click.scale>Cresce ao aparecer (0.9 → 1)</div>
<div v-click.fade.right>Fade-in vindo da direita</div>
<div v-click.up>Slide-in de baixo</div>
<div v-click.left>Slide-in da direita pra esquerda (entrada por trás)</div>
```

Modificadores compostáveis: `.fade` + direção + `.scale`. Default direção = 20px de offset.

### Global default

```md
---
clickAnimation: up
---
```

Aplica `.up` a TODO `<v-click>` do deck que não tenha modificador próprio. Coerência sem repetir em cada slide.

---

## Motion system (`v-motion`)

Slidev empacota `@vueuse/motion`. Use quando o elemento **se move** — não quando só aparece.

### Entrada animada (sem click)

```md
<div
  v-motion
  :initial="{ x: -80, opacity: 0 }"
  :enter="{ x: 0, opacity: 1 }"
>
Entra deslizando da esquerda ao montar o slide
</div>
```

### Click-triggered motion (variantes `:click-N`)

```md
<div
  v-motion
  :initial="{ scale: 1, x: 0 }"
  :click-1="{ scale: 1.3, x: 100 }"
  :click-2="{ scale: 1, x: 0, rotate: 360 }"
>
Click 1: cresce e move. Click 2: volta, girando.
</div>
```

### Click ranges

```md
<div
  v-motion
  :initial="{ x: -80 }"
  :click-1="{ x: 0 }"
  :click-2-4="{ x: 40 }"
>
Move pra 0 no click 1, fica em 40 entre clicks 2-4.
</div>
```

### Stagger via `:delay`

```md
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 100 }}">Item 1</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 200 }}">Item 2</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 300 }}">Item 3</div>
```

### Combinar visibility (click) + movimento (motion)

```md
<div v-click="[2, 4]" v-motion :enter="{ y: 0 }" :initial="{ y: 60 }">
Visível entre clicks 2 e 3, e quando aparece sobe 60px → 0.
</div>
```

---

## Slide transitions

Aplicar globalmente no headmatter (1º slide):

```md
---
transition: slide-left | slide-right
---
```

Sintaxe pipe: `forward | backward`. `slide-left` ao avançar, `slide-right` ao voltar. Sem pipe, a mesma transição em ambos sentidos.

### Per-slide override

```md
---
transition: fade
---
```

### Built-ins disponíveis

- `fade`, `fade-out`
- `slide-left`, `slide-right`, `slide-up`, `slide-down`
- `view-transition` — usa View Transitions API: elementos com mesmo `view-transition-name` morfam entre slides (Magic Move-like cross-slide)
- `zoom`

### Tabela de uso

| Contexto | Transition |
|---|---|
| Navegação padrão da deck | `slide-left \| slide-right` |
| Mudança de capítulo (section) | `fade` |
| Reveal de impacto (fact, statement) | `zoom` |
| Continuidade visual entre slides (elemento "viaja") | `view-transition` (precisa `view-transition-name` no elemento) |
| Direção da navegação | `go-forward \| go-backward` |

### Custom transition

`styles/index.css`:

```css
.my-blur-enter-active,
.my-blur-leave-active {
  transition: opacity 0.5s ease, filter 0.5s ease;
}
.my-blur-enter-from,
.my-blur-leave-to {
  opacity: 0;
  filter: blur(8px);
}
```

Slide:

```md
---
transition:
  name: my-blur
---
```

---

## Pitfalls reais (capturados em decks reais)

### 1. Mistura `<v-click>` directive + component

❌ Errado (no mesmo slide):
```md
<div v-click>Item A</div>
<v-click>

Item B com markdown

</v-click>
```

Funciona mecanicamente, mas confunde a contagem visual. **Padronize.**

### 2. Mismatched `<v-clicks>` aberto sem fechar

❌ Errado:
```md
<v-clicks>

- Item 1
- Item 2

<!-- esqueceu </v-clicks> -->

---
```

O Slidev parseia tudo até o próximo slide como filho do wrapper, e a contagem de clicks vaza. **Sempre feche.**

### 3. Indentação de 4+ espaços vira bloco de código

❌ Errado:
```md
<div class="container">
  <div class="space-y-6">
    <v-click>            ← 4 espaços = bloco de código
    <div>conteúdo</div>
    </v-click>
  </div>
</div>
```

✅ Correto — 0 ou 2 espaços, com linhas em branco:
```md
<div class="container">
<div class="space-y-6">

<v-click>
<div>conteúdo</div>
</v-click>

</div>
</div>
```

### 4. Linhas em branco DENTRO de bloco HTML multi-elemento (sem wrapper Vue)

❌ Errado:
```html
<div class="grid">
<div>A</div>

<div>B</div>          ← linha em branco quebra o bloco
</div>
```

✅ Correto — compactar:
```html
<div class="grid">
<div>A</div>
<div>B</div>
</div>
```

**Importante**: a regra é diferente para wrappers Vue como `<v-click>`. Nesses, **você PRECISA** de linha em branco antes/depois pra markdown parsear conteúdo interno. Resumindo:

- `<div>` puro envolvendo markdown → SEM linhas em branco dentro.
- `<v-click>` / `<v-clicks>` / `<template #right>` envolvendo markdown → COM linhas em branco antes e depois do conteúdo interno.

### 5. `v-motion` + `v-click` no mesmo elemento (v0.48 bug)

Bug conhecido: `v-motion` só reage a `v-click` se ambos estão **no mesmo elemento**. Combinar `v-click` num pai e `v-motion` num filho não dispara o motion.

Fix:
```md
<!-- ❌ não funciona como esperado -->
<div v-click="2">
  <div v-motion :initial="{x:-80}" :enter="{x:0}">…</div>
</div>

<!-- ✅ usar v-if reativo ao $clicks -->
<div v-motion :initial="{x:-80}" :enter="{x:0}" v-if="$clicks > 1">…</div>
```

### 6. CSS keyframes não disparam no primeiro reveal

Animações via `@keyframes` rodam quando o elemento monta no DOM, não a cada click. Se você combina `v-click.hide` com keyframes, a animação roda só na primeira aparição.

Fix: separar em **dois slides distintos** — o splash no slide N, a animação no slide N+1. Assim, montar o slide N+1 dispara o keyframe naturalmente.

### 7. `clicks: N` no frontmatter

Sem `clicks:`, Slidev avança pro próximo slide assim que passa do último `v-click` registrado. Com `clicks: 10`, ele trava em 10 clicks no slide — útil quando você usa `v-motion :click-5` e precisa que existam pelo menos 5 clicks.

### 8. PDF export não captura `v-motion`

Exporting para PDF (`npm run export`) congela o estado do click `N` por slide, mas não anima `v-motion`. Se a deck será PDF-distribuída, prefira `v-click` puro pra revelações; `v-motion` só pra apresentação ao vivo.

---

## Quick reference card

```md
---
# Headmatter coerente
transition: slide-left | slide-right
clickAnimation: up
---

# Slide com lista revelada
<v-clicks>
- Item 1
- Item 2
- Item 3
</v-clicks>

---

# Slide com revelações fora de ordem
<div v-click="2">Aparece no click 2</div>
<div v-click="1">Aparece no click 1</div>
<div v-click="3">Aparece no click 3</div>

---

# Slide com motion + click
<div v-motion :initial="{x:-80}" :click-1="{x:0}" :click-2="{x:80}">
Move conforme clicks
</div>

---

# Slide com switch
<v-switch>
<template #1>Estado A</template>
<template #2>Estado B</template>
<template #3>Estado C</template>
</v-switch>

---

# Slide com transition diferente (capítulo)
---
transition: fade
layout: section
---

# Parte 2
```

# Components — Reference para slidev-carousel

7 componentes: **4 carousel-specific novos** (`HookSlide`, `StepCard`, `CTASlide`, `PanoramicElement`) + **3 reutilizados de slidev-presentation** (`StatNumber`, `QuoteReveal`, `CalloutBadge`).

Para Iconify, layouts, e built-ins Slidev, veja `slidev-presentation/references/components.md`.

---

## `<HookSlide>` — slide 1

Hook gigante com AutoFitText + swipe indicator embaixo. Pensado para ser o "stop the scroll".

| Prop | Tipo | Default | Descrição |
|---|---|---|---|
| `hook` | `string` | — | Frase principal (≤12 palavras) |
| `subhook` | `string` | — | Linha secundária opcional |
| `variant` | `'dark'\|'gradient'\|'accent'` | `'dark'` | Estilo de fundo |

```md
---
layout: cover
---

<HookSlide
  hook="Você está perdendo R$ 200k/ano sem saber."
  subhook="3 erros que custam mais que ads de Black Friday"
  variant="gradient"
/>
```

---

## `<StepCard>` — passo numerado

Slide de educação. Badge grande com número + título + body curto.

| Prop | Tipo | Default | Descrição |
|---|---|---|---|
| `step` | `number` | — | Número do passo (1, 2, 3...) |
| `title` | `string` | — | Título curto |
| `body` | `string` | — | Body 1-2 frases (não passar de 12 palavras totais incluindo título) |
| `icon` | `string` | — | Iconify HTML opcional |

```md
<StepCard
  :step="1"
  title="Pare de buscar leads"
  body="Crie um sistema. Leads frios não viram clientes."
  icon='<mdi-target />'
/>
```

---

## `<CTASlide>` — slide final

CTA + handle + arrow back-to-start opcional.

| Prop | Tipo | Default | Descrição |
|---|---|---|---|
| `cta` | `string` | `'Salva esse post'` | Call to action |
| `handle` | `string` | `'@gouveaero'` | Handle do autor |
| `backArrow` | `boolean` | `true` | Mostra "← Volta pro início" hint |

```md
---
layout: end
---

<CTASlide
  cta="Salva esse post pra revisitar."
  handle="@gouveaero"
  :back-arrow="true"
/>
```

Para clientes (Tribotax, Vhoe, etc), trocar o `handle` no briefing.

---

## `<PanoramicElement>` — continuidade entre slides

Slot reservado pro elemento visual que atravessa todos os slides. Implementado via global layer (`global-bottom.vue`), mas pode ser usado por slide pra reforçar.

A prop `slideIndex` é injetada pelo Slidev context. Componente decide como animar.

Exemplo (linha que cresce):

```vue
<!-- global-bottom.vue -->
<script setup>
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
const progress = computed(() => (currentPage.value / total.value) * 100)
</script>

<template>
  <PanoramicElement :progress="progress" />
</template>
```

| Prop | Tipo | Default | Descrição |
|---|---|---|---|
| `progress` | `number` | 0 | 0-100, controla o avanço do elemento |
| `color` | `string` | `'var(--accent)'` | Cor da linha/elemento |
| `position` | `'top'\|'bottom'\|'left'\|'right'` | `'bottom'` | Lado da tela |

---

## Componentes reutilizados de slidev-presentation

### `<StatNumber>` — counter animado

```md
<StatNumber :value="98" suffix="%" label="erram nisso" />
```

Em PNG export, captura o estado final (counter completo). Não captura a animação 0→target.

### `<QuoteReveal>` — citação word-by-word

Em PNG: usar `:auto-play="true"` (anima sozinho com stagger; o último frame tem todas as palavras visíveis).

```md
<QuoteReveal
  text="A maioria fala em scale. Poucos sabem servir bem."
  author="lição da semana"
  :auto-play="true"
/>
```

### `<CalloutBadge>` — badge animado

```md
<CalloutBadge variant="live">essa semana</CalloutBadge>
<CalloutBadge variant="alert">spoiler</CalloutBadge>
```

Variantes: `new`, `live`, `alert`, `highlight`.

---

## Built-ins úteis (de Slidev, ver slidev-presentation/references/components.md)

| Built-in | Use em carousel |
|---|---|
| `<AutoFitText>` | Hooks de tamanho variável |
| `<Transform>` | Zoom em elemento de foco |
| Iconify (`<mdi-*>`) | Decoração visual, ícone gigante em pattern interrupter |
| `<SlideCurrentNo />` + `<SlidesTotal />` | "3/8" no canto do slide |

---

## Authoring novos componentes carousel

Padrão:

```vue
<script setup lang="ts">
import { useSlideContext } from '@slidev/client'

const props = defineProps<{
  /* ... */
}>()
</script>

<template>
  <!-- ALTO CONTRASTE, TIPOGRAFIA GRANDE, UMA IDEIA -->
</template>

<style scoped>
/* Lembre: vai ser screenshot pra Instagram. Foco visual único. */
</style>
```

Coloca em `components/MyComponent.vue` na pasta do carrossel.

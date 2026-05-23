# Interactive features — Reference

Slidev não é Markdown estático — é Vue 3 disfarçado. Dá pra criar slides interativos: polls, calculadoras reativas, sliders, drag-and-drop, embeds executáveis. **Esses recursos morrem no PNG export** (são runtime-only), mas brilham em apresentação ao vivo e SPA hospedada.

---

## Vue 3 reactive em slides.md

Cole `<script setup>` direto no slide — refs, computed, lifecycle hooks, tudo funciona.

```md
---

<script setup>
import { ref, computed } from 'vue'

const taxa = ref(0.10)
const principal = ref(10000)
const final = computed(() => principal.value * (1 + taxa.value))
</script>

# Calculadora ao vivo

<div class="grid gap-4">
  <label>Principal: <input v-model.number="principal" type="number" /></label>
  <label>Taxa: <input v-model.number="taxa" type="range" min="0" max="0.30" step="0.01" /> {{ (taxa * 100).toFixed(0) }}%</label>
  <div class="text-4xl">Final: R$ {{ final.toFixed(2) }}</div>
</div>

---
```

O `v-model` mantém o estado vivo, `computed` recalcula a cada mudança. Audiência pode interagir antes/durante a apresentação.

Para padrões prontos, use os componentes `<InteractivePoll>` e `<ROICalculator>` ([components.md](./components.md)).

---

## `v-drag` — elementos arrastáveis

Posiciona elementos livremente. O Slidev persiste a posição final em `dragPos:` no frontmatter — útil pra ajustes visuais durante autoria.

```md
---
dragPos:
  card: 200,150,180,90,0
---

<v-drag pos="card">
  <div class="border p-2">Arrasta-me</div>
</v-drag>
```

Sintaxe `pos`: `x,y,width,height,rotate`.

### `<v-drag-arrow>` — setas arrastáveis

```md
<v-drag-arrow pos="seta" x1="100" y1="100" x2="300" y2="200" />
```

Use pra anotar diagramas durante apresentação ao vivo (whiteboard-style).

---

## Monaco editor — código editável

Bloco editável ao vivo (ver [code-features.md](./code-features.md) §"Monaco editor"). A audiência vê você editar o código, com IntelliSense completo.

````md
```ts {monaco}
function double(n: number) {
  return n * 2
}
```
````

Com `{monaco-run}`, o código executa e mostra output:

````md
```js {monaco-run}
const items = [1, 2, 3, 4, 5]
console.log(items.reduce((s, x) => s + x, 0))
```
````

---

## Web components nativos

Use custom elements em qualquer slide:

```md
<my-custom-element data-prop="value"></my-custom-element>
```

Útil pra embeds de third-party (3D viewer, map widget, audio player custom).

Registrar no `setup/main.ts` do projeto Slidev:

```ts
import { defineCustomElement } from 'vue'
import MyElement from './MyElement.ce.vue'
customElements.define('my-custom-element', defineCustomElement(MyElement))
```

---

## `zoom:` por slide

Salva layout denso sem reescrever:

```md
---
zoom: 0.8
---

# Slide muito completo

[muitos elementos que não cabem em 100%]
```

`zoom: 0.8` reduz o conteúdo a 80%. Faixa útil: 0.5–1.5.

---

## Global context API

Acesso a navegação, frontmatter, e estado via composables. Para componentes que precisam reagir a clicks ou contexto do slide:

```vue
<script setup>
import { useSlideContext, useNav } from '@slidev/client'

const { $clicks, $frontmatter, $slidev } = useSlideContext()
const { currentPage, next, prev } = useNav()
</script>

<template>
  <div v-if="$clicks > 0">Visível depois de 1 click</div>
  <div>Slide atual: {{ currentPage }}</div>
  <div>Total clicks deste slide: {{ $clicks }}</div>
</template>
```

| API | O que faz |
|---|---|
| `useSlideContext()` | `$clicks`, `$frontmatter`, `$page`, `$nav`, `$renderContext` |
| `useNav()` | `currentPage`, `total`, `next()`, `prev()`, `go(n)` |
| `$slidev` | Config global, theme, addons |

---

## Drawing & annotations (presenter)

No modo presenter (`/presenter`), abre toolbar de desenho — caneta, marcador, formas. Anota direto sobre o slide durante apresentação ao vivo. Não persiste no export estático.

Configurar no headmatter:

```yaml
drawings:
  persist: false  # default; se true, mantém anotações entre reloads
```

---

## Recording — gravar apresentação

`/recording` no preview abre interface de gravação (RecordRTC + WebRTC). Grava câmera + slides + áudio. Sai como vídeo separado pra editar (não embeda nas slides).

Pra um deck que vai virar vídeo de produto sem precisar abrir OBS: essa é a feature.

---

## Presenter mode (`/presenter`)

URL `http://localhost:3030/presenter` abre painel lateral com:
- Notas do slide atual (extraídas dos comentários `<!-- ... -->`)
- Próximo slide preview
- Timer
- Drawing toolbar
- Screen mirror (capturar outra janela/monitor)

Pra editar notas em batch: `/notes-edit` abre interface dedicada.

---

## Quando NÃO usar interativos

- **Carrossel para Instagram** → tudo isso morre no PNG. Use [`slidev-carousel`](../../slidev-carousel/) que evita features runtime.
- **PDF estático para download** → Monaco/poll/drag não exportam. Use componentes nativos só pro preview, e desativa com `<RenderWhen context="!presenter">` se necessário.
- **Slide muito simples** → Vue reactive pra mostrar 1 número é overkill. Use `<StatNumber>`.

A regra: usar interatividade quando a **interação faz parte da palestra** (poll que captura input da audiência, calculadora que demonstra trade-off, demo que recompila ao vivo). Não usar como adorno.

# Animations — Reference

Animação em Slidev = 4 sistemas: **click** (`v-click`, `v-clicks`, `v-after`), **motion** (`v-motion` via @vueuse/motion), **transition** (entre slides), e **CSS custom** (keyframes em `styles/index.css`).

---

## Click system

### `<v-click>` e `<v-clicks>`

Elemento aparece no próximo click do controle remoto.

```md
<v-click>
Aparece depois de 1 click
</v-click>

<v-clicks>

- Primeiro bullet (click 1)
- Segundo bullet (click 2)
- Terceiro bullet (click 3)

</v-clicks>
```

### Posicionamento absoluto / relativo

```md
<div v-click="3">Aparece no click 3</div>
<v-click at="+2">Aparece 2 clicks depois do anterior</v-click>
```

### Modificadores

```md
<div v-click.hide>Some depois do click</div>
<div v-click.hide="[2, 4]">Visível só entre clicks 2 e 3</div>
```

### `<v-after>` — sincronizar com click anterior

Mostra elementos junto com o último `v-click`:

```md
<v-click>O que aconteceu</v-click>
<v-after>Por isso é importante</v-after>  <!-- aparece junto -->
```

Mais limpo que contar clicks manualmente.

### `<v-clicks depth>` para listas aninhadas

```md
<v-clicks depth="2">

- Pai 1
  - Filho 1.1
  - Filho 1.2
- Pai 2
  - Filho 2.1

</v-clicks>
```

`depth=2` revela nível-a-nível em vez de bullet-a-bullet.

### `<v-clicks every>` para passos múltiplos por item

```md
<v-clicks every="3">
<!-- cada 3 itens contam como 1 click -->
</v-clicks>
```

### `<v-switch>` — alternar estados

```md
<v-switch>
<template #1>Problema: deploy demora 20min</template>
<template #2>Solução: CI builda no GitHub Actions</template>
<template #3>Resultado: deploy em 2min</template>
</v-switch>
```

Ótimo para before/after, problema/solução, decisões A/B/C.

### Click presets — substituem CSS manual

```md
<div v-click.scale>Cresce ao aparecer</div>
<div v-click.fade.right>Fade-in da direita</div>
<div v-click.up>Slide-in de baixo</div>
```

Default global no frontmatter:

```md
---
clickAnimation: up
---
```

Define todos os `<v-click>` do deck para usar o preset `.up`.

### Total clicks do slide

```md
---
clicks: 10
---
```

Útil quando você usa `v-motion :click-1 :click-2` e quer garantir N clicks.

---

## Motion system (@vueuse/motion)

Já vem como dependência no `package.json` do template.

### `v-motion` directive

```md
<div
  v-motion
  :initial="{ x: -80, opacity: 0 }"
  :enter="{ x: 0, opacity: 1 }"
>
Texto que entra deslizando da esquerda
</div>
```

### Click-triggered motion

```md
<div
  v-motion
  :initial="{ scale: 1 }"
  :click-1="{ scale: 1.3, x: 100 }"
  :click-2="{ scale: 1, x: 0, rotate: 360 }"
>
Elemento que cresce, gira e volta conforme você clica
</div>
```

### Combinar com `v-click` (visibility + motion)

```md
<div v-click="[2, 4]" v-motion :enter="{ y: 0 }" :initial="{ y: 60 }">
Visível só entre clicks 2 e 3, e quando aparece, sobe
</div>
```

### Stagger via :delay

```md
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 100 }}">Item 1</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 200 }}">Item 2</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 300 }}">Item 3</div>
```

---

## Slide transitions

Aplicar globalmente no frontmatter do primeiro slide:

```md
---
transition: view-transition
---
```

Aplicar per-slide:

```md
---
transition: slide-left
---
```

### Built-in disponíveis

- `view-transition` — Magic Move-style morphing entre elementos com mesmo `view-transition-name`
- `slide-left` / `slide-right` / `slide-up` / `slide-down`
- `fade` / `fade-out`
- `go-forward` / `go-backward` — direção depende de navegação next/prev
- `zoom`

### Variar por contexto

| Contexto | Transition sugerida |
|---|---|
| Início de palestra / capa | `view-transition` (mais impactante) |
| Section break | `slide-up` |
| Comparison (before/after) | `slide-left` |
| Fade pra slide de respiro / quote | `fade` |
| Navegação geral | `go-forward` |

### Custom transition

Definir em `styles/index.css`:

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

Aplicar no slide:

```md
---
transition:
  name: my-blur
---
```

---

## Pitfall — indentação de `<v-click>`

Markdown CommonMark interpreta 4+ espaços de indentação no início da linha como bloco de código, mesmo dentro de tags HTML. Resultado: `<v-click>` renderiza como `<pre><code>`.

❌ Errado:

```md
<div class="container">
  <div class="space-y-6">
    <v-click>            ← 4 espaços do início
    <div>conteúdo</div>
    </v-click>
  </div>
</div>
```

✅ Correto — reduzir indentação para 0 ou 2 espaços:

```md
<div class="container">
<div class="space-y-6">

<v-click>               ← 0 espaços
<div>conteúdo</div>
</v-click>

</div>
</div>
```

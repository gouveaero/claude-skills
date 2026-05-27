# Animations — Reference (subset que sobrevive ao PNG)

Carrossel exporta PNG estático — só o **estado visual final** é capturado. Use animação Slidev pra **construir a composição visual final**, não pra criar interatividade.

Para o sistema completo de animação Slidev (v-click, v-clicks, v-motion, transitions, presets), ver `slidev-presentation/references/animations.md`. Aqui só o subset relevante.

---

## v-motion — usado pelo estado `:enter`

`v-motion` renderiza o elemento no estado `:enter` por default. PNG captura esse estado final.

```md
<div
  v-motion
  :initial="{ opacity: 0, y: 40 }"
  :enter="{ opacity: 1, y: 0 }"
>
Conteúdo
</div>
```

**Resultado no PNG**: o elemento aparece na posição `y: 0` com `opacity: 1`. O `:initial` não importa pra export (é só o estado pré-animação).

### Stagger pra grupos

```md
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 100 }}">Item 1</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 200 }}">Item 2</div>
<div v-motion :initial="{x: -40}" :enter="{x: 0, transition: { delay: 300 }}">Item 3</div>
```

PNG: todos no estado final (`x: 0`). Pra ver a animação, abre no dev server.

---

## v-click / v-clicks — atenção ao export

Por default, `slidev export --format png` captura **um único frame por slide** — o que tem o **último click resolvido** (todos os v-clicks visíveis).

Se você quer **cada click como PNG separado**, use:

```bash
slidev export --format png --with-clicks
```

Mas pra carrossel Instagram, **regra é 1 PNG por slide**. Se cada estado importa visualmente, **faça slides separados** em vez de v-clicks dentro de 1 slide.

### Quando v-clicks ainda vale em carrossel

Em slides onde a versão "todos os clicks ok" já é a composição visual final que você quer no PNG. Exemplo:

```md
<v-clicks>

- Erro 1: focar em ferramenta
- Erro 2: copiar competidor
- Erro 3: ignorar dados

</v-clicks>
```

PNG final mostra os 3 bullets visíveis. v-clicks só serve pra que, no dev preview, eles entrem progressivamente — visual gratificante de desenvolvimento mas irrelevante pro PNG.

---

## Click animation presets

Servem como "estilo de entrada" no dev preview. No PNG, pega o estado final.

```md
<div v-click.fade.right>Conteúdo</div>
```

Para carrossel, usar default global no headmatter:

```yaml
clickAnimation: up
```

Apenas pra não ficar bugado no dev preview enquanto você cria. **Não afeta o PNG**.

---

## Slide transitions — irrelevantes pro PNG

```md
---
transition: slide-left
---
```

PNG export ignora transitions (cada slide é capturado isolado). **Não precisa configurar transitions pra carrossel** — apenas se você quer um preview gostoso de navegar.

---

## Global layer animations — **A FEATURE-CHAVE**

Aqui mora a continuidade panorâmica. Global layer renderiza em **TODOS os slides** e tem acesso ao `currentPage` via `useNav()`. PNG captura o estado do layer **para aquele slide específico**.

Exemplo — linha que cresce:

```vue
<!-- global-bottom.vue -->
<script setup>
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
const progress = computed(() => (currentPage.value / total.value) * 100)
</script>

<template>
  <div class="fixed bottom-0 left-0 right-0 h-2 bg-gray-800 pointer-events-none">
    <div
      class="h-full bg-gradient-to-r from-teal-400 to-indigo-400"
      :style="{ width: progress + '%' }"
    />
  </div>
</template>
```

PNG do slide 1 = barra 14%. PNG do slide 4 = barra 57%. PNG do último = 100%.

Quando o usuário vê os 8 PNGs no Instagram em sequência, **swipa um e vê a barra crescer** — esse é o efeito panorâmico.

### Outros padrões de global layer

- **Persona caminhando**: SVG ou imagem que `translateX` baseado em `currentPage / total`
- **Counter crescente**: `<div>{{ currentPage }} / {{ total }}</div>` discreto no canto
- **Gráfico que se completa**: bar chart com N barras visíveis = N (currentPage)
- **Fundo gradiente migrando**: `:style="{ background: \`hsl(\${progress * 3.6}, 60%, 20%)\` }"`

---

## Anti-padrões

- ❌ Usar `<v-switch>` ou `v-clicks` esperando 2 estados num único PNG — não funciona
- ❌ Configurar transitions achando que vão sair no carrossel — não saem
- ❌ Magic Move num slide só — PNG pega 1 estado; pra refactoring story em carrossel, **N slides separados**
- ❌ Animação só pelo dev preview — se não muda o PNG final, é distração
- ❌ Esquecer global layer — sem continuidade panorâmica, carrossel parece bullet list separada

---

## Resumo

| Quero | Use |
|---|---|
| Composição visual final boa | qualquer animação Slidev (PNG pega o estado final) |
| Continuidade entre slides | **Global layer** (`global-bottom.vue`) |
| Mostrar evolução de algo | **N slides separados**, não animação dentro de 1 |
| Stagger entrada de elementos no preview | v-motion ou v-clicks (não muda PNG, mas dev fica gratificante) |
| Animar **só pro PNG** | impossível — PNG é estático |

# Layouts — Reference (curado para carrossel)

Slidev tem 19 layouts. Carrossel usa só ~7 deles bem. O resto (`iframe*`, `intro`, `section`, `two-cols-header`) **não funciona** em carrossel (ou porque embed não carrega no PNG, ou porque o formato curto não comporta).

Para o catálogo completo dos 19, ver `slidev-presentation/references/layouts.md`.

---

## Decision tree

| Slide do carrossel é... | Layout | Componente complementar |
|---|---|---|
| **Slide 1 (hook)** | `cover` | `<HookSlide hook="..." />` |
| Estatística grande (98%, R$ 200k, 3x) | `fact` | `<StatNumber>` ou só texto gigante |
| Citação curta / linha provocativa | `quote` | `<QuoteReveal autoPlay>` |
| Manifesto / linha que carrega o slide sozinha | `statement` | apenas texto + AutoFitText |
| **Passo numerado** | `default` | `<StepCard :step="N" />` |
| Imagem dominante (foto, screenshot, ilustração) | `image` | só `image:` no frontmatter |
| Imagem + texto lado a lado | `image-left` ou `image-right` | |
| **Slide final (CTA)** | `end` | `<CTASlide />` |
| Texto livre quando nenhum dos acima cabe | `default` | |

---

## Especificações

### `cover` — slide 1

```md
---
layout: cover
class: text-center
---

<HookSlide hook="Você está perdendo R$ 200k/ano." />
```

Aspect ratio configurado no headmatter global (4:5 default).

### `fact` — estatística como protagonista

```md
---
layout: fact
---

# 98%

<div class="text-2xl opacity-70">dos founders fazem isso errado.</div>
```

Em portrait 1080×1350, o número deve ocupar ~50% da altura. Use `<AutoFitText>` se ele varia:

```md
<AutoFitText :max="400" :min="120" model-value="98%" />
```

### `quote` — linha provocativa

```md
---
layout: quote
---

<QuoteReveal
  text="A maioria fala em scale. Poucos sabem servir bem."
  author="lição da semana"
  :auto-play="true"
/>
```

### `statement` — afirmação grande

```md
---
layout: statement
---

# Stop. <br> Não é falta de leads.
```

### `default` — passo numerado (uso mais comum no meio)

```md
---
layout: default
---

<StepCard
  :step="3"
  title="Aprenda 1 framework por mês"
  body="Não 5. Não 10. Um, profundo."
  icon='<mdi-school />'
/>
```

### `image` — imagem dominante

```md
---
layout: image
image: /screenshot.png
class: relative
---

<div class="absolute bottom-12 left-12 right-12 text-3xl font-bold">
Veja onde o gargalo aparece.
</div>
```

Use overlay de texto pra contextualizar a imagem. Cap de 12 palavras vale aqui também.

### `image-left` / `image-right`

```md
---
layout: image-right
image: /foto-persona.jpg
---

# Quem é seu cliente?

<v-clicks>

- Não é "todo mundo".
- É essa pessoa específica.

</v-clicks>
```

Em carrossel 4:5, split visual é apertado — use só se faz sentido.

### `end` — slide final

```md
---
layout: end
---

<CTASlide
  cta="Salva esse post pra revisitar."
  handle="@gouveaero"
/>
```

---

## Não use em carrossel

- `iframe`, `iframe-left`, `iframe-right` — embed não carrega no PNG export
- `intro` — formato denso demais para um único slide de carrossel (cabeçalho + bio + autor)
- `section` — separador de capítulo não faz sentido em sequência de 6-13 slides
- `two-cols-header` — apertado em 4:5 portrait
- `full`, `none` — possível, mas você acaba reimplementando o que outros layouts já dão

---

## Aspect ratio overrides por slide

Pra slide específico com ratio diferente (raro):

```md
---
layout: default
aspectRatio: '1/1'
---
```

Mas normalmente o headmatter global define para todo o carrossel (default 4:5).

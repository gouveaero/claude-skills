# Custom Component Library — API Reference

All components live in `templates/components/` and auto-register in Slidev (no import needed in `slides.md`). They integrate with Slidev's click system via `useSlideContext().$clicks` when interactive.

---

## `<CodeReveal>`

Progressive code walkthrough. Each step highlights specific lines and shows an annotation on the right. Advances on click.

### Props
| Prop | Type | Description |
|------|------|-------------|
| `code` | `string` | The full code (multiline string). |
| `lang` | `string` | Language for future syntax hinting. Defaults to plain. |
| `steps` | `Array<{ lines: number[], note?: string }>` | 1-indexed line numbers per step + optional note. |

### Example
```md
<CodeReveal
  lang="ts"
  :code="`function handler(req: Request) {
  const token = req.headers.get('auth')
  if (!token) return unauthorized()
  return json({ user: verify(token) })
}`"
  :steps="[
    { lines: [1], note: 'Entry point — recebe o request HTTP.' },
    { lines: [2], note: 'Lê o token do header.' },
    { lines: [3], note: 'Se não houver, aborta com 401.' },
    { lines: [4], note: 'Caso contrário, valida e retorna o user.' }
  ]"
/>
```

**Tip:** lembre-se que cada step do array consome 1 click. Ajuste `clicks:` no frontmatter do slide.

---

## `<StatNumber>`

Counter animado de 0 ao valor alvo ao montar (ease-out). Ideal para métricas impactantes.

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `number` | — | Valor final. |
| `prefix` | `string` | `''` | Ex: `'R$'`, `'+'`. |
| `suffix` | `string` | `''` | Ex: `'%'`, `'x'`. |
| `label` | `string` | — | Texto abaixo do número. |
| `duration` | `number` | `1.6` | Segundos da animação. |
| `decimals` | `number` | `0` | Casas decimais. |

### Example
```md
<div class="flex gap-16 justify-center">
  <StatNumber :value="99.9" suffix="%" label="uptime" :decimals="1" />
  <StatNumber :value="3.2" suffix="x" label="mais rápido" :decimals="1" />
  <StatNumber :value="420" prefix="+" label="deploys/dia" />
</div>
```

---

## `<ArchitectureFlow>`

Diagrama SVG de arquitetura. Nós aparecem primeiro, um a cada click; depois as arestas, uma a cada click.

### Props
| Prop | Type | Description |
|------|------|-------------|
| `nodes` | `Node[]` | `{ id, label, x, y, w?, h? }` — coordenadas absolutas no viewBox. |
| `edges` | `Edge[]` | `{ from, to, label? }` — `from`/`to` são ids de nodes. |
| `width` | `number` | viewBox width (default 800). |
| `height` | `number` | viewBox height (default 400). |

### Example
```md
<ArchitectureFlow
  :nodes="[
    { id: 'client', label: 'Client',  x: 40,  y: 170 },
    { id: 'api',    label: 'API',     x: 240, y: 170 },
    { id: 'queue',  label: 'Queue',   x: 440, y: 80  },
    { id: 'worker', label: 'Worker',  x: 440, y: 260 },
    { id: 'db',     label: 'DB',      x: 640, y: 170 }
  ]"
  :edges="[
    { from: 'client', to: 'api',    label: 'HTTP' },
    { from: 'api',    to: 'queue',  label: 'publish' },
    { from: 'queue',  to: 'worker', label: 'consume' },
    { from: 'worker', to: 'db',     label: 'write' },
    { from: 'api',    to: 'db',     label: 'read' }
  ]"
/>
```

**Total clicks consumed**: `nodes.length + edges.length`.

---

## `<TerminalDemo>`

Terminal falso com prompt realista e animação de digitação. Comandos "são digitados", outputs aparecem inteiros.

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `lines` | `Array<{ type: 'cmd' \| 'out', text: string, delay?: number }>` | — | Sequência de linhas. |
| `prompt` | `string` | `'$'` | Prompt shown before `cmd` lines. |
| `speed` | `number` | `30` | ms por caractere digitado. |

### Example
```md
<TerminalDemo
  :lines="[
    { type: 'cmd', text: 'npm create slidev@latest my-talk' },
    { type: 'out', text: '✓ Project created' },
    { type: 'cmd', text: 'cd my-talk && npm run dev', delay: 400 },
    { type: 'out', text: '➜  Local:   http://localhost:3030' }
  ]"
/>
```

Inicia automaticamente no mount. Use `clicks: 0` no slide se não quiser consumir clicks.

---

## `<QuoteReveal>`

Citação com reveal palavra-por-palavra. Útil pra abrir/fechar palestra ou slides de transição emocional.

### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `text` | `string` | — | A frase. |
| `author` | `string` | — | Atribuição opcional. |
| `autoPlay` | `boolean` | `false` | Se `true`, anima sozinho com stagger. Se `false`, avança por click. |

### Example (autoplay)
```md
<QuoteReveal
  text="A melhor arquitetura é aquela que pode ser refeita."
  author="Martin Fowler"
  :auto-play="true"
/>
```

### Example (click-driven)
```md
<QuoteReveal
  text="Premature optimization is the root of all evil."
  author="Donald Knuth"
/>
```

**Clicks consumed** (quando `autoPlay=false`): `text.split(/\s+/).length`.

---

## Mixing with native Slidev directives

Você pode combinar livremente com:

- `<v-click>` / `<v-clicks>` — reveal por click em qualquer elemento.
- `v-motion` — animação de posição/opacity com Motion One.
- Shiki Magic Move — morphing entre versões de código (blocos ` ```ts {*|1|2-5|all} `).
- `<Transform>` — escala/pan.
- `<Arrow>` — setas desenhadas.

Regra de bolso: **componente custom quando a animação é central ao slide; directive nativa quando é um detalhe.**

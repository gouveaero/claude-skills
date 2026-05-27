# Slidev v0.48 → v52.15 — Features que decks antigos não usam

Este doc captura mudanças e features adicionadas a partir de v0.48 (set/2024) até v52.15 (recente). Decks antigos perdem features importantes; consulte aqui antes de gerar.

---

## Renames e removals (importante!)

| O que mudou | De | Para | Versão |
|---|---|---|---|
| Headmatter MDC | `mdc: true` | `comark: true` | v52.14.0 |
| Code groups | Implícito | Precisa `comark: true` | v52.14.0 |
| Highlighter Prism | Disponível | **Removido** — só Shiki | v0.50.0 |
| Motion preload workaround | `preload: false` necessário | Não é mais necessário | v0.48.9 |

### Como migrar `mdc:` → `comark:`

Decks antigos com `mdc: true` no headmatter perdem features Comark (code groups, etc.). Trocar para `comark: true`:

```md
---
# antes
mdc: true

# depois
comark: true
---
```

Se a deck **não usa** features que exigem comark (code groups, alguns inline directives), pode remover a linha — defaults Slidev cobrem o resto.

---

## Click animation presets (v52.15+)

Substituem CSS custom para entradas estilizadas. Compostáveis via modificadores no `v-click`.

```md
<div v-click.fade>Fade-in</div>
<div v-click.fade.right>Fade-in da direita (20px offset)</div>
<div v-click.up>Slide-in de baixo</div>
<div v-click.down>Slide-in de cima</div>
<div v-click.scale>Escala 0.9 → 1</div>
<div v-click.none>Sem animação (instant)</div>
```

### Global default (headmatter)

```md
---
clickAnimation: up
---
```

Aplica `.up` a todo `<v-click>` que não tenha override. Coerência sem repetir.

### Combinar com `.hide`

```md
<div v-click.hide.fade>Some com fade-out no próximo click</div>
```

---

## Alerts nativos (v52.15)

Sintaxe GitHub-style para callouts inline:

```md
> [!NOTE]
> Informação contextual neutra.

> [!TIP]
> Sugestão útil.

> [!IMPORTANT]
> Crucial — não perca.

> [!WARNING]
> Cuidado, isto pode quebrar.

> [!CAUTION]
> Risco real, atenção.
```

Renderiza com cor + ícone próprios. Substitui `<CalloutBadge>` para callouts inline em texto. Use `<CalloutBadge>` quando precisar de badge flutuante visual; `[!NOTE]` para callouts em parágrafo.

---

## `<BlueSky>` embed (v52.15)

```md
<BlueSky post="https://bsky.app/profile/dimaslz.dev/post/3l5tj5djh4w2u" />
```

Análogo a `<Tweet>` e `<Youtube>`. Útil em decks técnicas que citam threads da rede.

---

## Code features completas (consolidação)

### Magic Move (4 backticks)

```` md
````md magic-move
```ts
const x = 1
```

```ts
const x: number = 1
```

```ts
interface Foo { x: number }
const x: Foo = { x: 1 }
```
````
````

Cada bloco é um "estado"; Slidev anima a transformação granular entre estados a cada click. Use para evolução de código (refactoring, type narrowing, antes/depois).

### Line highlight + ranges

```` md
```ts {2,4-6|all}
const a = 1
const b = 2
const c = 3
const d = 4
const e = 5
```
````

`{2,4-6|all}` = primeiro click highlight linhas 2,4,5,6; próximo click highlight tudo.

### Twoslash

```` md
```ts twoslash
const x: number = 'string'
//                ^?
```
````

Mostra tipos inline e errors do TypeScript como tooltips. Ótimo para type-level explanations.

### Monaco (editável ao vivo)

```` md
```ts {monaco}
const x = 1
```
````

Vira editor Monaco completo. `{monaco-run}` adiciona botão de executar. Use só em demos interativas; rasga performance se exagerar.

### Code groups (precisa comark: true)

```` md
::code-group

```ts [config.ts]
export default { foo: 'bar' }
```

```ts [server.ts]
import config from './config'
```

::
````

Tabs entre arquivos. Use para "veja como isto se conecta em N arquivos".

### Import snippet

```md
<<< @/snippets/file.ts#region-name {2-5|all}
```

Importa código real do disco. Use `#region-name` (via comentários `// #region foo` / `// #endregion`) para selecionar trecho. Mantém slide enxuto e source-of-truth no código real.

### Shiki transformers

```md
---
features:
  shiki:
    transformers: [{ /* … */ }]
---
```

Para customizar highlighting além do default. Raro em decks gerais.

---

## Frontmatter — keys canônicas

Lista completa de keys reconhecidas no headmatter (global) e per-slide:

### Headmatter (1º slide, configura a deck inteira)

| Key | Tipo | Default | Uso |
|---|---|---|---|
| `theme` | string | `default` | Nome do tema (seriph, apple-basic, bricks, …) |
| `title` | string | — | Título mostrado no browser tab |
| `info` | string (md) | — | Texto de "sobre" no presenter mode |
| `author` | string | — | Autor (vai pra metadata) |
| `keywords` | string | — | SEO |
| `transition` | string | — | Transição global; aceita pipe `forward \| backward` |
| `clickAnimation` | string | — | Preset global pra `v-click` (`up`, `down`, `fade`, `scale`, …) |
| `mdc` | bool | false | **Renamed → `comark` em v52.14** |
| `comark` | bool | false | Habilita Comark (code groups, etc.) |
| `fonts` | object | — | Custom fonts (sans, serif, mono, weights, provider) |
| `colorSchema` | string | `auto` | `light` / `dark` / `auto` |
| `aspectRatio` | string | `16/9` | `4/3`, `1/1`, etc. |
| `canvasWidth` | number | 980 | Largura interna em px |
| `lineNumbers` | bool | false | Mostra line numbers em todo code block |
| `monaco` | bool/string | `dev` | Carrega Monaco (`true` / `dev` / `build` / false) |
| `htmlAttrs` | object | — | Attrs no `<html>` (lang, dir, etc.) |
| `download` | bool/string | — | Habilita download button |
| `exportFilename` | string | — | Nome do PDF exportado |
| `seoMeta` | object | — | OG tags, twitter card |
| `defaults` | object | — | Defaults pra frontmatter per-slide |
| `addons` | string[] | — | Lista de addons npm pra carregar |
| `routerMode` | string | `history` | `history` / `hash` |
| `selectable` | bool | false | Permite seleção de texto |
| `presenter` | bool | true | Habilita presenter mode |
| `record` | string | `dev` | Recording |
| `contextMenu` | bool/string | true | Click direito mostra menu |

### Per-slide (frontmatter de cada `---` slide)

| Key | Tipo | Uso |
|---|---|---|
| `layout` | string | Nome do layout (cover, two-cols, etc.) ou layouts/*.vue custom |
| `class` | string | Classes Tailwind/Uno extras no `.slidev-layout` |
| `transition` | string | Override per-slide |
| `clicks` | number | Total de clicks no slide (trava) |
| `clicksStart` | number | Click inicial (default 0) |
| `clickAnimation` | string | Override per-slide do preset |
| `title` | string | Título do slide (vai pra TOC) |
| `level` | number | Hierarquia (1 = section, 2 = sub, …) — afeta `<Toc>` |
| `hideInToc` | bool | Esconde no TOC |
| `routeAlias` | string | Alias de rota custom (`/$alias`) |
| `zoom` | number | Zoom in/out do slide (`0.8` aperta conteúdo denso) |
| `background` | string | URL de background image OU CSS color |
| `disabled` | bool | Pula o slide |
| `src` | string | Importa slides externos (slides parciais) |
| `preload` | bool | Force pre-load deste slide (raramente preciso post-v0.48.9) |

Por-layout, há props específicas (`image:` em image-left, `url:` em iframe, etc.). Ver `references/layouts.md`.

---

## Sintaxe markdown que importa

### Linhas em branco em wrappers Vue

Block-level Vue wrappers (`<v-clicks>`, `<v-click>` component, `<template #right>`, `<div>` envolvendo markdown) precisam de **linha em branco** antes e depois do markdown interno:

```md
<v-clicks>

- Item 1
- Item 2

</v-clicks>
```

Sem as linhas em branco, markdown-it pula e tudo vira HTML literal.

**Exceção**: `<div>` puro sem markdown interno (só HTML/Vue) NÃO deve ter linhas em branco — markdown-it trata como fim de bloco e quebra.

### Comentários HTML

`<!-- -->` dentro de blocos `<div>` extensos em markdown pode fechar o bloco prematuramente. Mova comentários para `<style scoped>` ou apague.

### Indentação

Indentação ≥4 espaços vira bloco de código no CommonMark. Tags HTML/Vue indentadas viram `<pre><code>`. Use 0 ou 2 espaços para wrappers em markdown.

### MDC inline directives (precisa comark)

```md
::div{class="bg-red-100 p-4"}
Conteúdo num div com classes
::
```

Atalho para `<div class="...">` em sintaxe MDC. Precisa `comark: true`.

---

## Recursos para checar

- Docs: https://sli.dev/
- Source: https://github.com/slidevjs/slidev
- CHANGELOG: https://github.com/slidevjs/slidev/blob/main/CHANGELOG.md
- Built-in components: https://sli.dev/builtin/components
- Built-in layouts: https://sli.dev/builtin/layouts

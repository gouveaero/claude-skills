# Feature matrix — o que sobrevive ao PNG export

Carrossel exporta para PNG estático (`slidev export --format png`). Cada slide vira 1 PNG no aspect ratio configurado. **Features de runtime morrem** — só o frame final estático é capturado.

| Feature Slidev | Sobrevive no PNG? | Por quê |
|---|---|---|
| `v-click` / `v-clicks` | ⚠️ Parcial — o frame final (último click) é capturado | Para ter cada estado como PNG separado, use `--with-clicks` na export OU coloque cada estado em slide próprio |
| `v-motion` | ✅ Visualmente, o estado `:enter` (final) é captado | |
| Click presets (`.scale`, `.fade.right`) | ✅ Estado final ok | |
| `v-switch` | ❌ Só renderiza 1 estado por click; PNG pega o último | Se precisa de A vs B, faça 2 slides |
| Slide transitions (`slide-left`, `view-transition`) | ❌ N/A — export captura cada slide sozinho, sem transição | |
| Layouts `cover`, `fact`, `quote`, `statement`, `image`, `default` | ✅ Renderizam normal | |
| Layouts `iframe*` | ❌ iframe não carrega no PNG export | Não use |
| `<AutoFitText>` | ✅ Renderiza correto | |
| `<Transform>` | ✅ | |
| `<Toc>` | ⚠️ Gera estaticamente; ok se navegação não importa | |
| **Global layers** (`global-bottom.vue`) | ✅ **CRÍTICO** — renderiza em TODOS os PNGs | É como a continuidade panorâmica funciona |
| Iconify (`<mdi-*>`, `<heroicons-*>`) | ✅ SVG inline, captura perfeito | |
| Mermaid | ✅ Renderiza pra SVG, captura | |
| PlantUML / Kroki | ✅ Mesma coisa | |
| LaTeX / KaTeX | ✅ HTML rendering, ok | |
| Slide-scoped CSS (`<style scoped>`) | ✅ Aplicado no build | |
| Shiki syntax highlighting | ✅ HTML estático, ok | |
| Shiki **Magic Move** | ⚠️ Cada bloco precisa estar num slide separado; PNG pega 1 estado por slide | Use sparingly em carrossel |
| Line highlighting `{2-3\|5\|all}` | ⚠️ Pega o estado do último click; pra cada estado, slide separado | |
| Twoslash `^?` hover | ❌ Hover não existe em PNG | Não use |
| Monaco editor `{monaco}` | ❌ Runtime-only | |
| Monaco runner `{monaco-run}` | ❌ Runtime-only | |
| Import snippets `<<< @/...` | ✅ Resolve em build time, ok | |
| `v-drag` | ❌ Interativo, morre | |
| `v-drag-arrow` | ❌ Interativo, morre | |
| Vue 3 `<script setup>` reactive forms | ❌ `v-model` precisa de runtime | |
| `<InteractivePoll>` / `<ROICalculator>` | ❌ Reactive, morre no PNG | Não use em carrossel |
| Web components | ⚠️ Depende — só estáticos sobrevivem | |
| `zoom: 0.8` | ✅ Aplicado no render | |
| Recording API | ❌ Runtime-only | |
| Drawing tools | ❌ Runtime-only | |
| Presenter mode | ❌ N/A | |
| `<SlidevVideo>` | ⚠️ Captura primeiro frame só | |
| `<Youtube>` / `<Tweet>` / `<BlueSky>` | ❌ Embeds não carregam em headless | |

---

## Regra de bolso

Se a feature **muda estado em runtime** (clicks, input, drag, video play), **não use em carrossel**. Use a feature pra construir o **estado visual final** estático.

Quer mostrar evolução de código? Faça 3 slides separados (não Magic Move).

Quer comparação antes/depois? 2 slides, não `<v-switch>` num slide só.

Quer interatividade de fato? Esse não é o veículo. Use `slidev-presentation` e deploy via slides-hub.

---

## Para presentation skill (não-carrossel)

Para ver o uso completo dessas features em apresentações que rodam ao vivo, ver `slidev-presentation/references/` — animations, code-features, interactive, components, etc.

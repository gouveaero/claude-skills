# Workflow — 4 phases

## Phase 1 — Intake

Read any file referenced by `$ARGUMENTS` (use Read / Glob as needed). Identify:

- **Domain**: web, ML, infra, design, security, etc.
- **Existing structure**: outline? transcript? raw notes? article?
- **Tone signals**: formal/casual, didactic/provocative.
- **Technical artifacts**: code snippets, diagrams, data, references.
- **Language** of the source material.

Produce a short summary (3–4 bullets) of what you understood, then move to Discovery.

---

## Phase 2 — Discovery

Batch the questions you actually need into a single `AskUserQuestion` call. Skip any question whose answer is already clear from Phase 1.

Default question bank:

1. **Tema central** — qual a tese/mensagem principal em uma frase?
2. **Público** — nível técnico e contexto (devs, gestores, misto, acadêmico)?
3. **Duração** — minutos de fala + Q&A?
4. **Takeaway** — o que o público deve lembrar ou fazer depois?
5. **Tom** — formal, casual, provocativo, didático, inspiracional?
6. **Estética** — minimalista, cinematográfico, corporativo, editorial, brutalist? Alguma referência (links, imagens)?
7. **Código/dados** — quais snippets, números, diagramas devem aparecer?
8. **Idioma** — PT ou EN?
9. **Contexto extra** — artigos, posts ou rascunhos que devo usar como fonte?
10. **Onde criar** — pasta de destino (default: `./presentation/`).

Depois das respostas, confirme com uma frase curta o que entendeu antes de ir para o outline.

---

## Phase 3 — Outline approval

Produza uma tabela slide-a-slide. Exemplo de formato:

| # | Título | Propósito | Componente/Layout |
|---|--------|-----------|-------------------|
| 1 | Hook | abrir com pergunta provocativa | `QuoteReveal` |
| 2 | Contexto | o problema em 3 pontos | `<v-clicks>` + lista |
| 3 | Números que doem | mostrar impacto | `StatNumber` (3 grandes) |
| 4 | Arquitetura antiga | ilustrar o before | `ArchitectureFlow` |
| 5 | A ideia | nossa proposta em 1 frase | layout `center` |
| 6 | Código | função chave passo-a-passo | `CodeReveal` |
| 7 | Demo CLI | mostrar comportamento | `TerminalDemo` |
| 8 | Resultados | métricas depois | `StatNumber` |
| 9 | Lições | 3 takeaways | `<v-clicks>` |
| 10 | Encerramento | call-to-action + contato | `QuoteReveal` |

Guidelines:
- 20–30 slides para palestra de 30–40 min. Ajuste proporcionalmente.
- Alterne slides densos com slides "respiro" (1 imagem/frase grande).
- Começo forte (gancho nos 2 primeiros), meio instrutivo, final memorável.

**Termine a mensagem com: "Aprova esse outline? Posso gerar a apresentação?" e espere o usuário responder.** Não gere sem aprovação explícita.

---

## Phase 4 — Generation

1. **Confirme o destino** — default `./presentation/`. Se a pasta já existe e não está vazia, pergunte antes de sobrescrever.

2. **Copie templates**:
   ```bash
   cp -r "<SKILL_DIR>/templates/." "<TARGET>/"
   ```
   (use Bash — não dependa de Glob para copiar binários).

3. **Escreva `slides.md`** expandindo o outline. Para cada slide:
   - Título + subtítulo/hook curto.
   - Conteúdo focado em 1 ideia.
   - Quando o outline indicou um componente custom, use-o com props realistas.
   - Inclua notas do apresentador em `<!-- ... -->` ao final do slide quando fizer sentido.
   - Use `transition:` por slide só quando a mudança de ritmo for intencional.
   - **Indentação de `<v-click>`**: jamais colocar `<v-click>` a 4 ou mais espaços do início da linha — markdown interpreta como bloco de código. Usar 0 ou 2 espaços (ver Bug 5).

4. **Atualize `package.json`**: substitua `"name": "presentation"` pelo título em kebab-case.

4b. **Adicione a regra CSS anti-goto-panel em `styles/index.css`** (ver Bug 6):
   ```css
   /* Hide Slidev dev-mode goto/autocomplete panel */
   .autocomplete-list { display: none !important; }
   ```

5. **Instale deps** em background:
   ```bash
   cd <TARGET> && npm install && npm i -D playwright-chromium
   ```
   Use `run_in_background: true`. O `playwright-chromium` é necessário para `npm run export` (PDF/PPTX).

6. **Rode o dev server**:
   ```bash
   cd <TARGET> && npm run dev
   ```
   Também em background. Leia o output para capturar a URL (geralmente `http://localhost:3030`).

7. **Verificação slide a slide (OBRIGATÓRIO antes de reportar ao usuário)**:

   Após o servidor subir, use Chrome DevTools MCP para verificar cada slide:
   ```
   navigate_page → http://localhost:3030/1
   take_screenshot → verificar visualmente
   navigate_page → http://localhost:3030/2 ... repeat for all slides
   ```

   **Checklist por slide:**
   - [ ] Título aparece no sidebar de navegação (não "undefined")
   - [ ] Conteúdo de primeiro nível visível (não em branco exceto por `v-click`)
   - [ ] Nenhum texto cortado ou overflow fora do slide
   - [ ] Componentes custom (QuoteReveal, StatNumber, ArchitectureFlow) renderizam

   **Se encontrar erro**, corrija antes de reportar. Ver seção "Bugs conhecidos" abaixo.

8. **Reporte ao usuário**:
   - Caminho da pasta.
   - URL do preview.
   - Total de slides.
   - Comandos de export:
     - `npm run export` → PDF
     - `npm run build` → SPA estática
     - `npm run export -- --format pptx` → PowerPoint
   - Pergunta de iteração: "quer ajustar o ritmo de algum slide, trocar o tema, ou mexer em alguma animação específica?"

---

## Bugs conhecidos e como evitar

### Bug 1 — Slide 1 interpretado como YAML (crítico)

**Sintoma**: Slide 1 exibe texto literal `layout: center class: 'text-center'` ou similar.

**Causa**: O bloco global `---...---` de configuração fecha e o conteúdo imediatamente seguinte é o slide 1. Se um bloco `<style>` for colocado entre o frontmatter global e o primeiro slide, ele se torna parte do YAML e corrompe o parsing.

**Regra**: Jamais inserir `<style>` entre o frontmatter global e o conteúdo do slide 1. Estilos customizados devem ir em `styles/index.css`. O slide 1 começa direto após o `---` de fechamento do frontmatter global — sem frontmatter individual próprio.

Estrutura correta:
```
---
theme: seriph
title: Minha Apresentação
---

<!-- Slide 1 começa aqui, sem frontmatter próprio -->
<div>conteúdo do slide 1</div>

---
layout: default
---

<!-- Slide 2 -->
```

---

### Bug 2 — Slides com `<h1>` dentro de `<div>` mostram "undefined" no sidebar

**Sintoma**: Slides com `layout: center` mostram "undefined" na navegação lateral.

**Causa**: Slidev extrai o título do slide do primeiro `#` markdown ou do campo `title:` no frontmatter do slide. Se o `<h1>` está dentro de um `<div>` HTML (não como markdown `# Título`), o Slidev não consegue extrair o título.

**Regra**: Sempre adicionar `title:` no frontmatter de qualquer slide que use HTML para o heading:
```
---
layout: center
title: Nome do Slide
---

<div>
  <h1>Nome do Slide</h1>
```

---

### Bug 3 — ArchitectureFlow invisível no carregamento (sem cliques)

**Sintoma**: Slide com `<ArchitectureFlow>` aparece completamente em branco.

**Causa**: A lógica original `isNodeVisible = (idx) => clicks > idx` nunca satisfaz `0 > 0`, então nenhum nó é exibido antes do primeiro clique.

**Correção no componente**: A lógica foi atualizada para `clicks >= idx`, tornando o nó 0 visível sem cliques. Além disso, o prop `:show-all="true"` exibe todos os nós e arestas imediatamente (útil em pitch decks onde a revelação progressiva não é necessária).

**Regra**: Usar `:show-all="true"` em slides onde o diagrama deve aparecer completo desde o início.

---

### Bug 4 — ArchitectureFlow com escala gigante em janelas largas

**Sintoma**: Os nós SVG aparecem com texto enorme que extrapola os boxes.

**Causa**: Slidev aplica `transform: scale()` no canvas inteiro para preencher o viewport. O SVG com `width: 100%` herda essa escala multiplicada, tornando os elementos visualmente maiores do que o esperado. Texto SVG com `font-size` em unidades do viewBox não se comporta como CSS — escala junto com o SVG.

**Solução**: Para diagramas de fluxo em pitch decks, **prefira HTML/Tailwind puro** em vez de ArchitectureFlow. Use flexbox com divs e setas `→` ou `↓`. HTML escala corretamente com o layout do Slidev.

```html
<div class="flex items-center justify-center gap-4">
  <div class="px-4 py-3 border border-teal-400 rounded-xl text-sm">Entrada</div>
  <span class="text-gray-500 text-xl">→</span>
  <div class="px-4 py-3 border-2 border-amber-500 rounded-xl text-sm">Processamento</div>
  <span class="text-gray-500 text-xl">→</span>
  <div class="px-4 py-3 border border-green-500 rounded-xl text-sm">Saída</div>
</div>
```

Reserve `ArchitectureFlow` para diagramas técnicos complexos onde as coordenadas exatas importam (ex: arquitetura de microsserviços com muitos nós).

---

### Bug 5 — `<v-click>` com 4-space indent renderiza como bloco de código

**Sintoma**: O conteúdo de um `<v-click>` aparece como texto literal `<v-click>` / `<div class="...">` dentro de um `<pre><code>`, em vez de renderizar o HTML.

**Causa**: Markdown CommonMark interpreta 4 espaços de indentação no início de uma linha como um bloco de código, **mesmo quando o conteúdo está dentro de uma tag HTML**. Isso ocorre quando `<v-click>` e seus filhos ficam aninhados dentro de um `<div>` que já está a 2 espaços de indent — resultado: `<v-click>` fica a 4 espaços do início da linha.

**Regra**: Tags `<v-click>` e todo o conteúdo HTML dentro delas devem sempre estar a **0 ou 2 espaços** de indentação relativa ao início da linha — nunca a 4 ou mais. Quando necessário, refatore o HTML pai para reduzir o nível de aninhamento antes do `<v-click>`.

Errado (4-space → vira `<pre><code>`):
```
<div class="container">
  <div class="space-y-6">
    <v-click>            ← 4 espaços → bloco de código!
    <div class="card">
    </div>
    </v-click>
  </div>
</div>
```

Correto (0-space):
```
<div class="container">
<div class="space-y-6">

<v-click>               ← 0 espaços → renderiza corretamente
<div class="card">
</div>
</v-click>

</div>
</div>
```

---

### Bug 6 — Goto panel do Slidev fica visível no dev preview durante verificação

**Sintoma**: Uma lista de navegação com todos os slides aparece no canto superior direito do preview, sobrepondo o conteúdo.

**Causa**: O atalho `g` do Slidev abre um painel de autocomplete de navegação (`.autocomplete-list`). Chamadas a `navigate_page` pelo MCP do Chrome DevTools durante a verificação slide a slide podem acionar esse painel e deixá-lo aberto.

**Regra**: Ao criar um novo deck, adicionar sempre esta regra em `styles/index.css` para suprimir o painel no preview:

```css
/* Hide Slidev dev-mode goto/autocomplete panel */
.autocomplete-list { display: none !important; }
```

Nota: o painel não aparece em modo de apresentação fullscreen (`f`). A regra CSS é puramente para o dev preview.

---

### Bug 7 — `::left::` não é um slot válido no layout `two-cols`

**Sintoma**: Conteúdo colocado após `::left::` desaparece completamente — não renderiza nem no dev preview nem no PDF.

**Causa**: O layout `two-cols` do Slidev tem apenas dois slots: o slot padrão (default) e `::right::`. O marcador `::left::` não é reconhecido e o conteúdo entre ele e `::right::` é descartado silenciosamente.

**Regra**: Em layouts `two-cols`, coloque o conteúdo da coluna esquerda diretamente no slot padrão (logo após o frontmatter, sem nenhum marcador de slot). Use `::right::` apenas para a coluna direita.

Estrutura correta:
```
---
layout: two-cols
---

# Título

<!-- conteúdo da coluna esquerda — slot padrão, sem ::left:: -->
<div>...</div>

::right::

<!-- conteúdo da coluna direita -->
<div>...</div>
```

Estrutura errada (conteúdo entre `::left::` e `::right::` desaparece):
```
---
layout: two-cols
---

# Título

::left::                 ← NÃO EXISTE como slot — conteúdo abaixo é descartado

<div>...</div>

::right::

<div>...</div>
```

---

## Iteration loop

Quando o usuário pedir ajustes após Phase 4:
- Mudanças de conteúdo → edite `slides.md` com Edit.
- Novo componente custom necessário → crie em `components/` seguindo o padrão dos existentes.
- Troca de tema → ajuste o `theme:` no frontmatter (ex: `apple-basic`, `bricks`, `default`).
- Ritmo de animação → ajuste props (`duration`, `speed`, `autoPlay`) ou reorganize `v-click`s.

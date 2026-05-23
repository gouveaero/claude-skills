# Design quality — princípios + checklist auditável

Esta reference existe pra **resolver problemas durante a escrita do deck**, não depois. Os princípios abaixo são adaptados do `impeccable` skill mas re-pensados para o contexto de slides projetados em monitor / sala de evento. Use durante a Phase 4 (Generation), não como cleanup final.

Critique objetivo (assertions) está em `scripts/self-critique.mjs` — esse arquivo é a versão *humana* dos mesmos princípios, pra você internalizar enquanto escreve.

---

## Princípio 0 — Slide é diferente de página

Um deck não é uma landing page. A diferença muda 80% das decisões:

| Página web | Slide |
|---|---|
| Lida em monitor pessoal, próximo, com tempo | Lida em projetor a 5–10m de distância, em ≤ 7 segundos |
| Usuário decide o ritmo (scroll) | Apresentador decide o ritmo (click) |
| Conteúdo é o produto | Atenção do público é o ativo escasso |
| Tipografia 16–18px é ok | Tipografia ≥ 24px corpo, ≥ 60px títulos |
| 7 cores num componente é ok | 7 cores num slide = ruído |
| Muitos cards repetidos = lista | Muitos cards repetidos = template SaaS |

A regra prática: **um slide tem que entregar UMA ideia em UM olhar**. Se o público precisa "ler" o slide, ele já perdeu a fala.

---

## 1 — Register: brand vs product

Decks têm o equivalente de brand/product do impeccable:

- **Talk / palestra / keynote / pitch** = brand register. O deck **é** o produto. POV, voz, opinião. Pode (deve) arriscar estranheza. Tipografia distintiva, color strategy commitida, animação cinematográfica.
- **Status update / training / docs internas** = product register. O deck **serve** o produto (info). Restrained, claro, sem fricção, hierarquia firme.

Identifique antes de escolher tipografia, cor, layout. Se Phase 2 (Discovery) mencionou "pitch", "evento", "palestra", "conferência" → brand. Se mencionou "status", "report", "training", "documentação" → product.

Misturar registros: pitch com voz de status update = sai burocrático e ninguém lembra. Status update com voz de keynote = sai melodramático e ninguém confia.

---

## 2 — Color strategy (4 níveis de comprometimento)

Antes de escolher cores, escolha **a estratégia**:

| Estratégia | Uso | Quando aplicar |
|---|---|---|
| **Restrained** | Neutros tintados + 1 accent ≤ 10% da tela | Product register. Brand minimalista (Apple keynote dark). Treinamentos internos. |
| **Committed** | 1 cor saturada cobre 30–60% da composição | Brand default. Pitch deck onde a cor *é* a marca. |
| **Full palette** | 3–4 cores em papéis nomeados (primary action, secondary, warning, success) | Data viz, dashboards apresentados, comparações multi-categoria. |
| **Drenched** | A tela inteira é a cor | Hero slides (capa, climax, end). Quando você quer choque visual. |

**Regras invioláveis** (já no impeccable, valem aqui):

- Use **OKLCH** quando possível. Reduza chroma perto de lightness 0 ou 100.
- **Nunca** `#000` nem `#fff` puros — sempre tinte para a hue da marca (chroma 0.005–0.01 é suficiente).
- Restrained tem a regra "1 accent ≤ 10%" — Committed/Full/Drenched **rompem** essa regra de propósito. Não colapse tudo para Restrained por reflexo.

### Em deck especificamente

- Identifique a cor que carrega o deck (uma só, geralmente o accent principal).
- Reserve 1 cor **só** para o climax do deck (1 slide de tese, 1 slide de CTA). Se aparece em mais de 1 slide, perde o impacto.
- Para diagramas (mermaid, fluxos): use **luminance ramp** dentro da mesma hue ao invés de cores diferentes por categoria, exceto quando categorias forem semanticamente distintas (ex: erro vs sucesso).

---

## 3 — Tipografia em slides

### Hierarquia mínima

Slide bem hierarquizado tem **3 níveis tipográficos**, não 5+:

1. **Eyebrow / metadata** — Space Mono ou outra mono, ~0.75rem, letter-spacing 0.2–0.3em, color muted (≤ 60% opacity). Função: contexto de onde o slide está no arco.
2. **Title** — display font (Orbitron, Fraunces, Recoleta, etc), grande, 1 só por slide.
3. **Body** — sans humanista (Inter, Söhne, etc), legível à distância.

Sub-níveis (subtitle, caption) só quando necessários. Body com 2 weights diferentes (regular + bold pra ênfase) é mais forte que 4 sizes diferentes.

### Display (títulos)

- Slidev canvas default é 980×550. Um título com 10 caracteres ocupa ~7em de largura — então `font-size: 6rem` já encosta na margem.
- Sempre usar `clamp(min, vw-value, max)` + `text-wrap: balance` + `max-width: 90vw`. Sem isso, títulos longos cortam.
- Letter-spacing alto (0.05–0.1em) consome **muita** largura — reduz quando o título é longo (10+ chars).
- `white-space: nowrap` é última opção pra força força — prefira clamp menor.

### Reflex-reject (mesma lógica do impeccable)

Fontes saturadas em decks "tech" / "AI":

- Inter sozinho ✗ (default monocultura)
- IBM Plex Mono ✗ (reflexo "tech terminal")
- Space Mono em todo o deck ✗ (reservar pra eyebrow/metadata só)
- Orbitron em todo o deck ✗ (reservar pra title display só)

Combinações testadas que NÃO são reflexo:

- Orbitron (display) + Inter (body) + Space Mono (meta) → adequado pra brand "tech engineer cinematic"
- Fraunces (display) + Söhne (body) → editorial/luxury
- Migra Italic + Söhne → editorial moderno
- Söhne Mono (display) + Söhne (body) → swiss minimal

### Scale

Ratio ≥ 1.25 entre níveis. Scale plano (1.1× apart) = visual entediante.

---

## 4 — Layout

### Cap rígido por slide

- **Word count**: ≤ 25 palavras pro slide médio. ≤ 40 pra slide de detalhe denso. ≤ 12 pra hook / climax.
- **H1 count**: 1. Sempre 1.
- **Bullet count**: ≤ 5 por slide. Acima disso, quebra em 2 slides ou usa `<MetricGrid>` / `<Timeline>`.
- **Card grid**: máximo 4 cards iguais por slide. 6+ cards "idênticos com ícone + título + texto" é o template SaaS que o impeccable proíbe.

### Padding-bottom safety

Slidev `default` layout corta conteúdo em projetores 4:3 ou ultrawide. Sempre `padding-bottom: 2.5rem+` no `.slidev-layout` (já está no template default `styles/index.css`).

### Hierarquia de leitura

Cada slide tem que ter **1 ponto focal claro**. Se uma pessoa olha o slide e não sabe pra onde olhar primeiro em 0.5s, a hierarquia falhou.

Hierarquia é construída com:
- **Tamanho** (escala 1.5–2× entre primary e secondary)
- **Peso** (900 vs 400)
- **Cor / contraste** (accent vs muted)
- **Posição** (centro pra hero, topo-esquerda pra info densa)

Nunca tudo igual. Tudo igual = nada importante.

### Asymmetric > centered stack

Slide centrado vertical e horizontalmente em tudo = template. Asymmetric (título à esquerda, conteúdo balanceando à direita) lê como "designed". Mantenha center só pra slides hero (fact, statement, quote).

---

## 5 — Banimentos absolutos (slide deck edition)

Match-and-refuse. Se você está prestes a escrever isto, reescreva com estrutura diferente:

### A. Gradient text espalhado
**Proibido**: `background-clip: text` aplicado a múltiplos h1 no deck.
**Por quê**: gradient text é decoração, não significado. Se aparece em todo slide, vira ruído. O cérebro deixa de notar.
**Use**: solid color (white em dark, ink em light) para todos os títulos. **Reserve gradient para 1 slide específico** (climax / tese / CTA). Esse slide específico vira o momento visual do deck.

### B. Side-stripe borders
**Proibido**: `border-left: 4px solid <accent>` em cards, callouts, alerts.
**Por quê**: vestígio Bootstrap circa 2014. Lê como "alerta" mesmo quando não é alerta. Distrai.
**Use**: full borders 1px, ou background tint, ou número/ícone leading, ou nada.

### C. Hero metric template
**Proibido**: big number + small label + 3 supporting stats embaixo + gradient accent. SaaS landing page cliché.
**Por quê**: monocultura. Saturado.
**Use**: `<StatNumber>` único focado em 1 número quando o número é a tese; `<MetricGrid>` 2×2 quando vários números têm peso comparável. Não os dois no mesmo slide.

### D. Identical card grids
**Proibido**: 4+ cards com mesmo tamanho, mesmo padding, ícone+título+texto, repetidos.
**Por quê**: SaaS feature grid. Lê como "esta empresa usa um template".
**Use**: variar tamanhos (1 card grande + 3 menores), ou quebrar em 2 slides com narrativa, ou usar Timeline pra mostrar ordem.

### E. Glassmorphism como default
**Proibido**: `backdrop-filter: blur(20px)` decorativo em todo card.
**Por quê**: substitui pensamento por efeito.
**Use**: raro, com propósito (overlay sobre vídeo de fundo). Nunca como skin de card.

### F. Em dashes (—) substituindo pontuação
**Proibido**: usar `—` como pausa retórica universal.
**Por quê**: AI slop signature. Tipograficamente correto em 1–2 lugares; bug em todo parágrafo.
**Use**: vírgulas, dois-pontos, parênteses, ponto-final. Em dash só quando a frase **precisa** dele.

### G. Modal como primeira opção
**Proibido**: usar `<v-clicks>` pra esconder info que vai aparecer em modal.
**Por quê**: em slide não tem modal — tem reveal progressivo. Exaurir inline / progressivo antes de pensar em "outra camada".
**Use**: `<v-clicks>` direto no conteúdo, ou separar em 2 slides se a info exige espaço.

### H. Hierarquia plana
**Proibido**: 5 itens com mesmo peso, mesmo size, mesmo color em um slide.
**Por quê**: nada se destaca. Olho fica perdido.
**Use**: estabeleça primary/secondary com 1.5× escala mínimo + weight contrast (700 vs 400).

### I. Categoria-reflex
**Proibido**: deck "tech AI" automaticamente em fundo preto + acento azul/cyan. Deck "fintech" automaticamente navy + gold. Deck "saúde" automaticamente branco + teal.
**Por quê**: primeiro reflex de training data. Lê como "AI made that".
**Use**: pergunte "se o brief fosse outra coisa, qual cor escolheria?" Aplique essa cor com justificativa narrativa. Se isso quebra reconhecimento da categoria, ótimo — distinção é o ponto.

### J. Layout monocultura
**Proibido**: > 60% dos slides usando `default` ou `center`.
**Por quê**: 17 outros layouts existem (`fact`, `quote`, `statement`, `section`, `cover`, `intro`, `image-left`, `image-right`, etc.). Sub-uso = deck visualmente plano.
**Use**: alterne layouts deliberadamente. Slide de estatística → `fact`. Slide de citação → `quote`. Separador de capítulo → `section`. Hero → `cover` ou `statement`.

---

## 6 — Motion

- **Não anime** layout properties (`width`, `height`, `top`, `margin`). Use `transform` + `opacity`.
- **Ease out exponential** (`cubic-bezier(0.16, 1, 0.3, 1)` aka ease-out-quart). Sem bounce, sem elastic em deck profissional.
- **Duração**: entry animations 400–800ms. Mais que isso vira distração.
- **v-motion stagger**: delay entre elementos 80–150ms. Reveal cascateado é o efeito.
- **Magic Move**: usa default 800ms. Não acelere — o cérebro precisa acompanhar a transformação.

Animação que não comunica nada deve ser cortada. Cada animação responde "por que isso se move?" — se a resposta é "pra ficar bonito", remova.

---

## 7 — Copy

- **Cada palavra ganha o lugar dela.** Se uma palavra pode ser removida sem perder sentido, remova.
- **Não repita o título no body** ("Nosso processo" como título + "Como funciona o nosso processo..." como body = redundância).
- **Eyebrow tem que ser metadata** ([CAPÍTULO 01], [TELEMETRIA], [ATO III]), não duplicar o título.
- **Substitua jargão por demonstração.** "Inovador" → mostre o que faz; "robusto" → mostre o teste.
- **Português**: evite "aprimorar", "alavancar", "otimizado" — palavras que viraram corporativo-genérico.

---

## 8 — AI slop test (slide deck edition)

Se alguém olha o deck e diz "AI fez isso" sem dúvida, falhou. Pra deck especificamente, os sinais:

| Sinal | Conserto |
|---|---|
| Fundo preto + gradient cyan/purple em todo título | Solid white em quase todos os títulos; gradient só em 1 slide-climax |
| 4 cards iguais com ícone+título+texto repetidos | Variar tamanho, ou usar componente diferente (Timeline, MetricGrid 2×2) |
| Em-dashes em todos os subtítulos | Trocar por vírgulas/dois-pontos; reservar em-dash para 1–2 momentos |
| Stack de cards centralizados verticalmente em todo slide | Asymmetric layouts; usar `image-left`, `two-cols-header`, layouts variados |
| Mesma fonte (Inter) em tudo + Orbitron em tudo | Pareamento testado com voz específica; verificar lista reflex-reject |
| Todos slides com `default` layout | Map de slide-tipo → layout (statement, fact, quote, etc.) |
| "Hero metric template" repetido | Reservar pra 1 slide; outros usam StatNumber simples ou prosa |
| Acento cyan/azul em deck "tech" | Justifique a cor por narrativa, não por categoria |

---

## Checklist Phase 4 — antes de declarar slide pronto

Para cada slide que você escreve, passe mentalmente:

```
□ Tem 1 ponto focal claro (em 0.5s o olho sabe pra onde ir)?
□ Word count ≤ 25 (hook ≤ 12)?
□ Layout escolhido por propósito (não default por reflexo)?
□ Cor accent usada com intenção (não decorativa)?
□ Hierarquia tipográfica visível (≥ 1.5× scale entre primary/secondary)?
□ Animação responde "por que isso se move?"?
□ Nenhum dos 10 banimentos absolutos está presente?
□ Copy passou pelo teste "cada palavra ganha o lugar"?
□ AI slop test: posso explicar por que UM título é gradient e o resto não?
```

E para o deck completo:

```
□ Variedade de layouts (< 60% default/center)?
□ Gradient text aparece em ≤ 1 slide?
□ Color strategy declarada e consistente?
□ Pareamento tipográfico justificado (não reflex-reject)?
□ Slide count entre 5 e 40?
□ Ao menos 1 feature premium usada (magic-move, mermaid, latex, InteractivePoll, ROICalculator)?
```

Falhar QUALQUER item desta lista é OK durante draft — não é OK quando declara pronto.

---

## Conexão com self-critique automático

`scripts/self-critique.mjs` checa um subset dos itens acima automaticamente (os que dão pra assertar objetivamente em código): word count, h1 count, gradient text count, layout variety, em-dash count, side-stripe presence, font count, slide count, feature showcase.

Os checks **subjetivos** (color strategy commitida, hierarquia visível, AI slop test) ficam pra você durante a Phase 4. O critique automático é um safety net, não substituto do julgamento.

Output do critique:
- **PASS** = nenhum item objetivo falhou. Pode deployar.
- **WARN** = item passa mas marginalmente; revise se vale ajustar.
- **FAIL** = item viola hard rule. Conserte antes de declarar pronto.

Exit code: 0 = PASS, 1 = FAIL (WARN não bloqueia).

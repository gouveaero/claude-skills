# Automação do Freepik Pikaso (chrome-devtools MCP) — DEPRECATED

> **DEPRECATED desde 2026-05-20.** Mantido só como fallback se o runtime Playwright em `automation/run_freepik.py` quebrar. Fluxo principal vive em `SKILL.md` + `references/playwright-freepik.md`.
>
> **Por que foi deprecado:** `execCommand('insertText')` cola o prompt instantâneo, `setTimeout(r, 700)` é timing determinístico, e os clicks não passam por mouse-movement — tríade que provavelmente causou o bloqueio da conta Freepik em maio/2026. A versão Playwright corrige isso com `page.type()` caractere-a-caractere + mouse em passos + pausas randomizadas + cap de sessão.

## Pré-requisitos

- chrome-devtools MCP instalado (ferramentas `mcp__chrome-devtools__*` disponíveis na sessão).
- Credenciais em `credentials.local.json` na pasta da skill (gitignored). Schema:
  ```json
  { "freepik": { "email": "...", "password": "...", "loginUrl": "...", "pikasoUrl": "..." } }
  ```
- Plano com geração ilimitada ativo.

## Filosofia token-eficiente

**Nunca use screenshots ou `take_snapshot` durante o loop.** Tudo é feito via JS rodando dentro da página através de `evaluate_script`, retornando apenas primitivos.

Todos os seletores abaixo são **estáveis** (atributos `data-cy`, `name`, `id`). Mudam raramente.

## Projetos Pikaso (seletor de projeto na sidebar)

O Pikaso organiza todas as criações em **projetos** (pastas de alto nível). Antes de submeter qualquer prompt, garanta que a UI está no projeto correto — senão as imagens vão pro projeto errado.

### Projetos atuais (verificado via DOM em 2026-04)

| Nome no UI do Pikaso | Slug canônico (usado em YAML headers) |
|---|---|
| `Projeto pessoal` | `pessoal` |
| `UFMG` | `ufmg` |
| `Spoiler` | `spoiler` (legado) |
| `Tribotax` | `tribotax` |
| `Exos` | `exos` |
| `Vhoe.co` | `vhoe` |
| `SAIF` | `saif` |

O mapeamento slug ↔ nome UI vive em `imagens-freepik/SKILL.md` §"Mapeamento de projetos" — editar lá quando projetos forem criados/renomeados.

### Seletores DOM do popover de projetos

| Seletor | O que é |
|---|---|
| `[data-cy="sidebar-project-selector"]` | Botão na sidebar que mostra o projeto ATIVO. `aria-label` = nome do projeto ativo. Clicar via MCP `click` abre o popover. |
| `[data-cy="projects-selector-menu"]` | `role="dialog"` — o popover aberto com a lista |
| `[data-cy="projects-selector-sidebar-content"]` | Container da lista scrollável dentro do popover |
| `[data-cy="projects-selector-sidebar-bottom"]` | Rodapé do popover (contém "Novo projeto") |
| `[data-cy="header-current-project-link"]` | Link no header com nome + href (UUID do projeto ativo) |

Cada item de projeto no popover é `BUTTON > DIV > DIV.flex.h-8 > DIV.text-surface-foreground-0` onde o DIV folha contém o nome UI exato. **Itens NÃO têm `data-cy` individual** — seleção é por `innerText` normalizado.

### Fluxo — garantir projeto correto ANTES do loop de submissão

1. **Ler projeto ativo**:
   ```javascript
   () => {
     const btn = document.querySelector('[data-cy="sidebar-project-selector"]');
     return { currentUiName: btn && btn.getAttribute('aria-label') };
   }
   ```
2. **Normalizar para slug** (case-insensitive, strip `.co`): `"Vhoe.co"` → `vhoe`, `"Projeto pessoal"` → `pessoal`.
3. Se slug ativo == slug target → **skip**, já está no lugar certo.
4. Se slug ativo ≠ slug target:
   - Pegar `take_snapshot`, achar `uid` do botão "Projeto pessoal" (ou qualquer projeto) na navegação.
   - `mcp__chrome-devtools__click` com esse uid (via `.click()` JS o popover fecha antes do próximo script rodar — é essencial usar o MCP click nativo).
   - `wait_for(["Todos os projetos","Novo projeto"])` — confirma popover aberto.
   - JS: procurar dentro de `[data-cy="projects-selector-menu"]` o `BUTTON` cujo `innerText` contém o nome UI target (case-insensitive). Clicar.
   - `wait_for(text=<nome UI target>)` na breadcrumb do header.
5. Se nome target NÃO existe na lista → **PAUSAR e perguntar ao user**: `"Projeto '<nome>' não existe na conta Pikaso. Opções: (a) criar o projeto agora, (b) usar outro projeto da lista [<lista>], (c) cancelar."` Nunca criar silenciosamente.
6. Se user aprovou criar → clicar "Novo projeto" no rodapé, preencher, aguardar estar ativo.

### Script de confirmação pós-troca

```javascript
() => {
  const btn = document.querySelector('[data-cy="sidebar-project-selector"]');
  const header = document.querySelector('[data-cy="header-current-project-link"]');
  return {
    ariaLabel: btn && btn.getAttribute('aria-label'),
    headerText: header && header.innerText.trim(),
    headerHref: header && header.getAttribute('href'),
  };
}
```

---

## Seletores estáveis

### Login page (`https://www.freepik.com/log-in?client_id=freepik&lang=pt`)

```
input[name="email"]               — campo email
input[name="password"]            — campo senha
input[name="keep-signed"]         — checkbox "manter conectado"
button#submit                     — botão submit
```

Primeiro a página exibe só o email + botão "Continuar com o e-mail". Clique nesse botão, aí o campo de senha aparece.

### Pikaso main UI (`https://br.freepik.com/pikaso/ai-image-generator`)

```
[data-cy="image-prompt-input"] [contenteditable="true"]  — campo do prompt (contenteditable, não textarea)
[data-cy="tti-mode-selector-v3-trigger"]                 — trigger do seletor de modelo
[data-cy="ai-model-selector-show-all-button"]            — expandir lista completa de modelos
[data-cy="ai-model-item-imagen-nano-banana-2"]           — Google Nano Banana Pro (ALVO)
[data-cy="image-aspect-ratio-input"]                     — trigger do aspect ratio (Radix popover)
[data-cy="image-resolution-input"]                       — trigger da resolução (1K / 2K), Radix popover
[data-cy="popover-option"]                               — opções dentro de dropdowns (filtrar por textContent)
[data-cy="unlimited-mode-toggle-button"]                 — toggle modo ilimitado
[data-cy="generate-button"]                              — botão Gerar
[data-cy="feed-virtual-item"]                            — itens do feed (alterna header/body)
[data-cy="feed-virtual-item-header"]                     — header (altura ~42px, contém prompt)
[data-cy="generated-image-group"]                        — grupo de geração (dentro do header)
[data-cy="main-feed-gallery"]                            — container do feed virtualizado
```

### Indicadores de estado do feed (strings no `textContent` do body)

| Texto no item body | Estado |
|---|---|
| `Preparando…` | Fila local antes de enviar ao servidor |
| `Gerando… ~1 minutos` | Em geração |
| `Na filaPular filaCancelar` | Na fila (modo acelerado pode pular) |
| `1K` ou `2K` (tags de resolução em img) | Imagem pronta |

## Padrões JS críticos

### Setar texto em contenteditable (React controla o input)

JSX normal `.value =` NÃO dispara o onInput do Vue/React. Use `execCommand`:

```javascript
const editable = document.querySelector('[data-cy="image-prompt-input"] [contenteditable="true"]');
editable.focus();
document.execCommand('selectAll', false, null);
document.execCommand('delete', false, null);
document.execCommand('insertText', false, JSON.stringify(promptObj, null, 2));
```

### Abrir popover Radix (aspect ratio / modelo)

`.click()` via JS NÃO abre popovers Radix-Vue. Use `focus()` + press_key MCP:

```javascript
// 1. JS
document.querySelector('[data-cy="image-aspect-ratio-input"]').focus();
// 2. MCP
await press_key("Enter");
// 3. Agora JS .click() nas opções funciona:
const options = [...document.querySelectorAll('[data-cy="popover-option"]')];
options.find(o => /4.*5/.test(o.textContent))?.click();
```

### Limite de clique no botão Gerar

Clicar no `[data-cy="generate-button"]` desabilita o botão por ~8 segundos. Tentar clicar múltiplas vezes no mesmo tick sem esperar resulta em apenas 1 request submetido (os subsequentes são engolidos).

**Então**: 1 click por prompt. Para ter N variações de um slide, fire N prompts diferentes ou repita o mesmo prompt N vezes com wait entre clicks (~8s).

A fila global aceita **múltiplas gerações em paralelo** (observado: 5+ simultâneas). O usuário só paga o cooldown do botão entre submissões.

## Fluxo de execução

### Passo 1 — Garantir página aberta e logada

```
mcp__chrome-devtools__list_pages
```

- Se uma aba `pikaso/ai-image-generator` está aberta **e** não redireciona pra login → ok.
- Se não → abrir `loginUrl` e executar fluxo de login (abaixo), depois navegar para `pikasoUrl`.

#### Login (se necessário)

```javascript
// 1. Preencher email
const setVal = (el, v) => {
  const set = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;
  set.call(el, v);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
};
setVal(document.querySelector('input[name="email"]'), EMAIL);
// 2. Click "Continuar com o e-mail"
[...document.querySelectorAll('button')].find(b => /continuar.*e.*mail/i.test(b.textContent))?.click();
```

Aguarde ~1s via `wait_for(["Senha","Password"])`, então:

```javascript
setVal(document.querySelector('input[name="password"]'), PASSWORD);
document.querySelector('button#submit').click();
```

Aguarde redirecionamento (`wait_for(["Pikaso","Criar","Gerar"])`).

### Passo 2 — Selecionar modelo Nano Banana Pro (uma vez por sessão)

```javascript
// Lê modelo atual — se já é nano-banana-2, pula.
const trigger = document.querySelector('[data-cy="tti-mode-selector-v3-trigger"]');
trigger.focus();
```

Press_key Enter (MCP), depois:

```javascript
document.querySelector('[data-cy="ai-model-selector-show-all-button"]')?.click();
// aguardar 200ms
document.querySelector('[data-cy="ai-model-item-imagen-nano-banana-2"]').click();
```

### Passo 3 — Escolher proporção (`9:16` default, `4:5` sob pedido)

Default = `9:16`. Use `4:5` apenas se o usuário pediu explicitamente em algum momento da conversa. **Não pergunte** — use o default.

```javascript
document.querySelector('[data-cy="image-aspect-ratio-input"]').focus();
```

Press_key Enter (MCP), depois:

```javascript
const want = '9:16'; // ou '4:5' se o usuário pediu
[...document.querySelectorAll('[data-cy="popover-option"]')]
  .find(o => o.textContent.includes(want))?.click();
```

### Passo 3b — Garantir resolução 2K (Nano Banana Pro unlimited)

**Default = 2K**. O plano ilimitado do Nano Banana Pro cobre 2K sem custo extra, então sempre suba pra 2K. Cheque antes do loop de submissão. Se já está em "2K", pule.

```javascript
// Lê resolução atual
document.querySelector('[data-cy="image-resolution-input"]')?.innerText?.trim();
// Se retorna "1K", abrir popover:
document.querySelector('[data-cy="image-resolution-input"]').focus();
```

Press_key Enter (MCP), depois:

```javascript
[...document.querySelectorAll('[data-cy="popover-option"]')]
  .find(o => /2K/i.test(o.textContent))?.click();
```

### Passo 4 — Modo de gatilho

**Default = Normal**: submeter um prompt, esperar ~8s cooldown, submeter o próximo. Quando a fila global fica cheia, itens ficam em "Na fila" — apenas aguardar. Sem custo extra de créditos. **Não pergunte** — use Normal.

**Modo Acelerado (opcional, só se o usuário pediu explicitamente)**: após submeter tudo, para cada item que está "Na fila", clicar "Pular fila" (custa 75 créditos cada).

### Passo 5 — Loop de submissão (PADRÃO BUNDLED — token-eficiente)

**Regra**: envie os slides de UM CARROSSEL INTEIRO em UMA ÚNICA chamada `evaluate_script`. Não faça uma chamada por slide — isso multiplica tool-call overhead e tokens de boilerplate.

Para cada carrossel (3 carrosséis = 3 chamadas totais, não 21+):

```javascript
async (slidesArray) => {
  // slidesArray = [{ slide: "s1", prompt: {...} }, { slide: "s2", prompt: {...} }, ...]
  const editable = document.querySelector('[data-cy="image-prompt-input"] [contenteditable="true"]');
  const btn = document.querySelector('[data-cy="generate-button"]');
  const VARIATIONS = 3;
  const results = [];
  for (const { slide, prompt } of slidesArray) {
    const promptText = JSON.stringify(prompt); // compacto, sem pretty-print
    for (let v = 0; v < VARIATIONS; v++) {
      editable.focus();
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
      document.execCommand('insertText', false, promptText);
      const start = Date.now();
      while (btn.disabled && Date.now() - start < 20000) await new Promise(r => setTimeout(r, 300));
      if (!btn.disabled) btn.click();
      results.push({ slide, v: v + 1, waitMs: Date.now() - start, clicked: !btn.disabled });
      await new Promise(r => setTimeout(r, 700));
    }
  }
  return { total: results.length, results };
}
```

**IMPORTANTE** — `evaluate_script` aceita funções JS, não argumentos nomeados livres; você precisa **colar o array de slides inline no JS** dentro da chamada. Ou seja, o bloco `slidesArray = [...]` deve ser construído dentro da função retornada. Exemplo completo:

```javascript
async () => {
  const slides = [
    { slide: "s1", prompt: { prompt: "...", subject: "...", /* ... */ } },
    { slide: "s2", prompt: { /* ... */ } },
    // ... todos os N slides do carrossel
  ];
  // … loop idêntico ao acima …
}
```

**Granularidade de falha**: 1 chamada por carrossel é o ponto ideal — se a chamada falhar, só reexecuta aquele carrossel. Não bundleie os 3 carrosséis em 1 call só (risco maior, benefício marginal de tokens).

**JSON compacto**: use `JSON.stringify(obj)` (sem `null, 2`). O gerador não liga pro pretty-print e você economiza ~15% dos caracteres que vão pro campo do Pikaso.

**Quantas variações por slide?** Default = **3**. Para alterar, mude `VARIATIONS` no topo da função.

**Cooldown**: ~8s entre clicks (Pikaso desabilita o botão). O `while (btn.disabled)` cobre isso. Não dorma além disso.

### Passo 6 — Modo acelerado (opcional)

Depois de todas as submissões, se o usuário escolheu "acelerado":

```javascript
() => {
  const items = [...document.querySelectorAll('[data-cy="feed-virtual-item"]')];
  let count = 0;
  for (const el of items) {
    if (/Na fila/i.test(el.textContent)) {
      const pularBtn = [...el.querySelectorAll('button, [role="button"]')]
        .find(b => /Pular fila/i.test(b.textContent));
      pularBtn?.click();
      count++;
    }
  }
  return count;
}
```

Avise o usuário do custo: `count × 75 créditos`.

### Passo 7 — Polling sem IA

Use `evaluate_script` com esta função a cada 15s até convergir:

```javascript
() => {
  const items = [...document.querySelectorAll('[data-cy="feed-virtual-item"]')];
  let inflight = 0, queued = 0, done = 0;
  for (const el of items) {
    const t = el.textContent;
    if (/Gerando|Preparando/i.test(t)) inflight++;
    else if (/Na fila/i.test(t)) queued++;
    else {
      const imgs = [...el.querySelectorAll('img')].filter(im => im.naturalWidth > 0 || im.src).length;
      if (imgs > 0) done += imgs;
    }
  }
  return { inflight, queued, done };
}
```

Pare quando `inflight === 0 && queued === 0` por 2 pools seguidos.

**Atenção**: o feed é virtualizado. Para ver TODOS os itens, é preciso rolar o container (`[data-cy="main-feed-gallery"]` achando o pai `overflow-y: auto`) e agregar por `data-index`. Veja o exemplo de agregação no script de contagem abaixo.

### Passo 8 — Contagem final por slide

```javascript
async () => {
  // Scrollar todo o feed para agregar items virtualizados
  let container = document.querySelector('[data-cy="main-feed-gallery"]');
  while (container && getComputedStyle(container).overflowY !== 'auto' && getComputedStyle(container).overflowY !== 'scroll') {
    container = container.parentElement;
  }
  const seen = new Map();
  for (let y = 0; y <= container.scrollHeight; y += 400) {
    container.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 120));
    for (const el of document.querySelectorAll('[data-cy="feed-virtual-item"]')) {
      const idx = el.getAttribute('data-index');
      if (seen.has(idx)) continue;
      const h = Math.round(el.getBoundingClientRect().height);
      const isHeader = h < 80;
      const imgs = [...el.querySelectorAll('img')].filter(im => im.naturalWidth > 0).length;
      seen.set(idx, { idx: +idx, isHeader, imgs, text: el.textContent.slice(0, 80) });
    }
  }
  container.scrollTo(0, 0);
  return [...seen.values()].sort((a, b) => a.idx - b.idx);
}
```

### Passo 9 — Encerramento

Reporta no terminal:
```
Carrossel <codinome> finalizado.
<N> slides × <V> variações = <total> imagens geradas.
Acesse o Pikaso para revisar e baixar suas favoritas.
```

A skill NÃO baixa as imagens.

## Tratamento de erros

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| Redirecionamento pra `/log-in` durante loop | Sessão expirou | Pausa, executa Passo 1 login, retoma |
| `[data-cy="generate-button"]` ausente | Página não carregou completamente | `wait_for(["Gerar","Generate"])`, retenta |
| Toast "limite atingido" | Créditos esgotados | Pausa, avisa o usuário |
| Polling não converge em 15 min | Algo trava | Pausa, pede intervenção manual |
| Popover não abre após `focus()` | Press_key Enter não chegou | Tente `ArrowDown` como alternativa |

## Modo "dry-run"

Se o usuário pedir dry-run, execute tudo exceto o `click()` do botão Gerar. Reporte os seletores encontrados e os prompts que SERIAM enviados.

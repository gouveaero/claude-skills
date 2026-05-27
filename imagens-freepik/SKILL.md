---
name: imagens-freepik
description: Skill generalista para geração de imagens no Freepik Pikaso (Nano Banana Pro) a partir de qualquer arquivo markdown com header YAML + blocos JSON de prompt. Garante que o projeto Pikaso correto está ativo antes de submeter, aplica `variations` por prompt, faz polling sem IA e executa hooks `on_complete` (mover arquivo, atualizar índices). Serve para qualquer projeto (Vhoe, Saif, TriboTax, Exos, UFMG, pessoal) — o fluxo Vhoe passa por aqui via backlog, mas a skill não depende da Vhoe. Use quando o usuário disser "gera as imagens desse carrossel", "submete isso no Pikaso", "roda `imagens-freepik X.md`", "faz as imagens da campanha Saif", ou equivalentes — sempre que existir um markdown com prompts JSON pronto para virar imagem.
---

# imagens-freepik — geração no Pikaso via runtime Playwright humanizado

Skill generalista. Recebe um caminho de arquivo markdown como input. O arquivo tem:
1. Um **header YAML** com config de geração (projeto Pikaso, aspect, variations, etc.)
2. Um ou mais **blocos ```json```** com prompts Nano Banana Pro (cada bloco = 1 imagem).

A skill submete cada prompt × `variations` no Pikaso, garante o projeto correto ativo, faz polling até convergir, e executa os hooks `on_complete` (mover arquivo, atualizar índices).

**Runtime:** Chrome real via Playwright com sessão persistente, digitação caractere a caractere, mouse em passos, pausas randomizadas e cap de 30 submissões/sessão. Não é mais Chrome DevTools MCP — esse fluxo está em `references/legacy/freepik-automation.md` como fallback. **Não voltar pro MCP sem aprovação explícita** — o MCP-flow foi o que causou o bloqueio anterior da conta.

## O que esta skill NÃO faz

- **Não escreve prompts.** Os JSONs já precisam existir no markdown.
- **Não é Vhoe-específica.** Serve pra qualquer projeto.
- **Não baixa imagens.** Elas ficam no Pikaso pro user revisar.
- **Não cria projetos Pikaso silenciosamente.** Se o projeto do header não existe, pausa e pergunta.
- **Não desliga a humanização.** Não existe flag pra isso por design.

## Input aceito

Caminho de um arquivo markdown. Exemplos válidos:
- `carrosseis_backlog/10_codinome.md` (ciclo Vhoe)
- `🚀_Projects/Saif/creative_briefs/c01.md` (ad isolado Saif)
- `teste_ad.md` (qualquer markdown com header YAML + JSONs)

Se o user invocar sem caminho, pergunte qual arquivo.

### Flags opcionais na invocação

Passadas direto pro script (ver §"Como o Claude invoca o runtime"):

- `--only s1,s3` → regenera só os blocos JSON com label `s1` e `s3`. Útil pra ressubmeter slides rejeitados sem refazer o carrossel inteiro. O label vem do heading antes do bloco JSON (ver §"Formato do markdown"). Se não houver headings, usa índice posicional (`s1` = 1º bloco, `s2` = 2º, etc.).
- `--dry-run` → executa tudo (login, projeto, digitação) **exceto** o click final em Gerar. Reporta o que SERIA submetido.
- `--variations N` → override do `variations` do header YAML.
- `--headed` (default) / `--headless` → controla visibilidade do browser. Sempre prefira headed: headless tem fingerprint detectável.

## Formato do markdown

### Header YAML (frontmatter)

```yaml
---
project: vhoe              # OBRIGATÓRIO. Slug: pessoal | ufmg | spoiler | tribotax | exos | vhoe | saif
aspect: 9:16               # default 9:16. Alternativas: 4:5, 1:1, 16:9
variations: 3              # default 3 variações por prompt
resolution: 2K             # default 2K (Nano Banana Pro ilimitado cobre)
model: nano-banana-2       # default nano-banana-2 (Google Nano Banana Pro)
mode: normal               # default normal (fila padrão). Alternativa: acelerado (75 créditos/skip)
on_complete:               # opcional — hooks pós-convergência
  move_to: carrosseis_gerados/           # se definido, move o .md para essa pasta ao convergir
  update_indices:                         # se definido, lista de _INDICE.md a atualizar
    - carrosseis_gerados/_INDICE.md
label: "10_codinome"       # opcional — prefixo de log no runner (aparece como "10_codinome/s1/v1")
---
```

Se `project` estiver ausente, o script tenta inferir pelo caminho. Se ainda ambíguo, retorna `status: needs_user_input` e o Claude pergunta.

### Blocos JSON de prompt

Cada bloco ```json``` no corpo do markdown é uma imagem a gerar. O script extrai em ordem de aparição.

Para permitir regen parcial via `--only`, prefixe o bloco com um heading `### Slide N` ou `## SN — <função>`. O script extrai o identificador (`sN`) do heading que precede o bloco. Sem heading: usa índice posicional.

Exemplo:

````markdown
## Slide 1 — hook

```json
{ "prompt": "...", "subject": "...", "camera": "...", "lighting": "...", "mood": "...", "style": "...", "constraints": ["..."] }
```
````

## Mapeamento de projetos (slug ↔ nome UI do Pikaso)

Fonte de verdade. Editar aqui quando projetos forem criados/renomeados no Pikaso. **Manter sincronizado** com `PROJECT_SLUG_TO_UI` em `automation/run_freepik.py`.

| Slug (YAML) | Nome exato no UI do Pikaso | Quando usar |
|---|---|---|
| `pessoal` | `Projeto pessoal` | Catch-all / experimentos / imagens pessoais |
| `ufmg` | `UFMG` | Faculdade |
| `spoiler` | `Spoiler` | Legado (nome antigo do TriboTax) |
| `tribotax` | `Tribotax` | Projeto Alex Agrotax (rebrand para TriboTax) |
| `exos` | `Exos` | Agência Exos |
| `vhoe` | `Vhoe.co` | Carrosséis / ads da Vhoe |
| `saif` | `SAIF` | Zahnspangehome / Saif |

### Inferência por caminho (quando `project` ausente no YAML)

| Caminho contém | Slug inferido |
|---|---|
| `🚀_Projects/Projeto_Vhoe/` ou `/Vhoe/` ou `vhoe.co` | `vhoe` |
| `🚀_Projects/Saif/` ou `/Saif/` ou `zahnspangehome` | `saif` |
| `🚀_Projects/Alex_Agrotax/` ou `/TriboTax/` ou `/Tribotax/` | `tribotax` |
| `🚀_Projects/Exos/` ou `/Exos_` | `exos` |
| `/UFMG/` ou `/Faculdade/` | `ufmg` |
| `🚀_Projects/Projeto_EU/` ou `/Pessoal/` | `pessoal` |
| (nenhum match) | **status `needs_user_input`** |

## Cadência e humanização (não-negociável)

| Limite | Valor | Por quê |
|---|---|---|
| Cap por sessão | **30 submissões** | Bloqueio Freepik de maio/2026 aconteceu em sessão com ~36 cliques rápidos. 30 deixa margem. |
| Cap por hora rolante | **60 submissões** | Bots típicos fazem 100+/h. Humano intenso fica em 40-60/h. |
| Pausa entre submissões | **12-25s aleatório** | Sub-10s é assinatura de bot. |
| Break a cada 5-10 subs | **+30-90s extra** | Humano para pra olhar, beber café, conferir. |
| Sessão idle | **30min reseta sessão** | Janela de retomada natural. |
| Block cooldown | **60min** | Se detectou bloqueio, novos runs barrados por 1h. |
| Digitação | **Gauss(μ=80ms, σ=30ms)/caractere** | ~12 cps com pausas de pensamento ocasionais. |
| Typo + correção | **3% chance** | Realismo. |
| Mouse antes do click | **15-35 steps até ponto aleatório do bbox** | Sem isso o click "teletransporta". |
| Headless | **proibido por default** | Headless tem fingerprint detectável. |

Estado persistido em `.session_state.json` (gitignored). Quando algum cap é atingido, o script retorna `status: cap_reached` com `resume_suggested_at_iso`. **O Claude reporta isso ao usuário e oferece retomar via `--only <remaining_labels>` depois do horário sugerido.** Não retentar antes.

## Tabela de rationalizations (red flags)

Quando esses pensamentos surgirem, **pare e leia a coluna direita**:

| Pensamento | Realidade |
|---|---|
| "Usuário tá com pressa, vou desligar a humanização" | Pular humanização = vetor do bloqueio anterior. Atraso de 24h+ pra desbloquear > 5min a mais agora. |
| "Só essa rajada rápida, depois volto pro padrão" | Cloudflare/Freepik analisa a sessão inteira, não slot a slot. |
| "30 é arbitrário, deixa eu fazer 50" | Cap existe porque o bloqueio aconteceu. Mexer só com aprovação explícita do usuário. |
| "Vou voltar pro Chrome DevTools MCP, é mais rápido" | MCP-flow foi exatamente o que causou o bloqueio. Está em `references/legacy/` por isso. |
| "Vou usar `page.fill()` em vez de `page.type()` que é mais rápido" | `page.fill()` cola instantâneo. `page.type()` com `delay` é obrigatório. |
| "O captcha foi falso positivo, retomo de imediato" | Captcha = sinal forte de bot. Para, reporta, espera intervenção humana. |
| "Vou pedir pro user e ele topa relaxar o cap" | Só relaxar com aprovação **explícita** registrada na conversa, e mesmo assim ajustar `CAP_PER_SESSION` no script — não na chamada. |

## Como o Claude invoca o runtime

```bash
python ~/.claude/skills/imagens-freepik/automation/run_freepik.py \
  <caminho_md> [--only s1,s3] [--dry-run] [--variations N] [--headed]
```

O script:
- Abre Chrome real (channel="chrome") com profile persistente em `.playwright-profile/`.
- Faz login (1ª vez) ou reusa sessão (`credentials.local.json` para login).
- Garante o projeto Pikaso correto ativo.
- Configura modelo, aspect, resolução conforme YAML.
- Submete cada prompt × variations com humanização.
- Faz polling até convergir.
- Imprime **JSON estruturado na última linha do stdout** (logs em stderr, não atrapalham).

Schema completo do JSON: `references/playwright-freepik.md` §"Schema do JSON de retorno".

### Decisão por `next_action`

Claude lê o JSON e decide:

| `next_action` | O que fazer |
|---|---|
| `run_on_complete` | Status converged. Executar hooks YAML: `move_to` (Passo on_complete-1) + `update_indices` (Passo on_complete-2). Depois relatar ao usuário (Passo final). |
| `partial_retry` | Alguns labels não fired ou não done. Reportar quais (do `remaining_labels`) e sugerir `python ... --only <labels>` numa nova invocação (pode rodar agora se cap permite). |
| `wait_then_resume` | Cap atingido. Mostrar `resume_suggested_at_iso` ao usuário; oferecer agendar retomada com `--only <remaining_labels>`. |
| `alert_user_blocked` | Bloqueio detectado. Mostrar `block_evidence`. **Não retentar automaticamente.** Sugerir checar conta manualmente; o cooldown de 60min está ativo. |
| `ask_user` | Mostrar `prompt_for_user` (ex.: projeto não existe). Aguardar decisão antes de qualquer ação. |

## Fluxo de execução (alto-nível)

### Passo 1 — Preparar invocação
Receber caminho do .md. Validar que existe. Identificar quais flags repassar:
- `--dry-run` se o usuário quer validar sem gastar fila;
- `--only` se está ressubmetendo slides específicos;
- `--variations N` se o usuário quer override pontual.

### Passo 2 — Rodar o script
```bash
python automation/run_freepik.py <md> [flags]
```
Capturar stdout. O JSON está na **última linha** do stdout (logs intermediários vão pra stderr).

### Passo 3 — Parsear JSON e ramificar por `next_action`
- `run_on_complete` → Passo 4 (hooks).
- `wait_then_resume` / `alert_user_blocked` / `ask_user` → reportar ao usuário, parar.
- `partial_retry` → relatar e sugerir comando de regen.

### Passo 4 — `on_complete` hooks (só se `next_action == run_on_complete`)

#### 4a. `on_complete.move_to: <pasta>`
Mover o .md de entrada pra pasta destino. Ex: `carrosseis_backlog/10_codinome.md` → `carrosseis_gerados/10_codinome.md`. Usar `git mv` se repo git (preserva histórico); senão `mv`. Confirmar destino existe.

No corpo do .md, próximo à seção `## Resumo` no campo `- **Status**:`, substituir `pendente de geração de imagem` por `Gerado em <YYYY-MM-DD>, imagens no Pikaso projeto <slug>`.

#### 4b. `on_complete.update_indices: [lista]`
Para cada arquivo da lista:
- Se não existe → criar com header mínimo.
- Prepend uma entrada nova após a seção "Padrões recentes" (ou no topo, depois do H1, se não existir seção).

**Formato Vhoe** (quando `label` segue padrão `NN_codinome`):

```markdown
## NN — <Codinome> — <YYYY-MM-DD>
- **Tema**: (copiar da seção Resumo do .md)
- **Framework/Estética/Série**: ... / ... / ...
- **Regime tipográfico**: ...
- **Slides (resumo)**: s1 ..., s2 ..., ...
- **Pilares DNA**: ...
- **Métricas (D+3)**: pendente

---
```

**Outros índices**: formato mínimo `- <YYYY-MM-DD> [<label>](<novo_caminho>)`.

### Passo 5 — Atualizar `_INDICE_BACKLOG.md` (quando há `move_to`)
Se o .md saiu de `carrosseis_backlog/`, remover entrada correspondente do `_INDICE_BACKLOG.md` (se existir).

### Passo 6 — Relatório final ao usuário

```
Imagens geradas no Pikaso.

- Arquivo: <caminho>
- Projeto Pikaso: <slug> (<nome UI>)
- Blocos processados: N × <variations> variações = <total> imagens
- Fired: <fired> / Skipped: <skip> / Errors: <err>
- Convergência: <ok|parcial|falhou>
- Duração: <duration_seconds>s
- Humanização: avg ~<avg_typing_cps> cps, ~<avg_pause_between_subs_s>s entre subs
- on_complete:
    - move_to: <destino ou "—">
    - indices atualizados: <lista ou "—">

Revise em br.freepik.com/pikaso (projeto <nome UI>).
```

## Tratamento de erros

| Sintoma (do JSON) | Status | Ação do Claude |
|---|---|---|
| `project` ausente e inferência por caminho falha | `needs_user_input` | Mostrar `prompt_for_user`, perguntar slug |
| Slug do `project` não existe no mapeamento | `needs_user_input` | Perguntar se deve adicionar ao mapeamento (editar SKILL.md + script) |
| Projeto não existe no Pikaso | `needs_user_input` | Mostrar `prompt_for_user` (criar/outro/cancelar) |
| Cap por sessão atingido | `cap_reached` | Mostrar `resume_suggested_at_iso` + sugerir `--only <remaining_labels>` |
| Cap por hora atingido | `cap_reached` | Idem |
| Captcha/bloqueio detectado | `blocked` | Reportar `block_evidence`. **Não retentar.** Cooldown 60min ativo. |
| `playwright` import error / Chrome ausente | `error` | Sugerir `pip install playwright; playwright install chrome` |
| 0 blocos JSON no arquivo | `error` | Pausar, avisar que não tem nada pra submeter |
| Loop terminou mas polling não convergiu em 15 min | `partial` | Reportar labels com `fired > done` e sugerir checar manualmente |

Detalhes de troubleshooting: `references/playwright-freepik.md` §"Troubleshooting".

## Princípios não-negociáveis

1. **Projeto Pikaso sempre confirmado antes de submeter.** Senão imagem vai pro projeto errado e bagunça a conta.
2. **Nunca criar projeto Pikaso silenciosamente.** Ação organizacional requer aprovação explícita.
3. **Humanização sempre ligada.** Não existe flag pra desligar. Velocidade-vs-segurança já foi decidido em favor de segurança.
4. **JSON compacto nos prompts.** `json.dumps(obj)` sem indent. Nano Banana não liga.
5. **on_complete só roda se `next_action == run_on_complete`.** Convergência parcial = arquivo fica onde está.
6. **Nunca baixa imagens.** Ficam no Pikaso pro user revisar.
7. **Defaults sensatos.** 9:16, 2K, 3 variações, nano-banana-2, normal. Só muda se o YAML pedir.
8. **Dry-run disponível** pra validação sem gastar fila/imagens.
9. **Mapeamento de projetos é editável**: se user criar projeto novo, atualize a tabela aqui E o dict no script.
10. **Caps são pisos de segurança, não tetos arbitrários.** Não relaxar por pressa.

## Quando carregar referências

- `references/playwright-freepik.md` → debug do runtime, ajustar seletores, entender JSON schema.
- `references/legacy/freepik-automation.md` → SÓ se o runtime Playwright estiver quebrado e for preciso fallback emergencial (raro). Não para "voltar a usar porque é mais rápido".
- `credentials.local.json` → o script lê; Claude não precisa ler em fluxo normal.

Pronto pra executar.

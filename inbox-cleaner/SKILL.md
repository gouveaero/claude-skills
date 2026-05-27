---
name: inbox-cleaner
description: Triagem das pastas to:financeiro@exosmkt.com e to:gabriel@exosmkt.com dentro de gvsg.gouvea@gmail.com via Gmail MCP. Classifica emails com subagentes Haiku em paralelo (Sonnet pra ambíguos), separa lixeira de notas fiscais/comunicação humana, e move ambíguos pra label "Triagem/Revisar". Use quando o usuário pedir pra limpar, triar, processar ou organizar emails das pastas Exos.
allowed-tools: Agent, ToolSearch, Bash, Read, Write, Edit, AskUserQuestion, TodoWrite, mcp__claude_ai_Gmail__authenticate, mcp__claude_ai_Gmail__complete_authentication
---

# Inbox Cleaner — Triagem multi-pasta via Gmail MCP

## Goal & escopo

Triar emails endereçados a **`financeiro@exosmkt.com`** e **`gabriel@exosmkt.com`** dentro da conta `gvsg.gouvea@gmail.com` (os emails caem nessa conta via "Check mail from other accounts" do Gmail).

**Escopo explícito:**
- ✅ Emails com `to:financeiro@exosmkt.com`
- ✅ Emails com `to:gabriel@exosmkt.com`
- ❌ NÃO mexer na inbox principal de `gvsg.gouvea@gmail.com`
- ❌ NÃO marcar nada como lido sem confirmação humana explícita

## Mapeamento por contexto

### Contexto A — `to:financeiro@exosmkt.com`

| Categoria | Ação | O que entra |
|---|---|---|
| `nota_fiscal` | **Guardar** (mark-as-read) | NFs eletrônicas, XMLs, NFS-e, recibos com CNPJ |
| `contabilidade` | **Guardar** (mark-as-read) | Comunicação humana com contador, DCTF, IRPJ, demonstrativos, pedidos de informação |
| `notificacao_venda` | **Lixeira** | Hotmart/Kiwify/Eduzz/Doppus/Cakto "Nova venda", "Comissão recebida", "Pagamento processado", "Reembolso", "Chargeback" — automatizado, alto volume |
| `ambiguo` | **Label `Triagem/Revisar`** | Qualquer dúvida — sobe pra revisão humana |

### Contexto B — `to:gabriel@exosmkt.com`

| Categoria | Ação | O que entra |
|---|---|---|
| `cliente_ativo` | **Guardar** | Comunicação humana de clientes Exos: Vhoe, Tribotax, Leticia Lang, Saif, Ecossustentavel, Projeto_EU, etc. |
| `parceiro_proposta` | **Guardar** | Propostas com referência específica a Gabriel/Exos, parcerias reais, threads ativas com humanos |
| `cold_outreach` | **Lixeira** | SDR spam, "I noticed your company...", outreach templated, "quick question?" frio |
| `marketing_saas` | **Lixeira** | Newsletters (mesmo as boas — Stratechery, Lenny's, etc), notifs SaaS (Linear, GitHub digests, n8n), marketing transacional |
| `ambiguo` | **Label `Triagem/Revisar`** | Qualquer dúvida |

**Princípio transversal:** errar pelo lado conservador. Confiança <80% em "lixeira" → vira `ambiguo`. Lixeira é destrutiva (recuperável só por 30 dias), label é reversível.

## Pipeline de 8 fases

### Fase 0 — Auth Gmail MCP (1x por sessão)

1. Tentar `ToolSearch` com query `+gmail message` (max 30) — se já vier `list_messages`/`get_message`/etc, **pular auth** (sessão já autenticada).
2. Se só aparecer `authenticate`/`complete_authentication`, chamar `mcp__claude_ai_Gmail__authenticate`. Mostrar a URL pro user e pedir que ele cole o callback URL da barra de endereço após autorizar.
3. Chamar `mcp__claude_ai_Gmail__complete_authentication` com o callback URL.
4. Após auth, rodar `ToolSearch` de novo pra descobrir os nomes reais das tools (varia entre versões do MCP).
5. **Verificar identidade**: chamar tool de profile (geralmente `get_profile` ou similar) e confirmar email = `gvsg.gouvea@gmail.com`. Se for outra conta, parar e avisar.
6. **Garantir label `Triagem/Revisar`**: usar tool `list_labels` (ou equivalente); se não existir, criar via `create_label` com nome `Triagem/Revisar`. Guardar o `labelId` retornado.

### Fase 1 — Fetch por contexto

Pra cada contexto (financeiro primeiro, gabriel depois):

```
query = "to:<endereço> is:unread"
limit = 50 (default; user pode override)
```

Usar a tool MCP equivalente (`list_messages` ou `search_messages`) com a query. Pra cada message ID retornado, chamar `get_message` (ou batch `get_messages` se existir) buscando pelo menos: `id`, `from`, `subject`, `snippet`, `date`, `internalDate`, headers `list-unsubscribe`, primeiros 1500 chars do body.

**Dedupe:** chave = `message-id` header (não o `id` interno do Gmail). Emails forwarded podem aparecer em ambos contextos.

### Fase 2 — Batching

- Dividir lista de emails em batches de **10**
- Cada batch vira input pra **1 subagente Haiku**

### Fase 3 — Triagem paralela (Haiku)

**Dispatchar TODOS os subagentes do contexto em UMA ÚNICA mensagem** com múltiplas chamadas Agent simultâneas. Isso ativa paralelismo real (não pode ser sequencial).

Cada agente é Agent tool com:
- `subagent_type`: `general-purpose`
- `model`: `haiku`
- `description`: `Triagem batch N pasta <contexto>`
- `prompt`: ver prompt em "Prompts dos subagentes" abaixo

### Fase 4 — Escalação Sonnet (ambíguos)

- Coletar todos retornos `ambiguo` ou `confianca < 0.8` dos Haiku
- Se zero ambíguos: pular esta fase
- Senão: 1 chamada Agent com `model=sonnet`, prompt similar mas reforçando rigor

### Fase 5 — Montar plano de ação

Consolidar resultados em estrutura:
```
PLANO PASTA <contexto>:
  → LIXEIRA (N emails):
    • <subject> — from <sender> — razão: <reason>
    ...
  → GUARDAR/mark-as-read (N emails):
    • <subject> — categoria: <categoria>
    ...
  → LABEL Triagem/Revisar (N emails):
    • <subject> — razão: <reason>
```

### Fase 6 — Confirmação humana

**OBRIGATÓRIO.** Mostrar plano completo ao user e perguntar:

> "Aplicar essas ações? [s/n/ajustar]"

Se `ajustar`: user diz quais IDs reclassificar manualmente, atualiza plano, pergunta de novo.

**NUNCA aplicar ações destrutivas (lixeira) sem essa confirmação.**

### Fase 7 — Aplicar ações

Mapeamento → tool MCP:

| Ação lógica | Tool MCP (nome confirmado em runtime) |
|---|---|
| Mark as read | `modify_message`: remove label `UNREAD` |
| Lixeira | `trash_message` (se exposta); senão `modify_message`: add `TRASH` + remove `INBOX` + remove `UNREAD` |
| Label Triagem | `modify_message`: add label `<labelId Triagem/Revisar>` + remove `UNREAD` |

Loop sequencial (50 emails ~30s). Reportar progresso pro user a cada 10 ações.

### Fase 8 — Resumo final

Após processar ambas as pastas, mostrar:
```
RESUMO:
• Financeiro: X lixeira, Y guardados, Z em revisão
• Gabriel:    A lixeira, B guardados, C em revisão
• Total: D ações aplicadas em ~E min, custo ~$F
• Label Triagem/Revisar tem N emails pra você revisar quando puder
```

## Schema JSON dos subagentes

Resposta esperada (parsing rígido):

```json
[
  {
    "id": "<gmail message id>",
    "categoria": "nota_fiscal|contabilidade|notificacao_venda|cliente_ativo|parceiro_proposta|cold_outreach|marketing_saas|ambiguo",
    "confianca": 0.0-1.0,
    "motivo": "<máx 80 chars: por que essa categoria>"
  },
  ...
]
```

## Prompts dos subagentes

### Prompt Haiku (contexto Financeiro)

```
Você é um classificador de emails da pasta `financeiro@exosmkt.com` do Gabriel Gouvea (cofundador da agência Exos, marketing digital pra infoprodutos).

Classifique cada email em UMA categoria:
- `nota_fiscal`: NFs eletrônicas, XMLs, NFS-e, recibos com CNPJ → AÇÃO: guardar
- `contabilidade`: comunicação humana com contador (Sage, Domínio, contadores), pedidos de info, demonstrativos, IRPJ, DCTF → AÇÃO: guardar
- `notificacao_venda`: notificações automáticas de plataformas (Hotmart, Kiwify, Eduzz, Doppus, Cakto, Monetizze) sobre "Nova venda", "Comissão", "Pagamento processado", "Chargeback", "Reembolso" → AÇÃO: lixeira
- `ambiguo`: qualquer dúvida → AÇÃO: revisão humana

Princípio: ERRE PELO LADO CONSERVADOR. Se confiança <80% em lixeira, marque `ambiguo`. Lixeira é destrutiva.

Retorne SÓ JSON válido no schema:
[{"id": "<id>", "categoria": "<cat>", "confianca": 0.0-1.0, "motivo": "<máx 80 chars>"}]

Sem markdown, sem prosa, só o JSON array.

EMAILS:
{batch_json}
```

### Prompt Haiku (contexto Gabriel)

```
Você é um classificador de emails da pasta `gabriel@exosmkt.com` do Gabriel Gouvea (cofundador Exos, agência de marketing pra infoprodutos; clientes ativos: Vhoe, Tribotax, Leticia Lang, Saif, Ecossustentavel, Projeto_EU).

Classifique cada email em UMA categoria:
- `cliente_ativo`: comunicação humana de clientes Exos (lista acima) → AÇÃO: guardar
- `parceiro_proposta`: propostas reais com referência específica a Gabriel/Exos, parcerias, threads ativas com humanos → AÇÃO: guardar
- `cold_outreach`: SDR spam, "I noticed your company", "quick question?", outreach templated → AÇÃO: lixeira
- `marketing_saas`: newsletters (mesmo úteis: Stratechery, Lenny's), notifs de SaaS (GitHub, Linear, n8n digests), marketing transacional → AÇÃO: lixeira
- `ambiguo`: qualquer dúvida → AÇÃO: revisão humana

Princípio: ERRE PELO LADO CONSERVADOR. Se confiança <80% em lixeira, marque `ambiguo`. Threads existentes com humanos = sempre `cliente_ativo` ou `parceiro_proposta`.

Retorne SÓ JSON válido no schema:
[{"id": "<id>", "categoria": "<cat>", "confianca": 0.0-1.0, "motivo": "<máx 80 chars>"}]

Sem markdown, sem prosa, só o JSON array.

EMAILS:
{batch_json}
```

### Prompt Sonnet (escalação ambíguos)

```
Você é classificador de emails sênior. Os emails abaixo foram marcados como AMBÍGUOS por classificadores Haiku — você precisa decidir com mais cuidado.

Contexto: Gabriel Gouvea, cofundador Exos (agência marketing pra infoprodutos). Esta pasta é `<contexto>` (financeiro ou gabriel).

Categorias permitidas pra `<contexto>`:
<lista de categorias do contexto>

Regras:
1. Lixeira só se >90% confiante (não 80%). Você é a última chance.
2. Se ainda assim ambíguo, mantenha `ambiguo` → vai pra label de revisão humana, é seguro.
3. Threads com humanos respondendo = nunca lixeira.

Retorne SÓ JSON:
[{"id": "<id>", "categoria": "<cat>", "confianca": 0.0-1.0, "motivo": "<máx 100 chars>"}]

EMAILS AMBÍGUOS:
{batch_json}
```

## Edge cases

| Caso | Tratamento |
|---|---|
| Pasta sem unread | Pular contexto silenciosamente, reportar no resumo final |
| Label `Triagem/Revisar` já existe | Reusar `labelId` existente, não criar duplicata |
| MCP não expõe `create_label` | Pedir ao user pra criar manualmente uma vez via Gmail web; pausar execução |
| MCP não expõe `trash_message` separado | Usar `modify_message` adicionando label `TRASH` |
| MCP rate limit (429) | Backoff exponencial: esperar 5s, 15s, 45s; após 3 tentativas avisar user |
| Email duplicado (forwarding cruzado) | Dedupe por `Message-ID` header antes de classificar |
| User responde "ajustar" na Fase 6 | Pegar lista de IDs + nova categoria, atualizar plano, perguntar de novo |
| Subagente retorna JSON inválido | Re-prompt 1x com "Resposta anterior não foi JSON válido. Retorne SÓ o array."; se falhar de novo → marcar todos `ambiguo` |
| Volume > 50 em um contexto | Avisar user e perguntar: aumentar limit? processar em rounds? Default: processar 50 e avisar quantos sobraram |

## Como rodar recorrente (referência futura)

Execução manual é o default. Pra automatizar semanalmente:
- `/schedule` com cron `0 9 * * MON` → "limpa as pastas Exos"
- Ou `/loop 7d /limpa-exos`

Antes de automatizar, rodar manual 2-3 vezes pra validar que a classificação tá no ponto.

## Custo e performance esperados

| Volume | Tempo | Custo (USD) |
|---|---|---|
| 50 emails | ~2 min | ~$0.02 |
| 100 emails (ambos contextos) | ~3 min | ~$0.04 |
| 200 emails (acúmulo) | ~6 min | ~$0.08 |

Custo é dominado pelos subagentes Haiku (5 por contexto × ~$0.003) + 1 Sonnet de escalação (~$0.01) + tools MCP (sem cost extra).

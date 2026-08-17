# Naming Conventions — Meta Ads Operator (Exos)

## Formato Padrão

```
[CLIENTE][PROJETO][ASSET][ANO][FASE][GEO][PÚBLICO][VARIANTE]
```

Cada componente entre colchetes, sem espaços, sem caracteres especiais fora dos colchetes.

**Regex de validação:**
```
^\[[A-Z]{2,3}\](\[[A-Z0-9]{2,10}\]){5,7}$
```

Toda criação DEVE passar nesse regex antes de ser submetida à API.

---

## Componentes

### `[CLIENTE]` — 2–3 letras, maiúsculas

| Cliente | Código |
|---------|--------|
| Letícia Lang | `LL` |
| Dr. Kleber Meireles | `KL` |
| Lívia Tolentino | `LT` |
| Elen Tolentino | `ET` |
| Jesse (cliente) | `JS` |
| *(novo cliente)* | Usar iniciais únicas 2–3 letras |

---

### `[PROJETO]` — código do projeto/lançamento

| Tipo | Código | Exemplo |
|------|--------|---------|
| Lançamento | `LANC` + ano | `LANC26` |
| Workshop/Evento | `WK` + data | `WK16MAI26` |
| Ebook/Lead magnet | `PEP` (perpétuo) ou `EBOOK` | `PEP`, `EBOOK` |
| Perpétuo genérico | `PERP` | `PERP` |
| Info produto específico | Abreviação do produto | `INTERNO`, `DTP`, `SEMENTE` |
| Evento online | `EVENTO` | `EVENTO` |

---

### `[ASSET]` — tipo de oferta

| Oferta | Código |
|--------|--------|
| Ebook/lead magnet | `EBOOK` |
| Workshop ao vivo | `WORKSHOP` |
| Infoproduto/curso | `INFO` |
| VSL (Video Sales Letter) | `VSL` |
| Webinar | `WEBIN` |
| Consultoria/serviço | `SERV` |
| Produto físico | `PROD` |

---

### `[ANO]` — 2 dígitos

`26` para 2026, `27` para 2027, etc.

---

### `[FASE]` — estágio do funil

⚠️ **Estes são os marcadores que o Dashboard Exos LÊ do nome** (12/08/2026 — a tabela
antiga `CAPT`/`AQUEC`/`RETAR`/`RECOV` divergia da produção e o dash não a reconhecia).
Referência viva: https://dash.exosmkt.com/convencoes

| Fase | Marcador aceito | Objetivo Meta típico |
|------|-----------------|---------------------|
| Captação/topo | `CADASTROS` / `CADASTRO` / `CAPTACAO` / `CAP` | OUTCOME_LEADS, OUTCOME_TRAFFIC |
| Contagem regressiva | frase `CONTAGEM REGRESSIVA` no texto livre | OUTCOME_AWARENESS |
| Venda/carrinho | `VENDAS` / `VENDA` / `VENDAS DO EVENTO` / `OFERTA` | OUTCOME_SALES |
| Carrinho aberto | `CARRINHO` ou a frase "carrinho aberto" | OUTCOME_SALES |
| Evento ao vivo | `EVENTO` / `AULA` / `AO VIVO` | OUTCOME_AWARENESS |
| Pesquisa pós-evento | `PESQUISA` | OUTCOME_ENGAGEMENT |
| Downsell | `DOWNSELL` | OUTCOME_SALES |
| Recuperação | `RECUPERACAO` / `REABERTURA` | OUTCOME_SALES |

Regras do leitor: um marcador por campanha (dois de fases diferentes anulam);
`[RECONHECIMENTO]` sozinho NÃO é fase; posição = antes do código do cliente ou
depois do ano, nunca entre os dois (quebra a identidade do projeto). O `[PGL]`
prefixo e texto livre após a tag são aceitos — o regex estrito abaixo é o ideal
de criação, não o que o parser exige.

---

### `[GEO]` — segmentação geográfica

| Segmentação | Código |
|-------------|--------|
| Brasil inteiro | `BR` |
| São Paulo (estado) | `SP` |
| RJ+SP+MG | `SUDESTE` |
| Capitais | `CAPS` |
| Sul+Sudeste | `SULSUD` |

---

### `[PÚBLICO]` — tipo de audiência

| Audiência | Código |
|-----------|--------|
| Frio — interesses | `INT` |
| Frio — comportamentos | `BEH` |
| Lookalike 1% | `LAL1` |
| Lookalike 1–3% | `LAL3` |
| Lookalike 5–10% | `LAL10` |
| Morno | `WARM` |
| Quente | `HOT` |
| Retarget LP | `RETLP` |
| Retarget abandono checkout | `RETCK` |
| Lista de leads | `LISTA` |
| Engajadores IG | `ENIG` |
| Compradores excluídos | `EXCCOMP` (em exclusions) |
| Adset único (sem variante) | `AS01`, `AS02` |

---

### `[VARIANTE]` — versão do criativo ou adset

| | Código |
|--|--------|
| Versão 1 | `V1` |
| Versão 2 | `V2` |
| Teste A | `VA` |
| Teste B | `VB` |
| Adset 01 | `AS01` |
| Adset 02 | `AS02` |

---

## Hierarquia por Nível

Campaigns, adsets e ads usam o mesmo formato. Ads adicionam sufixo `-AD` ao final para diferenciar.

| Nível | Nome | Exemplo |
|-------|------|---------|
| Campaign | `[C][P][A][Y][F][G][AU][V]` | `[KL][PERP][INFO][26][CAPT][BR][LAL1][V1]` |
| Ad Set | `[C][P][A][Y][F][G][AU][V]` | igual à campaign (1:1 quando adset representa a segmentação) |
| Ad | `[C][P][A][Y][F][G][AU][V]-AD` | `[KL][PERP][INFO][26][CAPT][BR][LAL1][V1]-AD` |

Para múltiplos adsets na mesma campanha, incrementar `[PÚBLICO]` ou `[VARIANTE]`:
```
[KL][PERP][INFO][26][CAPT][BR][LAL1][V1]   ← adset 1
[KL][PERP][INFO][26][CAPT][BR][INT][V1]    ← adset 2
[KL][PERP][INFO][26][CAPT][BR][LAL3][V1]   ← adset 3
```

---

## 10 Exemplos Reais

### Letícia Lang — Workshop ONCO+ (16–17 mai 2026)

```
Campaign: [LL][WK16MAI26][EVENTO][26][CAPT][BR][LAL1][V1]
Adset 1:  [LL][WK16MAI26][EVENTO][26][CAPT][BR][LAL1][V1]
Adset 2:  [LL][WK16MAI26][EVENTO][26][CAPT][BR][INT][V1]
Ad:       [LL][WK16MAI26][EVENTO][26][CAPT][BR][LAL1][V1]-AD

Retarget: [LL][WK16MAI26][EVENTO][26][RETAR][BR][RETLP][V1]
```

### Kleber — Lançamento Semente 2026

```
Campaign captação: [KL][SEMENTE][INFO][26][CAPT][BR][LAL1][V1]
Campaign aquecimento: [KL][SEMENTE][INFO][26][AQUEC][BR][WARM][V1]
Campaign venda: [KL][SEMENTE][INFO][26][VENDA][BR][HOT][V1]
Recovery: [KL][SEMENTE][INFO][26][RECOV][BR][RETCK][V1]
```

### Kleber — Funil Perpétuo

```
Topo CBO: [KL][PERP][INFO][26][CAPT][BR][LAL3][V1]
Meio ABO: [KL][PERP][INFO][26][AQUEC][BR][WARM][V1]
Fundo CBO: [KL][PERP][INFO][26][VENDA][BR][HOT][V1]
```

### Lívia — Ebook PEP

```
Campaign: [LT][PEP][EBOOK][26][CAPT][BR][INT][V1]
Adset 1:  [LT][PEP][EBOOK][26][CAPT][BR][INT][V1]     ← interesses odonto
Adset 2:  [LT][PEP][EBOOK][26][CAPT][BR][LAL1][V1]    ← LAL compradores pós
Ad:       [LT][PEP][EBOOK][26][CAPT][BR][INT][V1]-AD
```

---

## Validação de Nomes

Antes de submeter qualquer nome à API, validar:

```bash
echo "[LT][PEP][EBOOK][26][CAPT][BR][INT][V1]" | \
  grep -Pq '^\[[A-Z]{2,3}\](\[[A-Z0-9]{2,10}\]){5,7}$' && echo "OK" || echo "INVALID"
```

**Erros comuns:**
- Usar minúsculas → tudo maiúsculas
- Espaços dentro dos colchetes → não permitido
- Código de cliente com 1 letra → mínimo 2
- Não fechar colchete → `[LT[PEP]` → inválido
- Componente com mais de 10 caracteres → reduzir abreviação

# Tool Reference — Meta Ads MCP Oficial

MCP endpoint: `https://mcp.facebook.com/ads`  
Auth: Meta Business OAuth (read+write tier)  
All tools prefixed `ads_` in the official MCP.

---

## Discovery

### `ads_get_ad_accounts`
Lista contas de anúncio acessíveis no token atual.

```json
ads_get_ad_accounts({})
```
Returns: list of `{id, name, account_status, currency, timezone_name}`.

**Gotcha:** retorna TODAS as contas no BM. Filtrar pelo nome do cliente para confirmar `act_id` correto.

---

### `ads_get_ad_entities`
Lista entidades (campaigns, adsets, ads) de uma conta.

```json
ads_get_ad_entities({
  "account_id": "act_XXXXXXXXX",
  "entity_type": "campaign",
  "status_filter": "ACTIVE"
})
```
`entity_type`: `"campaign"` | `"adset"` | `"ad"`  
`status_filter`: `"ACTIVE"` | `"PAUSED"` | `"ALL"` (default)

---

### `ads_get_pages_for_business`
Lista Pages conectadas ao Business Manager.

```json
ads_get_pages_for_business({
  "business_id": "XXXXXXXXX"
})
```
Returns: `{id, name, category}` — usar `id` como `page_id` em criativos.

---

## Campaign Management (Create/Update/Activate)

### `ads_create_campaign`

```json
ads_create_campaign({
  "account_id": "act_XXXXXXXXX",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][INT][V1]",
  "objective": "OUTCOME_LEADS",
  "status": "PAUSED",
  "special_ad_categories": [],
  "buying_type": "AUCTION",
  "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
  "daily_budget": 5000
})
```

**Campos obrigatórios:** `account_id`, `name`, `objective`, `status`  
**Budget:** `daily_budget` OU `lifetime_budget`, em centavos (5000 = R$50,00)  
**Bid strategies válidas:** `LOWEST_COST_WITHOUT_CAP`, `LOWEST_COST_WITH_BID_CAP`, `COST_CAP`, `LOWEST_COST_WITH_MIN_ROAS`  
**Gotcha CRÍTICO:** usar objetivos ODAX, nunca legacy. `LEAD_GENERATION` → 400 error.

---

### `ads_create_ad_set`

```json
ads_create_ad_set({
  "account_id": "act_XXXXXXXXX",
  "campaign_id": "<campaign_id>",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][INT][V1]",
  "status": "PAUSED",
  "optimization_goal": "LEAD_GENERATION",
  "billing_event": "IMPRESSIONS",
  "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
  "daily_budget": "5000",
  "targeting": {
    "age_min": 25,
    "age_max": 65,
    "geo_locations": {"countries": ["BR"]},
    "interests": [
      {"id": "6003107902433", "name": "Dentistry"}
    ]
  },
  "start_time": "2026-05-10T00:00:00-0300",
  "end_time": "2026-06-10T00:00:00-0300"
})
```

**Gotcha:** `daily_budget` aqui é string (diferente de campaign que é int).  
**`optimization_goal`** válidos por objective:

| Objective | optimization_goal |
|-----------|------------------|
| OUTCOME_LEADS | `LEAD_GENERATION`, `LANDING_PAGE_VIEWS`, `LINK_CLICKS` |
| OUTCOME_SALES | `OFFSITE_CONVERSIONS`, `VALUE`, `LINK_CLICKS` |
| OUTCOME_TRAFFIC | `LINK_CLICKS`, `LANDING_PAGE_VIEWS` |
| OUTCOME_ENGAGEMENT | `POST_ENGAGEMENT`, `VIDEO_VIEWS`, `THRUPLAY` |

---

### `ads_create_ad`

```json
ads_create_ad({
  "account_id": "act_XXXXXXXXX",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][INT][V1]-AD",
  "adset_id": "<adset_id>",
  "status": "PAUSED",
  "creative": {
    "object_story_spec": {
      "page_id": "<page_id>",
      "link_data": {
        "image_url": "https://example.com/image.jpg",
        "link": "https://site.com.br/ebook",
        "message": "Texto do anúncio...",
        "name": "Título do anúncio",
        "call_to_action": {
          "type": "DOWNLOAD",
          "value": {"link": "https://site.com.br/ebook"}
        }
      }
    }
  }
})
```

**CTAs válidos:** `LEARN_MORE`, `DOWNLOAD`, `SIGN_UP`, `SUBSCRIBE`, `CONTACT_US`, `SHOP_NOW`, `BOOK_TRAVEL`, `WATCH_MORE`

---

### `ads_update_entity`
Atualiza qualquer campo de campaign/adset/ad.

```json
ads_update_entity({
  "entity_id": "<campaign_id>",
  "entity_type": "campaign",
  "fields": {
    "daily_budget": 6000,
    "status": "PAUSED"
  }
})
```

**Gotcha:** não usar para mudar `objective` (impossível em campanha existente) nem `optimization_goal` em adset ativo (mata learning phase).

---

### `ads_activate_entity`
Ativa uma entidade (muda status para ACTIVE).

```json
ads_activate_entity({
  "entity_id": "<campaign_id>",
  "entity_type": "campaign"
})
```

**REGRA:** só chamar após confirmação humana explícita. Ver safety-rules.md.

---

## Insights

### `ads_insights_performance_trend`
Série temporal de métricas de performance.

```json
ads_insights_performance_trend({
  "object_id": "<campaign_id or account_id>",
  "time_range": "last_7d",
  "breakdown": ["placement", "age"],
  "level": "adset"
})
```

`time_range`: `"last_7d"`, `"last_14d"`, `"last_30d"`, `"last_90d"`, `"this_month"`, `"last_month"`  
`level`: `"ad"`, `"adset"`, `"campaign"`, `"account"`

Key metrics returned: `spend`, `impressions`, `reach`, `frequency`, `ctr`, `cpc`, `cpm`, `actions`, `cost_per_action_type`

---

### `ads_insights_anomaly_signal`
Detecta anomalias (quedas/picos inesperados).

```json
ads_insights_anomaly_signal({
  "object_id": "<campaign_id>",
  "time_range": "last_7d"
})
```

Útil para: identificar quando CTR caiu de repente, quando gasto dobrou sem motivo.

---

### `ads_insights_auction_ranking_benchmarks`
Compara rankings da leilão vs. anúncios concorrentes.

```json
ads_insights_auction_ranking_benchmarks({
  "object_id": "<adset_id>",
  "time_range": "last_7d"
})
```

Returns: `quality_ranking`, `engagement_rate_ranking`, `conversion_rate_ranking`  
Values: `"ABOVE_AVERAGE"`, `"AVERAGE"`, `"BELOW_AVERAGE_10"`, `"BELOW_AVERAGE_20"`, `"BELOW_AVERAGE_35"`

---

### `ads_insights_industry_benchmark`

```json
ads_insights_industry_benchmark({
  "industry": "EDUCATION",
  "metric": "cpl",
  "country": "BR"
})
```

`industry`: `"EDUCATION"`, `"HEALTH"`, `"ECOMMERCE"`, `"FINANCE"`, `"REAL_ESTATE"`

---

### `ads_insights_performance_trend` — Advertiser Context

```json
ads_insights_advertiser_context({
  "account_id": "act_XXXXXXXXX"
})
```

Visão geral da conta: performance nos últimos 30 dias, campanhas principais, tendência de gasto.

---

### `ads_get_opportunity_score`
Score de oportunidades de otimização sugeridas pela Meta.

```json
ads_get_opportunity_score({
  "account_id": "act_XXXXXXXXX"
})
```

Use como checklist de melhorias. Não aplique automaticamente — revisar cada sugestão.

---

## Datasets (Pixel/CAPI)

### `ads_get_dataset_quality`

```json
ads_get_dataset_quality({
  "dataset_id": "<pixel_id>"
})
```

Returns: `event_match_quality` (score 0–10), `event_volume` (eventos/semana), `active_event_types`

**Regra pré-flight:** `event_match_quality >= 6` antes de subir campanha de conversão.

---

### `ads_get_dataset_stats`

```json
ads_get_dataset_stats({
  "dataset_id": "<pixel_id>",
  "time_range": "last_7d"
})
```

Mostra volumes por event type. Confirmar que o evento otimizado (`Lead`, `Purchase`) está ativo.

---

### `ads_get_dataset_details`

```json
ads_get_dataset_details({
  "dataset_id": "<pixel_id>"
})
```

Metadados do pixel: nome, data criação, status, owner.

---

### `ads_get_errors`

```json
ads_get_errors({
  "business_id": "<business_id>"
})
```

Erros de política, billing, conta restrita. Verificar antes de qualquer criação.

---

## Catalog (Uso raro para Exos — sem e-commerce)

`ads_catalog_*` — 10 tools para gerenciar catálogos de produtos. Raramente necessário no portfólio Exos (todos infoprodutos). Documentadas mas não detalhadas aqui. Consultar Meta API docs se necessário.

---

## Budget Schedules

### `ads_create_budget_schedule`
Programa aumento temporário de budget (ex: pico de carrinho aberto).

```json
ads_create_budget_schedule({
  "campaign_id": "<campaign_id>",
  "budget_value": 20000,
  "budget_value_type": "ABSOLUTE",
  "time_start": 1746316800,
  "time_end": 1746403200
})
```

`budget_value` em centavos. `time_start`/`time_end` em Unix timestamp.  
`budget_value_type`: `"ABSOLUTE"` (valor fixo) ou `"MULTIPLIER"` (ex: 1.5 = 50% a mais)

Útil para: aumentar budget no pico do carrinho (18h–23h) sem alterar o budget base permanentemente.

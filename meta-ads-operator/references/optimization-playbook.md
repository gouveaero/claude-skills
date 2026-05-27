# Optimization Playbook

## Part 1 — Diagnose

Never propose changes before completing diagnosis. Data first, action second.

### Step 1: Pull Performance Data

```json
ads_insights_performance_trend({
  "object_id": "<campaign_id or account_id>",
  "time_range": "last_7d",
  "breakdown": ["age", "placement", "device_platform"],
  "level": "adset"
})
```

Pull both `last_7d` and `last_30d`. Key metrics to extract:
- `spend`, `impressions`, `reach`, `frequency`
- `ctr` (click-through rate), `cpc` (cost per click)
- `cpm` (cost per 1000 impressions)
- `actions` (leads, purchases, etc.), `cost_per_action_type`
- `video_p50_watched_actions`, `video_p75_watched_actions` (for video ads)

### Step 2: Anomaly Detection

```json
ads_insights_anomaly_signal({
  "object_id": "<campaign_id>",
  "time_range": "last_7d"
})
```

Flags: unusual spends, sudden CTR drops, delivery issues.

### Step 3: Auction Ranking Benchmarks

```json
ads_insights_auction_ranking_benchmarks({
  "object_id": "<adset_id>",
  "time_range": "last_7d"
})
```

Returns three key rankings vs. competitor ads targeting the same audience:
- **Quality Ranking:** perceived quality of the ad vs. expected ad (above average / average / below average)
- **Engagement Rate Ranking:** expected engagement vs. competitor ads
- **Conversion Rate Ranking:** expected conversion vs. ads with same objective

**What the rankings mean:**
| Ranking | Implication |
|---------|-------------|
| Above average, above average, above average | Creative and landing page are good. Problem is likely audience saturation or budget. |
| Below average quality, X, X | Creative problem. The ad feels low quality. Swap creative. |
| X, below average engagement, X | Copy problem. Headlines/hooks not compelling. Test new angles. |
| X, X, below average conversion | LP problem or wrong optimization event. Check pixel, LP load time, CTA. |

### Step 4: Industry Benchmark

```json
ads_insights_industry_benchmark({
  "industry": "EDUCATION",
  "metric": "cpl",
  "country": "BR"
})
```

Use to compare client's CPL/CPA against industry average. Adjusts expectations.

---

## Diagnosis Decision Tree

**Symptom: CPL alto (acima da meta)**

```
CPL alto?
├── Frequency > 3.0? → Audience exhaustion. Rotate creative or expand audience.
├── Quality ranking "below average"? → Creative problem. New visual/hook.
├── Engagement ranking "below average"? → Copy problem. New headline/body.
├── Conversion ranking "below average"? → LP or pixel problem. Check landing page and pixel events.
├── CTR < 0.8%? → Creative not stopping the scroll. New format (video vs. image).
└── All rankings "average"? → Budget too low for learning phase. Increase or consolidate adsets.
```

**Symptom: ROAS baixo (abaixo da meta)**

```
ROAS baixo?
├── Learning phase ativo? (<50 conv/week) → Wait. Don't touch for 3–7 days.
├── Wrong optimization event? (ex: Link Click em vez de Purchase) → Rebuild adset with correct event.
├── Audience mismatch? → Check age/gender/device breakdown. Exclude ages that spend but don't convert.
├── LP conversion rate baixo? → Check with analytics. If LP converts <2%, problem is post-click, not ads.
└── Creative mismatch with offer? → Video fala de benefício X, LP vende produto Y. Align.
```

**Symptom: Frequência alta (>4 em 30 dias)**

```
Audience saturated?
├── Increase audience size (LAL 1% → LAL 1-3% or expand geo)
├── Rotate creative (new visual, new hook, same copy)
├── Exclude recent converters (30-day buyer list)
└── Pause adset and launch sibling with fresh audience
```

**Symptom: CTR baixo (<0.8%)**

```
CTR low?
├── Image/video not eye-catching? → Test 3 new visuals
├── Headline not compelling? → Test curiosity hook, problem hook, social proof hook
├── Wrong placement? → Check if Audience Network or Marketplace is diluting. Exclude low-CTR placements.
└── Wrong audience match? → Audience knows your brand well (warm) may not respond to cold awareness creative.
```

---

## Diagnosis Output Format

Always present as a table:

```
📊 DIAGNÓSTICO DE CAMPANHA — [Campaign Name]

Período: últimos 7 dias | Conta: act_XXXXXXXXX

| Adset | Impressões | Freq | CTR | CPL | Quality Rank | Engagement Rank | Conv Rank | Diagnóstico |
|-------|-----------|------|-----|-----|--------------|-----------------|-----------|-------------|
| INT-ODONTO | 45.230 | 2.1 | 1.2% | R$18 | Average | Average | Below avg | ⚠️ LP/pixel problem |
| LAL1-COMP | 12.400 | 1.3 | 1.8% | R$11 | Above avg | Above avg | Above avg | ✅ Saudável |

Anomalia detectada: CTR de INT-ODONTO caiu 40% nos últimos 3 dias.
Benchmark indústria: CPL médio Brasil Educação = R$22 (client está 18% abaixo = bom sinal).
```

---

## Part 2 — Optimize

### Rule: One Change at a Time

Never change multiple variables in the same week. If you change the creative and the audience simultaneously, you won't know which change caused the result.

### Timing Rules

| Situation | Action |
|-----------|--------|
| Campaign < 72 hours live | Do nothing. Not enough data. |
| Learning phase active (<50 conv/week) | Do not touch budget or targeting. Only swap creative if CTR < 0.5% after 5 days. |
| Campaign running 7+ days, stable data | Safe to make one optimization change. |
| Budget change needed | Max +20% or -20% at a time. |

### When to Duplicate vs Edit In-Place

**Edit in-place when:**
- Budget adjustment (small, ≤20%)
- Status change (pause/unpause)
- Bid strategy adjustment

**Duplicate adset when:**
- Testing new creative (keep original running, duplicate = new creative test)
- Testing new audience (keep original, duplicate = new audience)
- Creative is "below average" — create sibling adset with fresh creative, let Meta decide

**Kill and rebuild when:**
- Wrong optimization event from the start (can't change pixel event on live adset)
- Campaign objective needs to change (requires new campaign)
- Naming convention violation that confuses reporting

### When to Change Bid Strategy

| Current situation | Change to |
|-------------------|-----------|
| LOWEST_COST_WITHOUT_CAP, CPL unstable | COST_CAP at 1.5× average CPL |
| COST_CAP, delivery very low (<50% budget spent) | Lower the cap or switch to LOWEST_COST_WITHOUT_CAP |
| Want to scale while protecting ROAS | LOWEST_COST_WITH_MIN_ROAS |

### Optimization Proposal Format

Always present before applying:

```
🔧 PROPOSTA DE OTIMIZAÇÃO

Campanha: [LT][PEP][EBOOK][26][CAPT][BR][INT-ODONTO][V1]

Problema identificado: Conversion Rate Ranking "below average" + LP bounce rate estimado alto.
Hipótese: A landing page não está convertendo os cliques em leads.

Ação proposta: Substituir a LP atual por versão mais curta com formulário above-the-fold.
  (Isso é uma mudança de landing page, não nas campanhas. Sem editar adsets.)

Ação secundária (se LP ok): Criar novo adset [V2] duplicando INT-ODONTO com novo creative
  focando em prova social (depoimento em vídeo de 30s) em vez do VSL atual.

NENHUMA mudança será feita antes da sua confirmação.

➡️ Confirma as mudanças propostas? (sim/não/explique mais)
```

### Budget Change Execution

```json
ads_update_entity({
  "entity_id": "<campaign_id>",
  "entity_type": "campaign",
  "fields": {
    "daily_budget": 6000
  }
})
```

Note: `daily_budget` in cents. 6000 = R$60.

### Killing a Poorly-Performing Adset

```json
ads_update_entity({
  "entity_id": "<adset_id>",
  "entity_type": "adset",
  "fields": {
    "status": "PAUSED"
  }
})
```

Do not delete — keep PAUSED for historical data and re-activation potential.

---

## Hard-No Rules

These optimization actions are FORBIDDEN without explicit written user approval:

1. Pause a campaign in learning phase based on <72h of data.
2. Increase budget by >20% in a single edit.
3. Change the campaign objective (requires rebuilding the whole campaign).
4. Edit the pixel conversion event on a live adset (kills learning phase, requires new adset).
5. Deactivate all campaigns simultaneously (lose all audience data).
6. Set bid_amount below the minimum required by Meta for the optimization goal.

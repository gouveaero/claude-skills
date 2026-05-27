# Launch Workflow — 9-Step Campaign Creation

Follow these steps in order, every time. Never skip a step.

---

## Step 1: Load Client Config

Look for `.meta-ads.json` starting from current directory, going up to `../../`. Extract:
- `act_id` — format `act_XXXXXXXXX`
- `page_id` — Facebook Page ID
- `instagram_actor_id` — Instagram account ID (if different from page)
- `pixel_id` — Meta Pixel / Dataset ID
- `client_code` — 2-3 letter code (e.g., `LT`, `KL`, `LL`)
- `naming_convention` — the client's naming template

If `.meta-ads.json` not found: ask user for `act_id` and client name. Offer onboarding (`assets/bm-onboarding-checklist.md`).

---

## Step 2: Campaign Brief

Use the template in `assets/campaign-brief.template.md`. Fill with the user:

- Business objective (what happens after the user converts?)
- Primary KPI and target (CPL < R$20? CPA < R$500? ROAS > 3×?)
- Total budget (daily or lifetime) and campaign duration
- Target audience (who, demographics, Brazil state or nationwide)
- Offer description (what are we selling/giving?)
- Creatives available (URLs of images/videos, or local file paths)
- Landing page or lead form URL
- Pixel event to optimize (Lead, Purchase, ViewContent, etc.)

---

## Step 3: Translate Brief → Campaign Structure

Map the brief to the correct ODAX objective:

| Goal | ODAX |
|------|------|
| Awareness | OUTCOME_AWARENESS |
| Traffic | OUTCOME_TRAFFIC |
| Engagement | OUTCOME_ENGAGEMENT |
| Lead gen | OUTCOME_LEADS |
| Sales/conversions | OUTCOME_SALES |
| App installs | OUTCOME_APP_PROMOTION |

Decide structure:
- **CBO** (Campaign Budget Optimization): best when you want Meta to decide where to spend. Use for cold audiences.
- **ABO** (Adset Budget Optimization): use when you need to guarantee minimum spend per audience. Use for warm/hot retarget.

Name campaign following naming convention. Example:
```
[LT][PEP][EBOOK][26][CAPT][BR][COLD][V1]
```

---

## Step 4: Targeting Research

The official Meta MCP does NOT have interest/behavior search tools. Use one of:
- **Option A (Preferred):** Use Meta Ads Manager > Ad Set > Audiences panel to look up interest IDs, then provide them.
- **Option B:** Use Pipeboard MCP if configured (`mcp_meta_ads_search_interests`, `mcp_meta_ads_search_behaviors`).
- **Option C:** Use hardcoded interests from `references/targeting-cookbook.md` for known niches (odonto, eventos, saúde).

For LAL (Lookalike Audiences): confirm with user which custom audience to use as seed (compradores, leads, top engagers). Note: creating/managing custom audiences directly via MCP is limited — do it in Ads Manager.

---

## Step 5: Pre-flight Checks

**ALWAYS run before any conversion campaign:**

```
ads_get_dataset_quality({
  "dataset_id": "<pixel_id from .meta-ads.json>"
})
```
Look for: `event_match_quality`, `event_volume`, `active_event_types`. If pixel shows no recent events or match quality < 6, alert user and pause launch.

```
ads_get_errors({
  "business_id": "<business_id>"
})
```
Look for: billing errors, policy violations, restricted business categories. Fix before proceeding.

---

## Step 6: Create in Order (All PAUSED)

### 6a. Create Campaign

```json
ads_create_campaign({
  "account_id": "act_XXXXXXXXX",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][COLD][V1]",
  "objective": "OUTCOME_LEADS",
  "status": "PAUSED",
  "special_ad_categories": [],
  "buying_type": "AUCTION",
  "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
  "daily_budget": 5000
})
```

Note: `daily_budget` is in cents (5000 = R$50,00). Alternatively use `lifetime_budget` for fixed-end campaigns.

Save returned `campaign_id`.

### 6b. Create Ad Set(s)

```json
ads_create_ad_set({
  "account_id": "act_XXXXXXXXX",
  "campaign_id": "<campaign_id>",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][INT-ODONTO][V1]",
  "status": "PAUSED",
  "optimization_goal": "LEAD_GENERATION",
  "billing_event": "IMPRESSIONS",
  "targeting": {
    "age_min": 25,
    "age_max": 65,
    "geo_locations": {
      "countries": ["BR"]
    },
    "interests": [
      {"id": "6003107902433", "name": "Dentistry"},
      {"id": "6003349442459", "name": "Orthodontics"}
    ]
  },
  "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
  "start_time": "2026-05-10T00:00:00-0300",
  "end_time": "2026-06-10T00:00:00-0300"
})
```

Save returned `adset_id`. Repeat for each adset.

### 6c. Upload Creative (if local file)

If the user provides a local file path (not URL), use CLI:

```bash
/Users/gabriel/Library/Python/3.9/bin/meta-ads create \
  --account act_XXXXXXXXX \
  --config campaign_config.yaml
```

Or for direct image upload (unofficial CLI may support):
```bash
meta-ads upload-image --account act_XXXXXXXXX --file /path/to/image.jpg
```

For public URLs, go directly to step 6d.

### 6d. Create Ad Creative (using URL)

```json
ads_create_ad({
  "account_id": "act_XXXXXXXXX",
  "name": "[LT][PEP][EBOOK][26][CAPT][BR][INT-ODONTO][V1]-AD",
  "adset_id": "<adset_id>",
  "status": "PAUSED",
  "creative": {
    "object_story_spec": {
      "page_id": "<page_id>",
      "link_data": {
        "image_url": "https://example.com/creative.jpg",
        "link": "https://leticialang.com.br/ebook",
        "message": "Descubra como tratar pacientes oncológicos na odontologia...",
        "name": "Baixe o guia completo de Odonto-Oncologia",
        "call_to_action": {
          "type": "DOWNLOAD",
          "value": {"link": "https://leticialang.com.br/ebook"}
        }
      }
    }
  }
})
```

---

## Step 7: Human-Readable Summary

Present BEFORE activating:

```
📋 RESUMO DA CAMPANHA — AGUARDANDO CONFIRMAÇÃO

Cliente: Letícia Lang | Conta: act_XXXXXXXXX
Campanha: [LT][PEP][EBOOK][26][CAPT][BR][COLD][V1]
Objetivo: OUTCOME_LEADS
Status: PAUSED

Conjuntos de anúncios (2):
  1. [LT][PEP][EBOOK][26][CAPT][BR][INT-ODONTO][V1]
     Público: Interesses Odontologia/Ortodontia | BR | 25-65
     Tamanho estimado: 2,1M–3,8M pessoas

  2. [LT][PEP][EBOOK][26][CAPT][BR][LAL1][V1]
     Público: LAL 1% de compradores históricos | BR | 25-65
     Tamanho estimado: 800K–1,5M pessoas

Anúncios: 1 por adset (imagem estática + copy Odonto-Oncologia)
Budget: R$50/dia (CBO distribuído entre adsets)
Pixel: XXXXXXXX — estado atual: ativo, 147 leads/semana

➡️ Para ativar, responda "ok". Para cancelar, responda "cancelar".
```

---

## Step 8: Activate on Confirmation

When user says "ok" (or equivalent):

```json
ads_activate_entity({
  "entity_id": "<campaign_id>",
  "entity_type": "campaign"
})
```

If user says "cancelar": do NOT delete (entities are PAUSED and can be activated later). Confirm entities remain PAUSED.

---

## Step 9: Log the Launch

Append to `<client>/.meta-ads/learnings.md`:

```markdown
## [DATE] — [CAMPAIGN_NAME]

**Launched:** YYYY-MM-DD  
**Budget:** R$XX/dia  
**Objective:** OUTCOME_LEADS  
**Audiences:** INT-ODONTO stack, LAL 1% compradores  
**Creative hypothesis:** Video VSL 60s com problema → solução → prova  
**Hooks tested:** V1 "Você sabe tratar um paciente oncológico na cadeira?"  
**Pixel:** Healthy (147 leads/week)  
**Expected CPL:** R$15–20  
**Review date:** 7 days after launch
```

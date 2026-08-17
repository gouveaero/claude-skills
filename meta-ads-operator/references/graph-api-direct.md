# Graph API Direto via System User Token (alternativa ao MCP)

Use quando o **Pipeboard MCP atinge rate limit** (Free plan tem cap semanal) ou quando precisa de operações em **batch grande** (muitas audiences/creatives/ads em sequência).

## Setup (uma vez por cliente que tem System User próprio)

Credenciais ficam em `~/.claude/secrets/meta-app.local.json` (gitignored, perm 600):

```json
{
  "app_id": "...",
  "app_secret": "...",
  "system_user_id": "...",
  "access_token": "EAA...",
  "ad_accounts": {"client_x": "act_..."},
  "page_ids": {"client_x": "..."},
  "pixel_ids": {"client_x": "..."}
}
```

**System User Token** (no Business Manager → Configurações → Usuários do sistema) com permissões: `ads_management, ads_read, business_management, pages_read_engagement, pages_manage_ads`. Tipo "Permanent" (não expira).

**Cobertura por System User**: cada System User vê apenas as ad accounts atribuídas a ele no respectivo BM. Se o cliente tem BM próprio (caso comum em agência), você precisa de:
- Um System User criado no BM do cliente, OU
- BM do cliente compartilhado com o System User da agência (Business Settings → Partners)

**Pattern recomendado**: registrar todos os System Users disponíveis no `~/.claude/secrets/meta-app.local.json` como uma estrutura por cliente:
```json
{
  "system_users": {
    "client_x": {"id": "...", "access_token": "...", "covered_acts": ["act_..."]},
    "client_y": {"id": "...", "access_token": "...", "covered_acts": ["act_..."]}
  }
}
```
Quando operar para um cliente, pegue o token correto via `client_code` do `.meta-ads.json` da pasta atual.

**Verifique cobertura antes de operar**: chame `/me/adaccounts?fields=id,name,account_status` com o token e confirme que o `act_id` do cliente alvo está na lista. Se não: o token não tem acesso, pare e peça ao usuário pra criar o System User ou compartilhar o BM.

## Quando usar Graph API direto vs MCP

| Cenário | Use |
|---|---|
| 1-3 chamadas de leitura (insights, audiences) | MCP Pipeboard |
| 1-3 chamadas de criação (1 campanha, 2 adsets) | MCP Pipeboard |
| **Upload em batch (10+ audiences, 20+ creatives)** | **Graph API direto** |
| **Atingiu rate limit Pipeboard** | **Graph API direto** |
| **Upload de imagens/vídeos locais** | **Graph API direto** (multipart files) |
| Diagnóstico/insights leitura | MCP (mais ergonômico) |

## Padrão de invocação via Bash + Python

```python
import json, os, requests
TOKEN = json.load(open(os.path.expanduser("~/.claude/secrets/meta-app.local.json")))["access_token"]
GRAPH = "https://graph.facebook.com/v21.0"

def post(path, **p):
    p["access_token"] = TOKEN
    return requests.post(f"{GRAPH}/{path}", data=p).json()

def get(path, **p):
    p["access_token"] = TOKEN
    return requests.get(f"{GRAPH}/{path}", params=p).json()
```

## Operações comuns

### Criar custom audience CSV-based + upload users

```python
# 1. Criar audience vazia
aud = post(f"{ACT}/customaudiences",
    name="ET_NEW_LIST",
    subtype="CUSTOM",
    customer_file_source="USER_PROVIDED_ONLY",
    description="...")
aud_id = aud["id"]

# 2. Upload users (chunks de 8000)
payload = {
    "schema": ["EMAIL", "PHONE", "FN", "LN"],
    "data": [["email", "phone", "fn", "ln"], ...],
    "is_raw": True,  # CRÍTICO em v21+ — Meta hashes internamente
}
post(f"{aud_id}/users", payload=json.dumps(payload))
```

### Criar pixel audience (sem subtype em v21+)

```python
rule = {"inclusions": {"operator": "or", "rules": [{
    "event_sources": [{"id": PIXEL, "type": "pixel"}],
    "retention_seconds": days * 86400,
    "filter": {"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": "Purchase"}]}
}]}}
post(f"{ACT}/customaudiences",
    name="ET_PIXEL_PURCHASE_180D",
    rule=json.dumps(rule),
    retention_days=180,
    prefill="true")
```

⚠️ **NÃO passe `subtype: WEBSITE`** — em v21+ Meta retorna "Parâmetro 'subtipo' não é aceito".

### Criar engagement audience (IG ou FB)

```python
# IG: event "ig_business_profile_engaged" (não "ig_business_profile_all" — esse é deprecated em v21)
# FB Page: event "page_engaged"
rule = {"inclusions": {"operator": "or", "rules": [{
    "event_sources": [{"id": IG_OR_PAGE, "type": "ig_business" or "page"}],
    "retention_seconds": days * 86400,
    "filter": {"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": "ig_business_profile_engaged"}]}
}]}}
post(f"{ACT}/customaudiences", name="...", rule=json.dumps(rule), retention_days=days)
```

### Criar Lookalike

```python
post(f"{ACT}/customaudiences",
    name="ET_LAL3_BASE",
    origin_audience_id=seed_id,
    lookalike_spec=json.dumps({"ratio": 0.03, "country": "BR", "type": "custom_ratio"}),
    subtype="LOOKALIKE")
```

⚠️ **Falha se seed audience tem <100 pessoas matched** ou ainda está populando (mostra "1000 placeholder"). Aguardar 1-6h após upload.

### Upload imagem via multipart (arquivo local)

```python
with open(filepath, "rb") as f:
    r = requests.post(f"{GRAPH}/{ACT}/adimages",
        files={"source": (filename, f, "image/png")},
        data={"access_token": TOKEN, "name": label})
new_hash = list(r.json().get("images", {}).values())[0].get("hash")
```

⚠️ **Não use `image_url` em system user app não publicado** — Meta retorna "(#3) Application does not have the capability". Multipart funciona.

### Upload imagem via URL HD (de uma conta CA01 → CA02 mesmo BM)

```python
# Se você tem o hash original na CA01 e quer migrar pra CA02:
url_resp = get(f"{ACT_OLD}/adimages", hashes=json.dumps([hash_orig]), fields="url,width,height")
hd_url = url_resp["data"][0]["url"]
# Download + multipart upload na nova conta (igual acima)
```

### Upload vídeo

```python
with open(videopath, "rb") as f:
    r = requests.post(f"{GRAPH}/{ACT}/advideos",
        files={"source": (name, f, "video/mp4")},
        data={"access_token": TOKEN, "name": label, "title": label},
        timeout=600)
video_id = r.json()["id"]
```

⚠️ **Vídeos são assíncronos** — após upload, espere `status.video_status=ready` antes de criar creative:
```python
info = get(video_id, fields="status,published")
# status.video_status = "ready" → OK
```

### Criar ad creative (imagem)

```python
spec = {
    "page_id": PAGE,
    "instagram_user_id": IG,
    "link_data": {
        "link": URL,
        "message": BODY,
        "name": HEADLINE,
        "image_hash": hash,
        "call_to_action": {"type": "LEARN_MORE", "value": {"link": URL}},
    }
}
post(f"{ACT}/adcreatives", name="...", object_story_spec=json.dumps(spec), url_tags=UTM)
```

### Criar ad creative (vídeo) — requer thumbnail!

```python
# 1. Pegar thumbnail do vídeo
pic = get(video_id, fields="picture")["picture"]
# 2. Spec com video_data
spec = {
    "page_id": PAGE,
    "instagram_user_id": IG,
    "video_data": {
        "video_id": video_id,
        "image_url": pic,  # OBRIGATÓRIO — sem isso Meta rejeita
        "message": BODY,
        "title": HEADLINE,
        "call_to_action": {"type": "LEARN_MORE", "value": {"link": URL}},
    }
}
post(f"{ACT}/adcreatives", name="...", object_story_spec=json.dumps(spec), url_tags=UTM)
```

### ❌ Reuso de creative via `object_story_id` NÃO funciona

Quando o post original foi criado com `asset_feed_spec` (DCO), Meta rejeita reuso simples com:
> "O criativo dinâmico está sem o ID do conjunto de produtos" (error_subcode 1815017)

**Workaround**: re-uploadar asset (image_hash ou video_id na conta-alvo) e criar creative novo. Na MESMA BM, video_id é reutilizável; image_hash NÃO é (precisa re-uploadar).

### Criar campanha — pegadinhas v21

```python
post(f"{ACT}/campaigns",
    name="...",
    objective="OUTCOME_SALES",
    status="PAUSED",
    buying_type="AUCTION",
    special_ad_categories=json.dumps([]),  # CRÍTICO: array vazio JSON, NÃO string "[]"
    is_adset_budget_sharing_enabled="false",  # OBRIGATÓRIO se ABO
    # NÃO passar bid_strategy aqui em ABO — vai pro adset
)
```

⚠️ Se passar `bid_strategy` na campanha sem budget na campanha → erro "Esta campanha não tem orçamento". **Em ABO, bid_strategy vai no nível adset.**

### Criar adset — pegadinhas

```python
targeting = {
    "age_min": 25, "age_max": 65,
    "geo_locations": {"countries": ["BR"], "location_types": ["home", "recent"]},
    "publisher_platforms": ["facebook", "instagram"],
    "facebook_positions": ["feed", "facebook_reels", "story"],
    "instagram_positions": ["stream", "story", "reels"],  # ⚠️ NÃO inclua "explore_home" sozinho — precisa "explore" também, ou nenhum
    "device_platforms": ["mobile", "desktop"],
    "custom_audiences": [{"id": "..."}],
    "excluded_custom_audiences": [{"id": "..."}],
    "targeting_relaxation_types": {"lookalike": 0, "custom_audience": 0},
    "targeting_automation": {"advantage_audience": 0},  # 1 ativa Advantage+ (cold)
}
post(f"{ACT}/adsets",
    campaign_id=cid,
    name="...",
    optimization_goal="OFFSITE_CONVERSIONS",
    billing_event="IMPRESSIONS",
    status="PAUSED",
    daily_budget=50000,  # cents (R$500/dia)
    bid_strategy="LOWEST_COST_WITHOUT_CAP",
    promoted_object=json.dumps({"pixel_id": PIXEL, "custom_event_type": "PURCHASE"}),
    targeting=json.dumps(targeting),
    attribution_spec=json.dumps([
        {"event_type": "CLICK_THROUGH", "window_days": 7},
        {"event_type": "VIEW_THROUGH", "window_days": 1}
    ]))
```

### Criar ad

```python
post(f"{ACT}/ads",
    name="...",
    adset_id=asid,
    creative=json.dumps({"creative_id": cid}),
    status="PAUSED")
```

Ads novos ficam em `effective_status: PENDING_REVIEW` por 15min-2h. Após Meta aprovar, vão automaticamente pra ACTIVE (se status=ACTIVE).

### Ativar entidade (campaign / adset / ad)

```python
post(entity_id, status="ACTIVE")  # retorna {"success": true}
```

### Listar ads de uma campanha (filtro broader)

```python
# Default exclui PAUSED+PENDING. Para ver TUDO:
get(f"{cid}/ads",
    fields="id,name,effective_status",
    filtering=json.dumps([{
        "field": "ad.effective_status",
        "operator": "IN",
        "value": ["ACTIVE", "PAUSED", "PENDING_REVIEW", "DISAPPROVED", "ADSET_PAUSED", "CAMPAIGN_PAUSED", "ARCHIVED"]
    }]))
```

## Rate limits (System User)

- ~25k chamadas/hora por business token (vs 200/hora user token)
- Erro `code: 17` = "User request limit reached" → aguardar 5-10 min
- **Retry exponencial**: 30s, 60s, 90s, 120s, 150s

```python
def post_with_retry(path, **p):
    for attempt in range(5):
        r = post(path, **p)
        if r.get("error", {}).get("code") == 17:
            time.sleep(30 * (attempt + 1))
            continue
        return r
    return r
```

## Performance tips

- Uploads em paralelo: `concurrent.futures.ThreadPoolExecutor(max_workers=4)` para imagens (max 3 para vídeos)
- Vídeo upload é assíncrono — paralelize uploads, depois aguarde batch via polling
- Audiences populam em 1-6h após upload — não tente criar LAL imediatamente

## Pegadinhas Meta v21 confirmadas (2026-05)

| Erro | Causa | Fix |
|---|---|---|
| "subtipo não é aceito" | `subtype: WEBSITE` deprecated | Omitir subtype, usar `rule` JSON |
| "Please send single PIIs" | SDK combinava keys | REST + `is_raw: true` no payload |
| "criativo dinâmico sem ID conjunto produtos" | Reuso de DCO | Re-uploadar asset + creative novo |
| "Application does not have capability" (#3) | Upload por URL no app não publicado | Multipart files= |
| "is_adset_budget_sharing_enabled" obrigatório | Default mudou | Passar `false` se ABO |
| "explore_home" inválido | placement deprecated sozinho | Usar `["stream", "story", "reels"]` |
| "Atualize forma de pagamento" | CA sem cartão | User adiciona em Billing |

## Cross-reference

- Setup completo do System User: `assets/system-user-setup.md` (a criar)
- Per-client playbook (operações cotidianas): `<ClientFolder>/.meta-ads/playbook.md` — leia primeiro se existir
- Estrutura completa de campanha: `<ClientFolder>/.meta-ads/structure-v*.md`
- Aprendizados históricos: `<ClientFolder>/.meta-ads/learnings.md`

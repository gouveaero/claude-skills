# CLI Fallback — Quando Usar CLI em vez do MCP

O MCP oficial Meta tem limitações. Para esses casos específicos, use CLI.

---

## Situações que exigem CLI

### 1. Upload de Imagem/Vídeo Local

O MCP oficial aceita apenas URLs públicas em `image_url`. Se o usuário fornece um arquivo local (`/tmp/criativo.jpg`), use a CLI para fazer upload e obter o hash.

**Unofficial CLI (Attainment Labs v0.1.0):**
```bash
/Users/gabriel/Library/Python/3.9/bin/meta-ads status \
  --account act_XXXXXXXXX
```

Este CLI opera via YAML config (cria campanha completa do arquivo). Útil para bulk creation.

**Alternativa recomendada para upload de imagem:**
Solicitar ao usuário que faça o upload via Meta Ads Manager > Assets > Images e forneça a URL pública. Isso é mais confiável do que depender do CLI unofficial.

---

### 2. Meta Ads CLI Oficial (Requer Python 3.12+)

O CLI oficial da Meta (`meta-ads-cli` by Meta, não o da Attainment Labs) requer Python 3.12+. O sistema atual tem Python 3.9.

**Instalação quando Python 3.12+ disponível:**
```bash
pip install meta-ads-cli  # verifica no https://developers.facebook.com
meta-ads campaign list --account-id act_XXXXXXXXX
meta-ads insights get --account-id act_XXXXXXXXX --date-preset last_30d --format json
meta-ads campaign create --config campaign.yaml --paused
meta-ads campaign activate --campaign-id <id>
```

**Comandos principais do CLI oficial:**
```bash
meta-ads campaign list|create|update
meta-ads adset create|update
meta-ads creative create
meta-ads ad create|update
meta-ads insights get --fields spend,impressions,ctr
meta-ads status          # health check da conta
meta-ads activate        # ativa campanha
meta-ads pause           # pausa campanha
```

**Flags úteis:**
- `--format json` — saída em JSON (pipeline para `jq`)
- `--no-input` — não solicitar input (CI/CD)
- `--force` — bypass de confirmações interativas
- `--version` — verificar versão instalada

---

### 3. Pipeboard CLI (Alternativa Multiplataforma)

Pipeboard CLI acessa Meta Ads, Google Ads e TikTok Ads via token único. Melhor para workflows multi-plataforma.

**Instalação:**
```bash
brew install pipeboard-co/tap/pipeboard  # macOS (brew não disponível no sistema atual)
# ou: baixar binário em https://github.com/pipeboard-co/pipeboard-cli
```

**Uso:**
```bash
export PIPEBOARD_API_TOKEN=<token de pipeboard.co/api-tokens>
pipeboard meta-ads get-campaigns --account-id act_XXXXXXXXX
pipeboard meta-ads get-insights --object-id act_XXXXXXXXX --date-preset last_30d
```

**Vantagem sobre CLI oficial:** sub-50ms startup, sem servidor, cobre Google Ads e TikTok Ads no mesmo binary.

---

### 4. Bulk Operations em Shell

Quando precisar criar 10+ adsets ou ads:

```bash
# Loop para criar múltiplos adsets via CLI oficial
for audience in INT LAL1 LAL3; do
  meta-ads adset create \
    --account-id act_XXXXXXXXX \
    --campaign-id <campaign_id> \
    --name "[LT][PEP][EBOOK][26][CAPT][BR][${audience}][V1]" \
    --paused \
    --optimization-goal LEAD_GENERATION \
    --daily-budget 5000
done
```

---

### 5. Export de Insights em CSV/JSON Grande

Para análises que exigem muitos dados históricos:

```bash
meta-ads insights get \
  --account-id act_XXXXXXXXX \
  --date-preset last_90d \
  --level adset \
  --fields "campaign_name,adset_name,spend,impressions,ctr,cpm,actions,cost_per_action_type" \
  --format json > /tmp/insights_90d.json

cat /tmp/insights_90d.json | jq '.[] | select(.cost_per_action_type[0].value > 50)'
```

---

## Decisão: MCP vs CLI

| Situação | Use |
|----------|-----|
| Criar/editar campanha, adset, ad | MCP (mais simples, menos setup) |
| Upload de imagem/vídeo local | CLI ou upload manual no Ads Manager |
| Diagnóstico e insights de performance | MCP (`ads_insights_*`) |
| Bulk creation (10+ entidades) | CLI com loop shell |
| Export grande para análise externa | CLI com `--format json` |
| Multi-plataforma (Google + TikTok + Meta) | Pipeboard CLI |
| Integração CI/CD não-interativa | CLI com `--no-input --force` |
| Ativar campanha após confirmação humana | MCP (`ads_activate_entity`) |

---

## Gotchas CLI

- O `meta-ads-cli` v0.1.0 (Attainment Labs, PyPI) é diferente do CLI oficial Meta. Verifique: `meta-ads --version` → se `0.1.0`, é o Attainment Labs.
- CLI oficial Meta requer Python 3.12+. Sistema atual tem 3.9 → instalar pyenv ou usar container para o CLI oficial.
- Exit codes padrão CLI oficial: 0 = sucesso, 3 = erro de autenticação, 4 = erro de API.
- Nunca usar `--force` em produção sem revisão humana — suprime todas as confirmações.

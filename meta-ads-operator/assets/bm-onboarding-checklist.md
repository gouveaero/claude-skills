# Business Manager Onboarding Checklist

Usar quando um cliente novo entra para a Exos e precisa ser conectado ao BM da agência.

---

## 1. Acesso ao Business Manager

- [ ] Solicitar ao cliente: acesso ao Meta Business Manager (nível Administrador ou Anunciante)
- [ ] URL: business.facebook.com → Configurações → Pessoas → Adicionar (email do gestor Exos)
- [ ] Nível mínimo: **Employee** no BM + **Advertiser** na conta de anúncios específica
- [ ] Verificar em: business.facebook.com → Contas → Contas de Anúncio → [conta do cliente]

---

## 2. Conta de Anúncios

- [ ] Confirmar `act_id` (formato: `act_XXXXXXXXX`)
  - No Ads Manager: URL contém o número após `/act_`
  - Via MCP: `ads_get_ad_accounts({})` após OAuth
- [ ] Verificar status da conta (ACTIVE, não restrita)
- [ ] Confirmar moeda: BRL (Real Brasileiro)
- [ ] Confirmar fuso horário: America/Sao_Paulo (GMT-3)
- [ ] Verificar limite de gasto: existe? qual?

---

## 3. Facebook Page + Instagram

- [ ] Confirmar `page_id` da Página do Facebook do cliente
  - Via MCP: `ads_get_pages_for_business({"business_id": "XXX"})`
  - Ou: facebook.com/[pagina] → Sobre → Informações da Página → ID
- [ ] Confirmar que a Page está conectada ao BM
- [ ] Confirmar `instagram_actor_id` (ID do perfil Instagram Business)
  - Em: business.facebook.com → Configurações → Contas Instagram
- [ ] Verificar se IG está conectado à Page do FB

---

## 4. Pixel / Meta Pixel (Dataset)

- [ ] Confirmar `pixel_id` (Dataset ID)
  - Em: business.facebook.com → Fontes de Dados → Pixels
  - Via MCP: `ads_get_dataset_details({"dataset_id": "XXX"})`
- [ ] Verificar se pixel está instalado no site do cliente
  - Via MCP: `ads_get_dataset_quality({"dataset_id": "XXX"})` → `event_match_quality >= 6`
  - Ou: Meta Pixel Helper (extensão Chrome)
- [ ] Confirmar eventos ativos: PageView, Lead, Purchase, ViewContent
- [ ] Se sem pixel → instalar via GTM ou código direto antes de qualquer campanha de conversão

---

## 5. CAPI (Conversions API) — Opcional mas recomendado

- [ ] Avaliar se o cliente tem tech para implementar CAPI (servidor Node/PHP ou integração Zapier/n8n)
- [ ] Se sim: configurar CAPI via Events Manager no BM
- [ ] Se lead gen nativo (Meta Lead Form): configurar CRM Sync (LeadSync, Zapier, n8n → WhatsApp/CRM)
- [ ] Verificar `ads_get_dataset_stats({"dataset_id": "XXX"})` para confirmar eventos chegando pelo CAPI

---

## 6. Audiences Base

Criar antes do primeiro lançamento. Requer dados históricos.

- [ ] Custom Audience: Compradores (evento Purchase) — 180 dias
  - Em: Ads Manager → Audiences → Create Audience → Custom Audience → Website → Purchase
- [ ] Custom Audience: Leads (evento Lead) — 60 dias
- [ ] Custom Audience: Visitantes LP (PageView URL contém /vendas ou /inscricao) — 30 dias
- [ ] Custom Audience: Engajadores IG — 60 dias
- [ ] LAL 1% de compradores (após ter ≥100 compradores na base)
- [ ] LAL 1-3% de compradores

---

## 7. Preencher .meta-ads.json

Após coletar todos os IDs, criar `<ClienteFolder>/.meta-ads.json` usando `assets/per-client.template.json`:

```json
{
  "client_name": "Dr. Kleber Meireles",
  "client_code": "KL",
  "act_id": "act_XXXXXXXXX",
  "business_id": "XXXXXXXXX",
  "page_id": "XXXXXXXXX",
  "instagram_actor_id": "XXXXXXXXX",
  "pixel_id": "XXXXXXXXX",
  "default_currency": "BRL",
  "timezone": "America/Sao_Paulo",
  "saved_audiences": {
    "compradores_180d": "<audience_id>",
    "leads_60d": "<audience_id>",
    "lal1_compradores": "<audience_id>"
  },
  "active_projects": ["SEMENTE26", "PERP"]
}
```

- [ ] Arquivo criado em `Exos/<Cliente>/.meta-ads.json`
- [ ] `.meta-ads.json` e `.meta-ads/` estão no `.gitignore`
- [ ] Inicializar `.meta-ads/learnings.md` vazio

---

## 8. Verificação Final

- [ ] `ads_get_ad_accounts({})` retorna a conta do cliente
- [ ] `ads_get_dataset_quality({"dataset_id": "XXX"})` retorna score ≥ 6
- [ ] `ads_get_errors({"business_id": "XXX"})` retorna zero erros
- [ ] `.meta-ads.json` preenchido e não commitado no git

---

**Onboarding concluído por:** _______________ **Data:** _______________

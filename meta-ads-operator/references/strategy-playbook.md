# Strategy Playbook — Meta Ads Operator (Exos)

This playbook covers the 4 business models the Exos client portfolio uses. Read `paid-ads` skill for broader platform strategy context.

---

## Business Model 1: Lançamento Brasileiro

**Clients:** Dr. Kleber (Lançamento + perpétuo), Letícia Lang (Workshop ONCO+), Lívia Tolentino (Ebook → pós-graduação).

### Funnel Phases

| Phase | Duration | Objective | Budget % | Audience |
|-------|----------|-----------|----------|----------|
| Captação (topo) | 2–4 weeks pre-cart | OUTCOME_LEADS | 50% | Cold (LAL 1–3%, interests) |
| Aquecimento (meio) | 1 week pre-cart | OUTCOME_ENGAGEMENT | 20% | Warm (leads, video viewers 50%+) |
| Carrinho aberto | 3–7 days | OUTCOME_SALES | 25% | Hot (lead list, LP visitors) |
| Recovery/Upsell | During/post cart | OUTCOME_SALES | 5% | Abandonment (visitou checkout, não comprou) |

### Campaign Structure (Lançamento)

```
Lançamento CBO - Captação [R$XXX/dia]
  ├── Adset: LAL 1% (base: compradores históricos)
  ├── Adset: LAL 1-3% (base: leads qualificados)
  └── Adset: Interests stack (5-8 interesses nicho)

Lançamento ABO - Aquecimento [R$XX/dia cada adset]
  ├── Adset: Video viewers 50%+ (últimos 30d)
  ├── Adset: Engajamento IG/FB (últimos 30d)
  └── Adset: Lista de leads (uploaded CSV ou pixel)

Lançamento CBO - Carrinho [R$XXX/dia]
  ├── Adset: Hot retarget (visitou LP venda, não comprou)
  ├── Adset: Leads que não compraram
  └── Adset: LAL 1% de compradores (escala)
```

### KPIs por Fase

| Phase | Primary KPI | Target (odonto) | Kill if |
|-------|-------------|-----------------|---------|
| Captação | CPL (lead) | R$5–25 | CPL > 3× meta após 7 dias |
| Aquecimento | CPM, CTR | CPM < R$30, CTR > 1.5% | CTR < 0.8% |
| Carrinho | CPA (venda) | 15–25% da oferta | CPA > 40% após 3 dias |
| Recovery | ROAS | ≥3× | ROAS < 2× |

### Budget Split Reference

- **Total diário disponível: R$500**
  - Captação CBO: R$250
  - Aquecimento ABO: R$50 × 3 adsets = R$150
  - Carrinho CBO: R$100
- **Escalar:** quando CPL estável 3 dias → +20% captação

---

## Business Model 2: Funil Perpétuo (Kleber evergreen)

Campanhas rodando sem parar, não dependem de datas.

### Estrutura Perene

```
[KL][PERP][INFO][26][TOPO][BR][LAL3][V1] — CBO Captação
  Budget: R$XXX/dia (maior % do total)
  Objetivo: OUTCOME_LEADS
  Adsets: LAL 1%, LAL 3%, Interests cold
  Otimização: Conversão (lead)

[KL][PERP][INFO][26][MEIO][BR][WARM][V1] — ABO Aquecimento
  Budget: R$XX/dia por adset
  Objetivo: OUTCOME_ENGAGEMENT ou TRAFFIC
  Adsets: Video 50%+, Engajamento, LP visitors 90d

[KL][PERP][INFO][26][FUNDO][BR][HOT][V1] — CBO Conversão
  Budget: R$XXX/dia
  Objetivo: OUTCOME_SALES
  Adsets: Leads não comprados, Visitantes checkout
```

### Regras do Funil Perpétuo

- Nunca pausar tudo ao mesmo tempo (perde dados de aprendizado).
- Rodar testes de criativo no topo a cada 30 dias (novo hook, nova thumbnail).
- Atualizar públicos de retarget mensalmente (evitar saturação).
- Budget mínimo por adset ABO: R$20/dia (abaixo disso, sem entrega suficiente para aprender).

---

## Business Model 3: Lead-Gen B2C (Lívia ebook)

Objetivo: capturar lead (ebook) → nutrir → vender pós-graduação.

### Decisão: Lead Form Nativo vs LP+Pixel

| Critério | Lead Form Nativo | LP + Pixel |
|----------|-----------------|------------|
| Volume | Alto | Médio |
| Qualificação | Baixa (pré-preenchido) | Alta |
| Velocidade | Imediata | Depende de pixel |
| Follow-up | Requer integração (LeadSync/n8n) | Direto via pixel event |
| Custo de setup | Baixo | Médio |

**Recomendação Exos:** usar LP + pixel para produtos acima de R$500 (mais qualificação). Lead form nativo para ebooks gratuitos/low-cost.

### Campaign (Lívia Ebook)

```
[LT][PEP][EBOOK][26][CAPT][BR][COLD][V1] — CBO OUTCOME_LEADS
  Adsets:
    - Interests: Ortodontia, Periodontia, Odontologia, Concursos Odonto, CRO
    - LAL 1% (base: lista de alunos históricos se disponível)
  Creative: Imagem estática ou Vídeo VSL curto (15–30s)
  CTA: Baixar Ebook / Quero Receber

Atenção: configurar follow-up automático (LeadSync → WhatsApp ou n8n → e-mail) ANTES de ativar.
```

---

## Business Model 4: Evento ao Vivo (Letícia Workshop)

Workshop presencial ou online com data fixa (ex: 16-17/mai/2026).

### Timeline de Campanhas

| Prazo p/ evento | Ação | Orçamento |
|-----------------|------|-----------|
| 4+ semanas antes | Captação antecipada (desconto early bird) | 40% |
| 2-4 semanas antes | Escalar captação, iniciar retarget interessados | 45% |
| 1-2 semanas antes | Urgência + last call | 10% |
| Última semana | Recovery (clicou mas não comprou) | 5% |

### Audiences para Evento

- **Frio:** LAL 1% de compradores de eventos anteriores, interests (onco-oncologia, oncologia, odonto, residência)
- **Morno:** Visitou LP do evento, salvou post com CTA do evento, assistiu vídeo teaser 50%+
- **Quente:** Iniciou checkout, lead capturado há <7 dias

### Criativo para Evento

- Fase captação: VSL de 60s com Dr. Letícia explicando o valor do evento
- Fase urgência: story/reel curto com countdown, vagas restantes
- Fase recovery: carrossel com depoimentos de edições anteriores

---

## Cross-Cutting: Regras de Budget

1. **Mínimo por campanha CBO:** R$100/dia (abaixo disso, Meta não otimiza direito).
2. **Mínimo por adset ABO:** R$20/dia.
3. **Escala segura:** +20% a cada 3 dias quando o KPI estiver dentro da meta.
4. **Learning phase:** precisa de ≥50 conversões/semana no pixel event otimizado. Se não atingir, CBO com ABO desligados até o pixel ter dados suficientes.
5. **Nunca aumentar orçamento de madrugada** (Meta recalcula a learning phase e pode desperdiçar o pico da manhã).

---

## Budget Allocation Framework por Total Mensal

| Total mensal | Distribuição sugerida |
|-------------|----------------------|
| R$3.000/mês | 70% captação, 20% retarget, 10% aquecimento |
| R$10.000/mês | 60% captação, 25% retarget, 15% aquecimento |
| R$30.000/mês | 50% captação, 30% retarget, 20% aquecimento |

Ajustar conforme estágio do funil (antes do lançamento = mais captação; durante carrinho = mais retarget).

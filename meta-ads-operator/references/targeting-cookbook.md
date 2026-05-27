# Targeting Cookbook — Meta Ads Operator

Receitas práticas de audiências para o portfólio Exos. Todos os públicos são para Brasil (salvo indicação).

---

## 1. Lookalike Audiences (LAL)

| Tipo | Seed | Tamanho | Quando usar |
|------|------|---------|-------------|
| LAL 1% | Compradores históricos | ~1–2M BR | Melhor qualidade, menor alcance. Lançamentos, top de funil |
| LAL 1-3% | Compradores históricos | ~3–5M BR | Escala com qualidade. CBO para escalar captação |
| LAL 5-10% | Leads qualificados | ~8–15M BR | Volume máximo. Awareness, early stage |
| LAL 1% engajadores | Top 25% engajadores IG/FB | ~1M BR | Alternativa quando seed de comprador é pequeno (<500 pessoas) |

**Regra de seed:** seed precisa de ≥100 pessoas (ideal: 1.000+) para LAL ser confiável. Verificar tamanho antes de criar.

**Atualização:** Recriar LAL a cada 30 dias para capturar novos comportamentos na base.

---

## 2. Custom Audiences para Retarget

### Por evento de pixel

| Audiência | Condição | Janela | Uso |
|-----------|----------|--------|-----|
| Visitantes LP | PageView URL contém `/ebook` ou `/workshop` | 30 dias | Retarget quente |
| Visitantes LP venda | PageView URL contém `/vendas` ou `/inscricao` | 14 dias | Retarget urgência |
| Abandono checkout | InitiateCheckout sem Purchase | 7 dias | Recovery carrinho |
| Compradores | Purchase event | 180 dias | Seed para LAL, exclude de prospecção |
| Leads não comprados | Lead sem Purchase | 60 dias | Nurture → venda |
| ViewContent alto | ViewContent >3× na mesma URL | 30 dias | Muito interessado, não converteu |

### Por vídeo

| Audiência | Condição | Janela | Uso |
|-----------|----------|--------|-----|
| Vídeo 25%+ | ThruPlayPercentage ≥ 25% | 30 dias | Engajou com o conteúdo |
| Vídeo 50%+ | ThruPlayPercentage ≥ 50% | 30 dias | Morno — base para aquecimento |
| Vídeo 75%+ | ThruPlayPercentage ≥ 75% | 30 dias | Quente — base para venda |
| Vídeo 95%+ | ThruPlayPercentage ≥ 95% | 14 dias | Muito quente — prioridade em recovery |

### Por engajamento IG/FB

| Audiência | Condição | Janela | Uso |
|-----------|----------|--------|-----|
| Engajadores IG | Interagiram com perfil IG | 60 dias | Aquecimento |
| Engajadores FB | Curtiram/comentaram/salvaram posts | 60 dias | Aquecimento |
| Salvou post | Saved post | 90 dias | Alta intenção |
| Enviou mensagem | Enviou DM via anúncio ou perfil | 30 dias | Super quente |

---

## 3. Interesses por Nicho (Odontologia — portfólio principal Exos)

Estes IDs podem mudar — validar antes de usar em campanhas novas.

### Clínico/Geral

```json
[
  {"id": "6003107902433", "name": "Dentistry"},
  {"id": "6003349442459", "name": "Orthodontics"},
  {"id": "6003396188899", "name": "Dental implant"},
  {"id": "6003614358912", "name": "Oral hygiene"},
  {"id": "6004129555695", "name": "Dental surgery"},
  {"id": "6003232892397", "name": "Periodontology"}
]
```

### Educação/Carreira Odonto

```json
[
  {"id": "6003139438447", "name": "Medicine"},
  {"id": "6003561800617", "name": "Health care"},
  {"id": "6004011440672", "name": "Health professional"},
  {"id": "6003484285615", "name": "Residency (medicine)"},
  {"id": "6003262334473", "name": "Postgraduate education"}
]
```

### Oncologia (para Letícia Lang — Odonto-Oncologia)

```json
[
  {"id": "6003107902433", "name": "Dentistry"},
  {"id": "6003560629753", "name": "Oncology"},
  {"id": "6003724116853", "name": "Cancer"},
  {"id": "6003616021762", "name": "Chemotherapy"},
  {"id": "6003232892397", "name": "Periodontology"}
]
```

### Stack recomendado para captação fria (odonto, BR)

Use 5–8 interesses por adset. Não misturar interesses muito genéricos (ex: "Health care") com muito específicos (ex: "Dental implant") no mesmo adset — cria audiência confusa. Prefira stacks temáticos.

**Stack A — Especialistas clínicos:**
Dentistry + Orthodontics + Periodontology + Dental implant

**Stack B — Educação e carreira:**
Postgraduate education + Residency + Health professional + Medicine

**Stack C — Público amplo saúde:**
Health care + Health science + Nutrition + Wellness

---

## 4. Públicos Frios por Comportamento

Behaviors disponíveis via Meta Ads Manager (não via MCP oficial). Úteis para Brasil:

| Comportamento | Uso |
|---------------|-----|
| Pequenos empreendedores (pequenas empresas) | Dentistas donos de clínica |
| Frequência de viagem: viajante frequente | Público premium |
| Usuários de dispositivos de alta renda (iPhone alto nível) | Público premium |
| Compradores online ativos | Para venda de cursos/infoprodutos |
| Engajados com conteúdo de negócios | Empreendedores |

---

## 5. Targeting por Região (Brasil)

| Segmentação | Quando usar |
|-------------|-------------|
| Brasil inteiro | Cursos online, lançamentos sem presencial |
| SP + RJ + MG + RS + PR | Maior poder aquisitivo. Para eventos presenciais ou segmento premium. |
| Capitais BR | Maior densidade de profissionais de saúde |
| São Paulo (estado) | Quando o evento ou cliente tem forte base paulista |
| Exclude: N/NE | Quando CPL muito alto vindo dessas regiões e produto não converte |

---

## 6. Faixas Etárias por Perfil de Cliente

| Perfil | Faixa ideal | Notas |
|--------|------------|-------|
| Dentista comprando pós | 25–45 | Residência + recém-formado |
| Dentista experiente comprando MBA | 30–55 | Já estabelecido |
| Paciente dental consumer | 25–65 | Amplo |
| Oncologista/especialista | 28–55 | Formação longa |
| Evento profissional premium | 30–60 | Maior poder aquisitivo |

---

## 7. Exclusões Padrão

Sempre excluir em campanhas de captação (não retarget):

```json
{
  "exclusions": {
    "custom_audiences": [
      {"id": "<compradores_180d_audience_id>"},
      {"id": "<leads_atuais_audience_id>"}
    ]
  }
}
```

Isso evita gastar budget em quem já converteu e melhora a eficiência do CPL.

---

## 8. Estratégia de A/B por Público

Nunca teste mais de um elemento por vez. Para testar audiências:

1. Criar 2 adsets irmãos dentro do mesmo CBO.
2. Adset A: LAL 1% de compradores.
3. Adset B: Interests stack odonto.
4. Mesmos criativos, mesmo budget de adset (se ABO) ou CBO distribuído.
5. Deixar rodar 7 dias sem tocar.
6. Killer: adset com CPL 2× acima do irmão após 7 dias → pausar.

Para testes de criativo no mesmo público: use `references/optimization-playbook.md` — seção "When to duplicate vs edit in-place".

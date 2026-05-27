# Safety Rules — Meta Ads Operator

Estas regras protegem o orçamento real dos clientes da Exos. Cada uma existe por uma razão específica.

---

## Regra 1: Toda entidade nasce PAUSED

**Regra:** `"status": "PAUSED"` em toda chamada de `ads_create_campaign`, `ads_create_ad_set`, `ads_create_ad`. Nunca passar `"status": "ACTIVE"` na criação.

**Why:** Uma campanha ativada inadvertidamente pode gastar centenas de reais em minutos antes de ser percebida. Meta começa a distribuir orçamento imediatamente após ativação.

**How to apply:** Verificar o payload antes de toda chamada de criação. Se `status` não estiver explícito, definir como `PAUSED` manualmente.

---

## Regra 2: Confirmação humana antes de ativar

**Regra:** Antes de chamar `ads_activate_entity` ou `ads_update_entity` com `status: ACTIVE`, apresentar resumo completo e aguardar resposta explícita "ok" (ou equivalente claro).

**Summary obrigatório contém:**
- Nome da entidade
- Objetivo e tipo (campaign/adset/ad)
- Budget diário e lifetime (se aplicável)
- Estimativa de tamanho do público
- URL do criativo
- Data de início
- Pixel/evento de otimização + status de saúde

**Why:** A confirmação cria uma linha de responsabilidade clara. Se algo der errado, tanto o gestor quanto o cliente sabem que houve revisão humana antes do gasto.

**How to apply:** Se o usuário disser algo vago como "pode ativar" sem ter visto o resumo → apresentar o resumo primeiro, aguardar "ok" explícito.

---

## Regra 3: Budget changes máximo 20%

**Regra:** Nunca propor ou aplicar um aumento/redução de orçamento superior a 20% em uma única edição. Entre edições, esperar no mínimo 24 horas.

**Why:** O algoritmo de entrega da Meta recalibra a distribuição quando o budget muda. Mudanças bruscas (ex: R$100 → R$300) forçam a campanha a entrar novamente na learning phase, desperdiçando os dados de otimização acumulados. A "regra dos 20%" é documentada pelos próprios times de Meta.

**How to apply:**
```
Budget atual: R$100 → máximo novo: R$120 (ou mínimo R$80)
Budget atual: R$500 → máximo novo: R$600 (ou mínimo R$400)
```

Se o usuário pedir um aumento maior (ex: "dobra o budget"), explicar o risco e propor escalonamento em 3–5 dias.

---

## Regra 4: Não pausar learning phase sem evidência clara

**Regra:** Campanhas com < 50 conversões/semana no evento otimizado estão em learning phase. Não pausar, não editar targeting, não mudar creative sem evidência clara de falha (ex: zero gasto em 48h, billing error, CPL > 5× a meta).

**Why:** A Meta precisa de ~50 conversões por semana para sair da learning phase e começar a otimizar de verdade. Interferências prematuras "reiniciam o contador" e desperdiçam o budget de aprendizado já gasto.

**How to apply:** Verificar status da learning phase antes de qualquer otimização. Se a campanha tem < 50 conv/semana, comunicar ao usuário e aguardar 3–7 dias antes de qualquer mudança.

Exceção: se CPL > 10× a meta após 5 dias com gasto real (não apenas falta de entrega), propor pausa.

---

## Regra 5: Pré-flight obrigatório para campanhas de conversão

**Regra:** Antes de criar qualquer campanha com objetivo `OUTCOME_LEADS` ou `OUTCOME_SALES`, rodar:
1. `ads_get_dataset_quality` — verificar `event_match_quality >= 6`
2. `ads_get_errors` — verificar ausência de erros de billing/política

**Why:** Lançar uma campanha de conversão com pixel quebrado ou conta com erro de billing é gastar dinheiro sem resultado. O pré-flight leva 10 segundos e evita um diagnóstico frustrante 3 dias depois.

**How to apply:** Se `event_match_quality < 6`, reportar ao usuário e recomendar verificar o pixel antes de continuar. Não bloquear o lançamento, mas documentar o risco.

---

## Regra 6: Nunca cruzar contexto de cliente

**Regra:** Ao trabalhar na pasta de cliente A, nunca operar no `act_id` de cliente B. Confirmar `act_id` contra o `.meta-ads.json` da pasta atual antes de qualquer operação de escrita.

**Why:** Misturar contas em agência é um erro catastrófico — pode criar campanhas, gastar orçamento ou alterar settings na conta errada. A separação por pasta + config file é a única salvaguarda confiável.

**How to apply:**
1. Ler `act_id` do `.meta-ads.json` da pasta atual.
2. Se o usuário mencionar um `act_id` diferente, confirmar: "Você quer operar na conta `act_YYY` que não é a conta padrão de `<ClienteName>`. Confirma?"
3. Nunca assumir que o `act_id` mencionado na conversa é igual ao do `.meta-ads.json`.

---

## Rationalization Table

Pensamentos que indicam que você está prestes a violar uma regra:

| Pensamento | Realidade |
|------------|-----------|
| "É só um teste rápido" | Ativar = gastar dinheiro real. Sempre confirmar. |
| "O budget é pequeno, sem risco" | R$50/dia em conta errada = R$1.500/mês. |
| "O cliente quer subir hoje" | Urgência não elimina o risco de erro. Confirmação leva 30 segundos. |
| "Eu já revisei, pode ativar" | Você revisou, o cliente ainda não. Ele precisa ver o resumo. |
| "É só editar o budget, não precisa confirmar" | Budget +50% reinicia learning phase. Sim, precisa confirmar. |
| "Vou pausar agora e reavaliar" | Se estiver em learning phase, pausar desperdiça o aprendizado. Espera 3 dias. |
| "O pixel tá com score 4, mas vou subir assim mesmo" | Conversions com pixel ruim = dados errados + otimização errada = dinheiro desperdiçado. |
| "Posso criar como ACTIVE e pausar logo depois" | "Logo depois" pode ser 5 minutos e R$30 gastos. Crie PAUSED. |
| "Sei que a conta certa é act_ABC" | Leia o .meta-ads.json. Não confie na memória. |

---

## Red Flags — STOP IMEDIATO

Se você está prestes a fazer qualquer uma dessas ações, **pare** e revise:

- [ ] Chamando `ads_create_*` com `status: ACTIVE`
- [ ] Chamando `ads_activate_entity` sem ter apresentado o summary completo
- [ ] Propondo mudança de budget > 20%
- [ ] Editando targeting ou objective de campanha em learning phase
- [ ] Usando um `act_id` diferente do que está no `.meta-ads.json` da pasta atual
- [ ] Submeter nome que não passa no regex de naming conventions
- [ ] Usando objetivo legacy (`LEAD_GENERATION`, `CONVERSIONS`, `LINK_CLICKS`)
- [ ] Subindo campanha de conversão sem rodar `ads_get_dataset_quality` primeiro

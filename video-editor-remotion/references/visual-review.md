# Visual Review — Loop Iterativo Obrigatório

Depois do render do proxy (Fase 7), `visual_review.py` extrai 1 frame por `rich_overlay` + escreve `visual_review_brief.md` com checklist específica por kind.

## Workflow do loop

1. **Ler cada frame** (Read tool).
2. **Aplicar checklist específica do kind** (definida em `visual_review.py`).
3. **Consertar problemas** em `RichOverlays.tsx` + ajustar `edit_plan.json` se preciso.
4. **Re-renderizar**.
5. **Re-rodar `visual_review.py`** — a iteração # incrementa, novos frames extraídos.
6. **REPETIR até NENHUM problema visual remanescer** (max 5 iterações).

Só ENTÃO apresentar o proxy ao humano.

## Erros catalogados (postmortem)

Erros que historicamente passaram em reviews simples e foram capturados pelo loop:

- **Texto fora de bounds** — overlay com `width: 100%` empurrando texto pra fora da safe zone
- **White-on-white** — fundo claro + texto branco, ilegível
- **Pleonasmos visuais** — duas representações da mesma coisa (ex: ícone $$ + texto "DINHEIRO")
- **SVG amador** — figura humana ou balança desenhada em SVG cru (ver [overlay-density.md](./overlay-density.md))
- **Sub-pixel aliasing** — bordas serrilhadas em SVG (fix: `--scale=2`, ver [known-bugs.md](./known-bugs.md))
- **Frames de transição capturados** — overlay em mid-animation com `opacity=0.2` parece "quebrado". `visual_review.py` extrai frame do middle 60% da duração pra evitar isso.

## Quando o loop pode terminar

O brief explicita "PASS" ou "FAIL" por overlay. Loop só termina quando:
- Todos os overlays = PASS, OU
- Iteração #5 atingida (escalate pro humano com explicação dos issues remanescentes)

**Não terminar o loop antecipadamente** "porque está bom o suficiente" — overlays curtos (<2s) passam batido em review humana mas o LLM consegue inspecionar frame-a-frame.

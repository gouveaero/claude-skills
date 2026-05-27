# Aspect Ratios — 9:16 vs 16:9

## 9:16 — Vertical (Reels, TikTok, Shorts)

**Resolução:** 1080 × 1920
**Uso:** Instagram Reels, TikTok, YouTube Shorts, Stories

### Safe areas (evite elementos críticos fora dessas zonas)
- **Topo:** primeiros 15% (270px) — reservado para UI do app (notificações, botões)
- **Base:** últimos 25% (480px) — reservado para caption nativa, botões de ação
- **Zona segura de conteúdo:** 270px → 1440px (do topo)

### Tamanhos de texto recomendados
- Hook/título principal: 72–96pt
- Corpo da legenda: 52–64pt
- Legenda kinetic (KineticCaption): 56pt, `position_y: 0.55` (centro-baixo)
- StatOverlay big number: 280–360pt
- LowerThird nome: 40pt, `positionY: 0.82`

### `objectFit` no VideoCut
- Clips horizontais (16:9) em frame vertical: `objectFit: "cover"` + crop centralizado
- Clips verticais (9:16) nativos: `objectFit: "cover"` sem crop

### Zoom keyframes em 9:16
- `transform_y` negativo desloca para cima (mostra rosto/produto)
- `transform_y` positivo desloca para baixo (mostra texto/ação)
- Máximo recomendado: `transform_x: ±0.15`, `transform_y: ±0.15`

---

## 16:9 — Horizontal (YouTube, LinkedIn)

**Resolução:** 1920 × 1080
**Uso:** YouTube, LinkedIn feed horizontal, apresentações

### Safe areas
- **Laterais:** primeiros/últimos 5% (96px) — evite elementos críticos
- **Topo:** primeiros 10% (108px) — reservado para thumbnails expandidas
- **Base:** últimos 10% (108px) — legendas automáticas do YouTube

### Tamanhos de texto recomendados
- Título/hook: 60–80pt
- Corpo da legenda: 44–56pt
- LowerThird: `positionY: 0.85`
- StatOverlay: 200–280pt

### `objectFit` no VideoCut
- Clips verticais (9:16) em frame horizontal: `objectFit: "contain"` com barras laterais OU `"cover"` com crop agressivo (escolha no brand-config)

### Zoom keyframes em 16:9
- `transform_x` para pan horizontal (revelar elementos à direita/esquerda)
- `transform_y` com menor amplitude que em 9:16

---

## Conversão automática

O `plan_edit.py` recebe `--aspect` e ajusta automaticamente:
- `resolution` no `edit_plan.json`
- Recomendações de `position_y` das legendas
- Tamanhos de fonte no system prompt
- `objectFit` nas props do `VideoCut`

O `build_pipeline.py` passa `--aspect` para todos os scripts que precisam.

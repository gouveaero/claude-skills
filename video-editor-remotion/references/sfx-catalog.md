# Catálogo SFX — Guia de Uso

Biblioteca em `/Users/gabriel/Documents/EFEITOS SONOROS/` — 262 arquivos, 17 categorias.
Índice em `assets/sfx_index.json`.

## Como o pipeline usa os SFX

1. `plan_edit.py` declara `sfx[]` com `category` + `at_ms` + `intent` + `volume_db`
2. `capcut_draft_builder.py` resolve para um arquivo concreto usando `random.seed(reel_name + category)` (reprodutível — mesmo reel sempre usa o mesmo arquivo por categoria)
3. Insere como AudioSegment na Track A2 do draft CapCut

## Categorias e uso recomendado

| Categoria | Arquivos | Uso principal | Volume típico |
|---|---|---|---|
| **WOOSH** | 107 | Cortes, swipes, entradas/saídas de overlay, mudança de cena | -8 dB |
| **PLIM** | 15 | Destaques de números, check-marks, revelações positivas, notificações | -10 dB |
| **RISER** | 8 | Build-up antes do hook, tensão antes de revelação, intro | -12 dB |
| **CLICK** | 35 | UI, CTAs, checklist items, botão, mouse click | -14 dB |
| **DIGITAL** | 25 | Interfaces digitais, overlays de UI, transições de tela tech | -12 dB |
| **CINEMATICA** | 5 | Impacto máximo, clímax, revelação dramática, CTA final | -6 dB |
| **CAMERA** | 19 | Flash de câmera, shutter, revelações de produto/rosto | -10 dB |
| **TRANSIÇÃO** | 22 | Mudanças de ato longas, passagem de tempo | -14 dB |
| **VARIAVEIS** | 7 | Especiais: Epic Impact, Braaam, XP Error, boa ideia | variável |
| **GLITCH** | 2 | Pattern interrupt, virada narrativa, momento de problema | -8 dB |
| **AMBIENTE** | 6 | B-roll de locação, paisagem sonora de fundo (longo) | -18 dB |
| **DINHEIRO** | 2 | Menção a valores, economia, resultado financeiro | -10 dB |
| **CONTAGEM** | 1 | Countdown, antes de revelar estatística | -12 dB |
| **ROLAGEM** | 4 | Listas longas, progressão mecânica, contagem crescente | -14 dB |
| **TECLADO** | 2 | Cenas de trabalho, digitação, dados sendo inseridos | -16 dB |
| **ESTALO** | 1 | Marcação rítmica de corte, enfatizar palavra-chave | -8 dB |
| **POPS** | 1 | Aparição de elemento, balão de texto, popup | -10 dB |

## Padrões de uso por tipo de vídeo

### Reel de conteúdo educacional (30s)
```
0ms:      RISER (-12dB)     — build-up do hook
1500ms:   WOOSH (-8dB)      — entrada do primeiro clip
4000ms:   PLIM (-10dB)      — primeiro número/dado
8000ms:   WOOSH (-8dB)      — corte para segundo clip
14000ms:  CINEMATICA (-6dB) — ponto de virada
18000ms:  WOOSH (-8dB)      — corte para solução
24000ms:  PLIM (-10dB)      — resultado/benefício
28000ms:  CLICK (-14dB)     — CTA
```

### Vídeo de produto/venda (60s)
```
0ms:      RISER (-12dB)     — abertura
3000ms:   WOOSH (-8dB)      — apresentação do problema
12000ms:  GLITCH (-8dB)     — virada (problema → solução)
15000ms:  WOOSH (-8dB)      — apresentação da solução
25000ms:  DINHEIRO (-10dB)  — menção ao preço/economia
30000ms:  PLIM (-10dB)      — benefício 1
35000ms:  PLIM (-10dB)      — benefício 2
40000ms:  PLIM (-10dB)      — benefício 3
50000ms:  CINEMATICA (-6dB) — prova social / resultado
55000ms:  CLICK (-14dB)     — CTA
```

## Atualizando o índice

Quando adicionar novos SFX à pasta:
```bash
python ~/.claude/skills/video-editor/scripts/build_sfx_index.py
```

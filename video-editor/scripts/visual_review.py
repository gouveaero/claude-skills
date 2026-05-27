#!/usr/bin/env python3
"""
visual_review.py — Fase 7.5 (entre preview e gate humano)

Extrai frames-chave do proxy.mp4 e escreve um brief markdown com critérios
de QA RIGOROSOS, especificos por tipo de overlay, baseados em erros que
historicamente passam despercebidos.

Uso:
    python3 visual_review.py --proxy <proxy.mp4> --plan <edit_plan.json>
                             --output-dir <review_dir> [--agent]

Exit codes:
    0 — sucesso
    1 — erro
    2 — modo --agent: agente deve revisar visualmente e consertar
"""
import argparse, json, subprocess, sys
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════
# QA CRITÉRIOS POR TIPO DE OVERLAY
# Baseados em falhas historicas — cada item DEVE ser explicitamente checado
# ═══════════════════════════════════════════════════════════════════════
QA_CRITERIA_BY_KIND = {
    "stamp_brand": [
        "Stamp circular legível (texto não corta na curva).",
        "Não obscurece o rosto do speaker.",
        "Cor de contraste suficiente com background atrás dele.",
    ],
    "roman_scroll_wipe": [
        "Não cobre captions ou rosto do speaker durante a transição.",
        "Aparece em momento de pivot temporal/narrativo (não no meio de uma frase do gancho).",
        "Duração curta (~0.5-1s) — não deve ser persistente.",
    ],
    "roman_columns_bg": [
        "Background sutil, NÃO parece 'sombra de imagem' ou erro visual.",
        "Posicionado claramente como moldura/elemento de fundo (não no meio do frame).",
        "Opacidade moderada — visível mas não distrai.",
    ],
    "year_caption": [
        "Texto legível, posição não conflita com captions.",
        "Mantida apenas durante o segmento narrativo apropriado.",
    ],
    "vespasian_bust": [
        "ÍCONE RECONHECÍVEL como busto/perfil de imperador romano (não parece ânfora, vaso, mancha).",
        "Tem coroa de louros visível.",
        "Tem nariz/perfil clássico distinguível.",
        "Posicionado em corner/edge, não cobre rosto.",
        "USE SVG paths bem desenhados ou referência a icon library (heroicons, lucide, simpleicons). Não desenhe paths SVG na mão — use templates/refs reais.",
    ],
    "roman_latrine": [
        "É RECONHECÍVEL como uma latrina romana (banco de mármore com furos em formato de chave, canal de água embaixo).",
        "Não parece um contêiner/caixa genérica.",
        "Texto 'LATRINA' legível (label opcional mas ajuda contexto).",
        "Tamanho suficiente (mín 500px largura) para ser visualmente impactante.",
    ],
    "gold_coin_drop": [
        "Moeda visivelmente DOURADA com detalhes (SPQR, $, marca de cunho).",
        "Tamanho adequado (raio mín 130px) — não parece bolinha.",
        "Animação de queda + spin + flash visíveis.",
    ],
    "cinematic_title": [
        "Texto NÃO QUEBRA em duas linhas estranhas (verificar whiteSpace nowrap + font-size responsivo).",
        "Background fullscreen suprime captions sobrepostas.",
        "Tipografia serif elegante (Georgia/Playfair).",
        "Subtítulo (se houver) coerente com o título principal — sem pleonasmos.",
    ],
    "code_document": [
        "Documento legível, contraste forte (texto escuro em bege).",
        "Animação de typewriter SE o texto for longo (não estático).",
        "Highlight na palavra-chave (ex: 'OBJETIVA') deve ter cor sólida visível.",
        "Não cobre rosto do speaker (top-half da tela).",
    ],
    "highlighter_underline": [
        "Posicionado sob a palavra/texto correto (não solto na tela).",
        "Cor de destaque visível (cobre/amarelo).",
    ],
    "split_comparison": [
        "Cards posicionados em SAFE ZONE (top OU bottom — NUNCA no meio cobrindo rosto).",
        "Divider central (VS, ↔, etc) PROPORCIONAL — não maior que os cards.",
        "Divider ALINHADO entre os dois cards (não desalinhado).",
        "Ícones reconhecíveis (use heroicons-style icons inline SVG).",
        "Labels legíveis com contraste forte.",
    ],
    "merge_into_keyword": [
        "Texto destacado, fundo de contraste forte.",
        "Posicionado em zona segura (top ou bottom).",
    ],
    "stf_stamp": [
        "Brasão reconhecível como SUPREMO TRIBUNAL FEDERAL (balança da justiça + estrelas + texto circular).",
        "Balança DETALHADA — não desenhada como palitos toscos.",
        "Letras legíveis (texto curvo + texto central).",
        "Tamanho impactante mas não cobre rosto.",
    ],
    "ticker_resp": [
        "Texto legível (fonte ≥ 24px), contraste forte com background.",
        "Background semi-opaco para garantir leitura.",
        "Posicionado em zona segura (sidebar/edge).",
    ],
    "scale_of_justice": [
        "Balança VISUALMENTE BONITA — não pixelada/tosca, com detalhes (correntes, pratos curvos, base decorada).",
        "Posicionada na parte inferior do frame, não cobrindo o rosto.",
        "Desequilíbrio claramente visível (lado pesado para baixo, lado leve para cima).",
        "Labels legíveis nos pratos.",
        "Considere mostrar o que está em cada prato (moedas no lado pesado).",
    ],
    "context_tags": [
        "Pills bem espaçados, não amontoados.",
        "Contraste forte (texto cobre em fundo escuro).",
        "Posicionados em row no top, fora da face zone.",
    ],
    "counter_number": [
        "Número GIGANTE (≥ 300px font-size).",
        "Animação de count-up visível (de 0 ao target).",
        "Fundo fullscreen suprime captions.",
        "Subtítulo opcional com contexto.",
    ],
    "data_network": [
        "DEVE ser INTUITIVO — mostrar dados FLUINDO entre fontes reconhecíveis (Receita, Bancos, etc), não apenas dots abstratos.",
        "Use ÍCONES de instituições (heroicons building-library, banknotes, etc).",
        "Animação de partículas/dots fluindo nas linhas para mostrar movimento de dados.",
        "Ponto central de convergência (lupa, magnifying glass) com label 'CRUZAMENTO'.",
    ],
    "mismatch_cards": [
        "Card 'declarado' em fundo claro com texto ESCURO (NÃO branco no branco — verificar contraste!).",
        "Card 'patrimônio' em fundo escuro com texto claro/dourado.",
        "Texto 'INCOMPATÍVEL' DENTRO de seu container (verificar bounds — usar HTML não SVG text).",
        "Seta visível conectando os dois cards.",
        "Cards posicionados em corners opostos (top-left + bottom-right) para contraste visual.",
    ],
    "tributavel_stamp": [
        "Stamp grande, rotacionado, com border duplo (estilo carimbo).",
        "Cor cobre escuro sobre fundo bege.",
    ],
    "warm_shift_pivot": [
        "Color shift radial cobre claramente visível.",
        "Curto (< 1s) — não persistente.",
        "Marca a transição problema → solução.",
    ],
    "tribotax_shield": [
        "Escudo se desenha (stroke draw-on) depois preenche.",
        "Check verde aparece dentro com pop.",
        "Documentos orbitando (se ativado).",
        "Label PROTEÇÃO DOCUMENTAL legível.",
    ],
    "comment_bubble_cta": [
        "NÃO USAR fullscreen overlay (verde/dark) — bubble deve aparecer SOBRE o vídeo do speaker.",
        "Bubble destacado com keyword (ex: PATRIMÔNIO) bem grande.",
        "Seta apontando pra baixo (indicando comentários).",
        "EVITAR pleonasmos como 'COMENTE NOS COMENTÁRIOS' — se incluir texto adicional, deve agregar info real (ex: 'arrasta pra cima', 'eu envio pra você').",
    ],
}

# ═══════════════════════════════════════════════════════════════════════
# REGRAS GERAIS QUE SEMPRE DEVEM SER CHECADAS
# ═══════════════════════════════════════════════════════════════════════
GENERAL_RULES = """
## REGRAS GERAIS — verificar para CADA frame

### 1. Bounds & posicionamento
- Texto está DENTRO do seu container (rect, badge, balão)? Verificar bounds explicitamente.
- Elementos não saem da safe area (1080×1920, padding 60px nas bordas)?
- Não cobre o rosto do speaker (zona y=240-1100) salvo se for fullscreen intencional?

### 2. Contraste & legibilidade
- Texto claro em fundo escuro OU texto escuro em fundo claro? Nunca claro em claro ou escuro em escuro.
- Borders tem contraste suficiente?
- Sombras/glow ajudam a destacar (não atrapalham)?

### 3. Coerência narrativa
- A animação faz SENTIDO no momento do voice-over? (ex: pergaminho NÃO deve aparecer durante o gancho moderno)
- Texto adicional NÃO é pleonasmo (ex: 'COMENTE NOS COMENTÁRIOS' = ruim)?
- Elementos visuais REPRESENTAM o que o speaker está falando?

### 4. Qualidade dos SVGs
- Ícones desenhados na mão parecem amadores → SUBSTITUA por SVG paths de heroicons (https://heroicons.com), lucide (https://lucide.dev), ou tabler (https://tabler-icons.io). Estas bibliotecas têm paths copiáveis prontos pra uso inline.
- Componentes complexos (busto, balança, latrina) devem ter detalhes suficientes pra serem RECONHECÍVEIS.
- Use gradientes, sombras, e detalhes (correntes em balança, furos em latrina, louros em busto romano).

### 5. Animações apropriadas
- Animação de entry suave (spring/ease-out)?
- Animação de exit clean (fade ou slide)?
- Pulso/movimento contínuo para CTAs (não estáticos)?

### 6. Sobreposição com captions
- Se overlay é FULLSCREEN, está em FULLSCREEN_OVERLAY_KINDS? (suprime captions)
- Se overlay é PARCIAL, está em zona que NÃO conflita com captions (que ficam no bottom-third)?
"""

# ═══════════════════════════════════════════════════════════════════════
# POSTMORTEM — porque erros passam
# ═══════════════════════════════════════════════════════════════════════
POSTMORTEM = """
## POR QUE ERROS PASSAM (e como evitar)

Análise de falhas reais que escaparam de revisões anteriores:

| Erro que passou | Causa raiz | Como evitar agora |
|---|---|---|
| Texto sai do container (ex: INCOMPATÍVEL fora do retângulo) | Não checou bounds explicitamente | Para CADA elemento com border, perguntar: 'o texto interno cabe?' |
| Texto branco em fundo branco/claro | Não checou contraste | Para CADA texto, perguntar: 'o que está atrás? tem contraste?' |
| Pleonasmo 'COMENTE NOS COMENTÁRIOS' | Foco só em visual, não em copy | Ler o texto adicional EM VOZ ALTA — soa redundante? |
| Anim. histórica durante hook moderno | Não validou narrativa por timestamp | Pra cada animação, ler o caption ATIVO simultâneo — fazem sentido juntos? |
| SVG bust desenhada na mão parece ânfora | Tentou criar paths complexos do zero | USE icon libraries! heroicons.com, lucide.dev. Copy-paste o path real. |
| Latrina não parece latrina | Símbolo abstrato sem reconhecibilidade | Pesquise referências reais (banco de mármore + furo em formato chave + canal de água) |
| Balança/STF parecem palitos | Subdimensionou detalhes | Adicione correntes, pratos curvos, decorações de base |
| Cruzamento de dados parece rede genérica | Não usou ícones representativos | Use ÍCONES de instituições reais — Receita, Bancos, Cartórios |

**REGRA DE OURO**: Se uma animação não é IMEDIATAMENTE reconhecível como o que deveria ser (sem precisar do label de texto), está ruim e precisa de mais detalhes/melhor SVG.
"""


def extract_frame(proxy_path: Path, time_s: float, output_path: Path) -> bool:
    subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{time_s:.2f}", "-i", str(proxy_path),
         "-vframes", "1", "-q:v", "2", str(output_path)],
        capture_output=True
    )
    return output_path.exists()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proxy", required=True, type=Path)
    p.add_argument("--plan", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--agent", action="store_true")
    args = p.parse_args()

    if not args.proxy.exists():
        sys.exit(f"❌ Proxy not found: {args.proxy}")
    if not args.plan.exists():
        sys.exit(f"❌ Plan not found: {args.plan}")

    output_dir = args.output_dir
    frames_dir = output_dir / "_review_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    plan = json.loads(args.plan.read_text())
    overlays = plan.get("rich_overlays", [])
    if not overlays:
        print("⚠️  No rich_overlays in plan — skipping visual review.")
        sys.exit(0)

    print(f"🎬 Extracting review frames from {args.proxy.name}...")

    extracted = []
    for i, ov in enumerate(overlays):
        kind = ov.get("kind", "unknown")
        start = float(ov["start"])
        end = float(ov["end"])
        mid = (start + end) / 2
        sample_times = [mid] if (end - start) < 2.0 else [start + (end - start) * 0.25, mid, start + (end - start) * 0.75]

        for j, t in enumerate(sample_times):
            suffix = "" if len(sample_times) == 1 else f"_p{j+1}"
            fname = frames_dir / f"{i:02d}_{kind}{suffix}_t{t:.1f}s.jpg"
            if extract_frame(args.proxy, t, fname):
                extracted.append({"overlay_idx": i, "kind": kind, "time_s": t, "frame_path": str(fname)})
                print(f"  ✓ {kind} @ {t:.1f}s")

    # Detect iteration count (look for previous review state file)
    state_file = output_dir / ".visual_review_iteration"
    iteration = 1
    if state_file.exists():
        try:
            iteration = int(state_file.read_text().strip()) + 1
        except Exception:
            iteration = 1
    state_file.write_text(str(iteration))

    # Write enriched brief with per-kind QA criteria
    brief_path = output_dir / "visual_review_brief.md"
    lines = [
        f"# Visual Review — STRICT Director-Level QA — Iteração #{iteration}\n",
        "**Você (Claude Code agent) é responsável pela qualidade visual final.**",
        "Não passe pra revisão humana até que CADA item da checklist abaixo esteja validado.\n",
        "## LOOP ITERATIVO — OBRIGATÓRIO",
        "",
        "1. Revise CADA frame extraído usando o `Read` tool.",
        "2. Para cada problema, conserte em `<remotion>/src/components/RichOverlays.tsx` + ajuste `edit_plan.json` se preciso.",
        "3. Re-renderize o proxy:",
        "   ```bash",
        "   cp <output>/edit_plan.json <remotion-dir>/src/edit_plan.json  # sincroniza",
        "   cd <remotion-dir> && npx remotion render Reel ../proxy.mp4 --scale=0.5 --jpeg-quality=80 --concurrency=4 --overwrite",
        "   ```",
        "4. Re-rode `visual_review.py` — vai gerar BRIEF ITERAÇÃO #N+1 com novos frames.",
        "5. **REPITA** até NENHUM problema visual remanescer (max 5 iterações).",
        "6. Só ENTÃO apresente o proxy ao humano.\n",
        "## RECURSOS DE ÍCONES — REGRA DURA (não negociável)\n",
        "**NUNCA desenhe figura/objeto/ícone reconhecível em SVG na mão. Sempre nessa ordem:**\n",
        "1. **PRIMEIRO — banco PNG local** (`/Users/gabriel/Documents/PNGS PARA EDICAO/`)",
        "   - LEIA `INDEX.md` integralmente (226 ícones, 8 categorias) antes de pensar em SVG.",
        "   - Busca por keywords semânticas: 'balanca', 'justi', 'estatua', 'busto', 'dinheiro', 'doc', 'mao'.",
        "   - Copie pra `<remotion>/public/icons/` e use `<Img src={staticFile('icons/<id>.png')} />`.",
        "",
        "2. **SEGUNDO — Wikimedia Commons + bibliotecas SVG**",
        "   - Brasões oficiais, bandeiras, símbolos institucionais → Wikimedia (PD/CC).",
        "   - Ícones genéricos → heroicons.com, lucide.dev, tabler-icons.io, svgrepo.com.",
        "   - Use `WebFetch` pra pegar o asset.",
        "",
        "3. **TERCEIRO — pedir ao usuário**",
        "   - Se não achou em (1) nem (2), PARE e peça PNG novo. Não tente desenhar.",
        "",
        "4. **ÚLTIMO recurso — SVG na mão**",
        "   - Só para formas geométricas puras (linhas, retângulos, gradientes, framing).",
        "   - PROIBIDO para: figura humana, animal, busto, balança, brasão, objeto reconhecível.",
        "",
        "**Por que esta regra é dura:** SVG cru sai amador (balança vira palitos, busto vira ânfora, brasão vira selo genérico). O feedback do usuário foi explícito: 'a balança ficou bem feia', 'a logo do STF não ficou legal'. Erro repetido = falha grave.\n",
        "Veja `references/icon-resources.md` (workflow completo).\n",
        f"## Frames extraídos: {len(extracted)}\n",
        "Para CADA overlay listado abaixo:",
        "1. Use o `Read` tool no arquivo do frame.",
        "2. Aplique a checklist específica do kind (abaixo).",
        "3. Aplique as REGRAS GERAIS.",
        "4. Se algo falhar, conserte em `<remotion>/src/components/RichOverlays.tsx` e re-renderize.",
        "5. Re-rode `visual_review.py` e revise novamente. ITERE até passar.\n",
        GENERAL_RULES,
        POSTMORTEM,
        "## QA por overlay\n",
    ]

    seen_kinds = set()
    for f in extracted:
        kind = f["kind"]
        criteria = QA_CRITERIA_BY_KIND.get(kind, ["Sem critérios específicos — aplicar regras gerais."])
        lines.append(f"### `{kind}` @ {f['time_s']:.1f}s")
        lines.append(f"Frame: `{f['frame_path']}`\n")
        if kind not in seen_kinds:
            lines.append("**Checklist específica:**")
            for c in criteria:
                lines.append(f"- [ ] {c}")
            seen_kinds.add(kind)
        lines.append("")

    lines.append("\n## Quando aprovar\n")
    lines.append("- TODOS os frames passam na checklist específica.")
    lines.append("- TODOS passam nas regras gerais (bounds, contraste, narrativa, qualidade SVG).")
    lines.append("- Animações que tinham problemas conhecidos (texto out of bounds, white-on-white, pleonasmos) foram corrigidas.\n")
    lines.append("Só ENTÃO chame o humano pra revisão final.")

    brief_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📋 Brief escrito: {brief_path}")
    print(f"📂 Frames: {frames_dir}")

    if args.agent:
        print("\n[AGENT MODE] Leia visual_review_brief.md e revise CADA frame com a checklist específica.")
        sys.exit(2)


if __name__ == "__main__":
    main()

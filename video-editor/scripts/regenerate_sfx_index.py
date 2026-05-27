#!/usr/bin/env python3
"""
regenerate_sfx_index.py — Regera assets/sfx_index.json a partir do manifest.json
da pasta SFX (/Users/gabriel/Documents/EFEITOS SONOROS/).

Mantém compat com edit_plan.json antigo (categorias UPPERCASE) mapeando as
categorias numeradas do novo manifest pra nomes legados.

Uso:
    python3 regenerate_sfx_index.py [--sfx-root <path>] [--output <path>]
"""
import argparse, json, sys
from pathlib import Path

# Mapeamento categoria nova (numerada) → categoria legada (uppercase)
CATEGORY_MAP = {
    "01_woosh":     "WOOSH",
    "02_click":     "CLICK",
    "03_digital":   "DIGITAL",
    "04_transicao": "TRANSIÇÃO",
    "05_camera":    "CAMERA",
    "06_plim":      "PLIM",
    "07_riser":     "RISER",
    "08_variaveis": "VARIAVEIS",
    "09_ambiente":  "AMBIENTE",
    "10_cinematica":"CINEMATICA",
    "11_rolagem":   "ROLAGEM",
    "12_glitch":    "GLITCH",
    "13_teclado":   "TECLADO",
    "14_dinheiro":  "DINHEIRO",
    "15_estalo":    "ESTALO",
    "16_contagem":  "CONTAGEM",
    "17_pops":      "POPS",
    "18_boom":      "BOOM",
    "19_notification": "NOTIFICATION",
    "20_drum":      "DRUM",
    "21_glass-break": "GLASS_BREAK",
    "22_applause":  "APPLAUSE",
    "23_horror":    "HORROR",
    "24_meme-fail": "FAIL",
    "25_magic":     "MAGIC",
    "26_heartbeat": "HEARTBEAT",
}

# Descrições + use_cases por categoria legada
CATEGORY_DESCRIPTIONS = {
    "WOOSH": ("Whooshes, swooshes, transições rápidas. Use em cortes secos, swipes, pans.",
              ["cut", "swipe_in", "swipe_out", "overlay_enter", "scene_change"]),
    "CLICK": ("Cliques de UI/botões. Use em CTAs, checklist, taps.",
              ["ui", "cta", "checklist", "button"]),
    "DIGITAL": ("Impactos digitais/UI. Use em overlays digitais, tech reveal.",
                ["ui_transition", "digital_overlay", "tech", "swipe"]),
    "TRANSIÇÃO": ("Transições genéricas. Use entre cenas.", ["transition", "scene_change"]),
    "CAMERA": ("Cliques de obturador. Use em reveal visual, zoom-in.",
               ["reveal", "photo", "product_shot", "zoom_reveal"]),
    "PLIM": ("Plims, sparkles, chimes. Use em destaque de números, checks, revelações positivas.",
             ["highlight", "checklist", "number_stat", "notification"]),
    "RISER": ("Uplifters, build-ups antes de clímax/drop.",
              ["hook_buildup", "intro", "before_reveal", "tension"]),
    "VARIAVEIS": ("SFX diversos — épico, error, idea moment.",
                  ["special", "epic_impact", "error_moment", "idea_moment"]),
    "AMBIENTE": ("Ambientes/atmosferas/drones. Use em b-roll, intros.",
                 ["ambient", "broll", "intro", "outdoor"]),
    "CINEMATICA": ("Hits cinematográficos — impactos grandes, climax, CTA final.",
                   ["impact", "dramatic_reveal", "cta", "climax"]),
    "ROLAGEM": ("Sons mecânicos de rolagem/engrenagem.",
                ["list_scroll", "count_up", "progress", "mechanism"]),
    "GLITCH": ("Glitches digitais. Use em pattern interrupts, virada de narrativa.",
               ["glitch_transition", "problem_moment", "pattern_interrupt"]),
    "TECLADO": ("Digitação. Use em typing text, kinetic text.",
                ["typing", "data_entry", "work_scene", "kinetic_text"]),
    "DINHEIRO": ("Cash register, ka-ching. Use em menção de valores, savings.",
                 ["money_reveal", "financial", "savings", "revenue"]),
    "ESTALO": ("Estalos/snaps curtos. Use em marcação rítmica, ênfase em palavras.",
               ["cut_accent", "word_emphasis", "rhythm"]),
    "CONTAGEM": ("Tick-tock, countdown. Use antes de revelar estatísticas.",
                 ["countdown", "number_reveal", "stat", "timer"]),
    "POPS": ("Pop-ups curtos. Use em aparição de elementos, balões.",
             ["overlay_appear", "bubble", "popup"]),
    "BOOM": ("Boom impacts, bass drops. Use em drops dramáticos, explosões.",
             ["drop", "explosion", "dramatic_impact"]),
    "NOTIFICATION": ("Notifications, success/error chimes. Use em UI feedback.",
                     ["notification", "ui_feedback", "success", "error"]),
    "DRUM": ("Drum hits, kicks, snares.",
             ["drum_hit", "rhythm_accent", "percussion"]),
    "GLASS_BREAK": ("Vidro quebrando.",
                    ["shatter", "break", "destruction"]),
    "APPLAUSE": ("Aplausos, claps.",
                 ["celebration", "applause", "victory"]),
    "HORROR": ("Horror stingers, jump scares.",
               ["horror", "suspense", "jump_scare"]),
    "FAIL": ("Sad trombone, meme fail.",
             ["fail", "negative_moment", "meme"]),
    "MAGIC": ("Magic, sparkle, twinkle.",
              ["magic", "sparkle", "twinkle"]),
    "HEARTBEAT": ("Heartbeat, pulse.",
                  ["tension", "anticipation", "fear"]),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sfx-root", default="/Users/gabriel/Documents/EFEITOS SONOROS")
    p.add_argument("--output", default=str(Path(__file__).parent.parent / "assets" / "sfx_index.json"))
    args = p.parse_args()

    root = Path(args.sfx_root)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"❌ manifest.json não encontrado em {manifest_path}")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Group assets by legacy category
    by_cat: dict[str, list[str]] = {legacy: [] for legacy in CATEGORY_MAP.values()}
    duration_sum: dict[str, float] = {legacy: 0.0 for legacy in CATEGORY_MAP.values()}

    for asset in manifest.get("assets", []):
        cat_new = asset.get("category")
        legacy = CATEGORY_MAP.get(cat_new)
        if not legacy:
            continue
        by_cat[legacy].append(asset["path"])
        duration_sum[legacy] += float(asset.get("duration_sec", 0))

    # Build new sfx_index.json structure
    out = {
        "root": str(root),
        "total_files": sum(len(files) for files in by_cat.values()),
        "categories": {},
    }
    for legacy, files in by_cat.items():
        if not files:
            continue
        desc, use_cases = CATEGORY_DESCRIPTIONS.get(legacy, (f"Categoria {legacy}", ["general"]))
        avg_ms = int((duration_sum[legacy] / len(files)) * 1000) if files else 0
        out["categories"][legacy] = {
            "description": desc,
            "use_cases": use_cases,
            "files": sorted(files),
            "count": len(files),
            "duration_ms_avg": avg_ms,
        }

    Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Regenerado: {args.output}")
    print(f"  Categorias: {len(out['categories'])}")
    print(f"  Total arquivos: {out['total_files']}")
    for cat, data in out["categories"].items():
        print(f"  {cat}: {data['count']} files")


if __name__ == "__main__":
    main()

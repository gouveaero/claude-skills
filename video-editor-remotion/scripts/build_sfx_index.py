#!/usr/bin/env python3
"""
build_sfx_index.py — Utilitário video-editor
Escaneia a pasta de efeitos sonoros e gera assets/sfx_index.json.

Uso:
  python build_sfx_index.py [--sfx-root "/Users/gabriel/Documents/EFEITOS SONOROS"]
                             [--output /path/to/sfx_index.json]
"""
import argparse, json, subprocess, os
from pathlib import Path

SFX_ROOT_DEFAULT = "/Users/gabriel/Documents/EFEITOS SONOROS"
INDEX_DEFAULT = str(Path(__file__).parent.parent / "assets" / "sfx_index.json")

# Metadados por categoria: descrição e use_cases
CATEGORY_META = {
    "AMBIENTE": {
        "description": "Paisagens sonoras ambientes. Use em cenas externas, b-roll de locação, introduções.",
        "use_cases": ["ambient", "broll", "intro", "outdoor"]
    },
    "CAMERA": {
        "description": "Sons de obturador, flash e câmera. Use em revelações visuais, zoom-in em produto/rosto.",
        "use_cases": ["reveal", "photo", "product_shot", "zoom_reveal"]
    },
    "CINEMATICA": {
        "description": "Hits cinematográficos épicos. Use em momentos de impacto máximo, revelações dramáticas, CTAs finais.",
        "use_cases": ["impact", "dramatic_reveal", "cta", "climax"]
    },
    "CLICK": {
        "description": "Cliques de mouse e botão. Use em elementos de UI, calls-to-action, check-list items.",
        "use_cases": ["ui", "cta", "checklist", "button"]
    },
    "CONTAGEM": {
        "description": "Contagem digital. Use em countdowns, sequências numéricas, antes de revelar estatísticas.",
        "use_cases": ["countdown", "number_reveal", "stat", "timer"]
    },
    "DIGITAL": {
        "description": "Sons de interface digital, whooshes de UI. Use em transições de tela, overlays digitais.",
        "use_cases": ["ui_transition", "digital_overlay", "tech", "swipe"]
    },
    "DINHEIRO": {
        "description": "Caixa registradora, dinheiro. Use em menção a valores, resultados financeiros, saving.",
        "use_cases": ["money_reveal", "financial", "savings", "revenue"]
    },
    "ESTALO": {
        "description": "Estalo/snap curto. Use em marcação rítmica de cortes, enfatizar palavras-chave.",
        "use_cases": ["cut_accent", "word_emphasis", "rhythm"]
    },
    "GLITCH": {
        "description": "Efeito de glitch/interferência. Use em transições criativas, efeito de 'problema -> solução'.",
        "use_cases": ["glitch_transition", "problem_moment", "pattern_interrupt"]
    },
    "PLIM": {
        "description": "Notificação/highlight curto (15 variações). Use em destaques de números, check-marks, itens de lista.",
        "use_cases": ["highlight", "checklist", "number_stat", "notification"]
    },
    "POPS": {
        "description": "Pop-up sonoro. Use em aparição de elementos, balões de texto, overlays.",
        "use_cases": ["overlay_appear", "bubble", "popup"]
    },
    "RISER": {
        "description": "Build-up de tensão crescente. Use no início (antes do hook), antes de grandes revelações.",
        "use_cases": ["hook_buildup", "intro", "before_reveal", "tension"]
    },
    "ROLAGEM": {
        "description": "Sons mecânicos de rolagem/engrenagem. Use em contagens, listas longas, progressão.",
        "use_cases": ["list_scroll", "count_up", "progress", "mechanism"]
    },
    "TECLADO": {
        "description": "Digitação de teclado. Use em cenas de trabalho, apresentação de dados, typing text.",
        "use_cases": ["typing", "data_entry", "work_scene", "kinetic_text"]
    },
    "TRANSIÇÃO": {
        "description": "Transições longas de ar. Use em mudanças de cena longas, viradas de ato.",
        "use_cases": ["scene_change", "act_transition", "long_cut"]
    },
    "VARIAVEIS": {
        "description": "SFX especiais diversos (impacto épico, braaam, XP error, bom ideia). Use case a case.",
        "use_cases": ["special", "epic_impact", "error_moment", "idea_moment"]
    },
    "WOOSH": {
        "description": "Whoosh/swipe de movimento (20+ variações). Use em cortes secos, entradas/saídas de overlays, pan.",
        "use_cases": ["cut", "swipe_in", "swipe_out", "overlay_enter", "overlay_exit", "scene_change"]
    }
}

AUDIO_EXTENSIONS = {".wav", ".mp3", ".aac", ".m4a", ".ogg", ".flac"}

def get_duration_ms(filepath):
    """Obtém duração em ms via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        return int(float(data["format"]["duration"]) * 1000)
    except Exception:
        return None

def scan_sfx_root(sfx_root):
    """Escaneia pasta raiz e agrupa por categoria (subpasta de primeiro nível)."""
    sfx_root = Path(sfx_root)
    categories = {}

    for item in sfx_root.iterdir():
        if not item.is_dir():
            continue
        category = item.name.upper()
        # Ignora pastas de sistema
        if category.startswith("__MACOSX") or category.startswith("."):
            continue

        files = []
        for f in item.rglob("*"):
            if f.suffix.lower() in AUDIO_EXTENSIONS and not f.name.startswith("._"):
                rel_path = str(f.relative_to(sfx_root))
                files.append(rel_path)

        if not files:
            continue

        # Amostra de duração (máx 5 arquivos)
        durations = []
        for rel in files[:5]:
            dur = get_duration_ms(sfx_root / rel)
            if dur:
                durations.append(dur)
        avg_dur = int(sum(durations) / len(durations)) if durations else None

        meta = CATEGORY_META.get(category, {
            "description": f"Efeitos de categoria {category}.",
            "use_cases": ["general"]
        })

        categories[category] = {
            "description": meta["description"],
            "use_cases": meta["use_cases"],
            "files": sorted(files),
            "count": len(files),
            "duration_ms_avg": avg_dur
        }

    return categories

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sfx-root", default=SFX_ROOT_DEFAULT)
    p.add_argument("--output", default=INDEX_DEFAULT)
    args = p.parse_args()

    sfx_root = args.sfx_root
    if not Path(sfx_root).exists():
        print(f"Erro: pasta SFX não encontrada: {sfx_root}")
        return

    print(f"Escaneando: {sfx_root}")
    categories = scan_sfx_root(sfx_root)

    index = {
        "root": sfx_root,
        "total_files": sum(c["count"] for c in categories.values()),
        "categories": categories
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    print(f"Índice gerado: {out_path}")
    print(f"  Categorias: {len(categories)}")
    print(f"  Total de arquivos: {index['total_files']}")
    for cat, data in sorted(categories.items()):
        print(f"  - {cat}: {data['count']} arquivos")

if __name__ == "__main__":
    main()

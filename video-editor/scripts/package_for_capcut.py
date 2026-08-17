#!/usr/bin/env python3
"""
package_for_capcut.py — Cria pasta `capcut_package/` autocontida com brutos
renomeados por cena, hooks separados, SFX selecionados e preview Remotion.
Gera também um plano "package-aware" + sfx_index ad-hoc apontando pros caminhos
da pasta organizada, prontos pro capcut_draft_builder.

Estrutura criada:
    <pkg_root>/capcut_package/
    ├── 01_brutos_hooks/      ← brutos contendo as primeiras tomadas (gancho-*)
    ├── 02_brutos_cenas/      ← brutos das cenas principais, renomeados por contexto
    ├── 03_sfx/               ← cópias dos SFX usados (uma por arquivo único)
    ├── 04_animacoes/preview_com_overlays.mp4   ← render Remotion (proxy)
    └── README.md

A timeline CapCut referencia caminhos ABSOLUTOS dentro dessa pasta — o usuário
pode mover/levar a pasta inteira; se mover, na primeira abertura do CapCut o
"Link media" reaponta tudo.

Uso:
    python3 package_for_capcut.py \\
        --plan        <output>/edit_plan.json \\
        --brutos-dir  <input>/                    # pasta com os brutos originais
        --proxy       <output>/proxy.mp4 \\
        --sfx-index   ~/.claude/skills/video-editor/assets/sfx_index.json \\
        --sfx-root    "$SFX_ROOT" \\
        --reel-name   TriboTax_R1_Pecunia \\
        --pkg-root    <input>/                    # onde criar o capcut_package/
        --out-plan    /tmp/edit_plan_packaged.json
        --out-sfx     /tmp/sfx_index_packaged.json
"""
import argparse, json, os, random, re, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path


def _ffmpeg_bin() -> str:
    """Acha o ffmpeg mais completo disponível (homebrew full prefer)."""
    for p in ("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg", "ffmpeg"):
        try:
            r = subprocess.run([p, "-version"], capture_output=True, timeout=2)
            if r.returncode == 0:
                return p
        except Exception:
            pass
    return "ffmpeg"


def _is_hevc(src: Path) -> bool:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "default=nw=1:nk=1", str(src)],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip().lower() in ("hevc", "h265")
    except Exception:
        return False


def transcode_to_h264_all_keyframe(src: Path, dest: Path) -> bool:
    """Reencoda pra H.264 com GOP=1 (todo frame é keyframe → seek frame-accurate
    no CapCut). Sem isso, CapCut sofre keyframe slop em brutos HEVC (~1s drift
    entre vídeo e áudio quando source_in cai entre keyframes).
    Preset 'medium' = bom balanço entre tempo e qualidade. Adicionado BT.709
    metadata pra evitar adivinhação BT.601 → highlights estourados.
    """
    ff = _ffmpeg_bin()
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff, "-y", "-v", "error",
        "-i", str(src),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-g", "1", "-keyint_min", "1", "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(dest),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ❌ transcode falhou: {r.stderr[-300:]}", file=sys.stderr)
        return False
    # Verifica integridade decodificando 30 frames (~1s). Captura arquivos
    # corrompidos por interrupção (encode foi morto no meio etc).
    verify = subprocess.run(
        [ff, "-v", "error", "-i", str(dest), "-frames:v", "30", "-f", "null", "-"],
        capture_output=True, text=True
    )
    if verify.returncode != 0 or "Invalid NAL" in verify.stderr or "Error splitting" in verify.stderr:
        print(f"  ❌ output corrompido: {dest.name}", file=sys.stderr)
        dest.unlink(missing_ok=True)
        return False
    return True

LEGACY_TO_FOLDER = {
    "WOOSH":"01_woosh","CLICK":"02_click","DIGITAL":"03_digital","TRANSIÇÃO":"04_transicao",
    "CAMERA":"05_camera","PLIM":"06_plim","RISER":"07_riser","VARIAVEIS":"08_variaveis",
    "AMBIENTE":"09_ambiente","CINEMATICA":"10_cinematica","ROLAGEM":"11_rolagem",
    "GLITCH":"12_glitch","TECLADO":"13_teclado","DINHEIRO":"14_dinheiro","ESTALO":"15_estalo",
    "CONTAGEM":"16_contagem","POPS":"17_pops","BOOM":"18_boom","NOTIFICATION":"19_notification",
    "DRUM":"20_drum","GLASS_BREAK":"21_glass-break","APPLAUSE":"22_applause","HORROR":"23_horror",
    "FAIL":"24_meme-fail","MAGIC":"25_magic","HEARTBEAT":"26_heartbeat",
}


def slug(text: str, maxlen: int = 45) -> str:
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", text.lower()).strip("-")
    return s[:maxlen]


def _cut_slug(cut: dict) -> str:
    """Slug de um cut: prioriza campo 'slug', cai em 'rationale', cai em 'clip'."""
    if "slug" in cut and cut["slug"]:
        return cut["slug"]
    raw = cut.get("rationale") or cut.get("clip") or "scene"
    return slug(raw)

def derive_bruto_scene_name(cuts_using_bruto: list) -> str:
    """Pega o slug com prefixo mais comum entre os cuts pra nomear o bruto."""
    if not cuts_using_bruto:
        return "scene"
    slugs = [_cut_slug(c) for c in cuts_using_bruto]
    # Prefixo comum (até o segundo "-")
    prefixes = set()
    for s in slugs:
        parts = s.split("-")
        prefixes.add("-".join(parts[:2]) if len(parts) >= 2 else parts[0])
    if len(prefixes) == 1:
        return slug(next(iter(prefixes)))
    # Sem prefixo único: usa o slug do PRIMEIRO cut
    return slug(slugs[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan",       required=True, type=Path, help="edit_plan.json")
    ap.add_argument("--brutos-dir", required=True, type=Path, help="Pasta com os brutos originais")
    ap.add_argument("--proxy",      required=False, type=Path, help="proxy.mp4 do Remotion")
    ap.add_argument("--sfx-index",  required=True, type=Path, help="sfx_index.json")
    ap.add_argument("--sfx-root",   default=Path(os.environ.get("SFX_ROOT", "$SFX_ROOT")), type=Path)
    ap.add_argument("--reel-name",  required=True, help="Usado como seed da seleção de SFX (e nome do draft)")
    ap.add_argument("--pkg-root",   required=True, type=Path, help="Onde criar capcut_package/")
    ap.add_argument("--out-plan",   default=Path("/tmp/edit_plan_packaged.json"), type=Path)
    ap.add_argument("--out-sfx",    default=Path("/tmp/sfx_index_packaged.json"), type=Path)
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    sfx_index = json.loads(args.sfx_index.read_text(encoding="utf-8"))

    pkg = args.pkg_root / "capcut_package"
    for sub in ("01_brutos_hooks", "02_brutos_cenas", "03_sfx", "04_animacoes"):
        (pkg / sub).mkdir(parents=True, exist_ok=True)

    # ── 1. Brutos: agrupar por arquivo, renomear por cena ──────────────────────
    by_bruto: dict[str, list] = defaultdict(list)
    for cut in plan["v1_main"]:
        by_bruto[cut["clip"]].append(cut)

    rename_map: dict[str, str] = {}
    hook_idx = cena_idx = 0
    for bruto_file in sorted(by_bruto.keys(), key=lambda f: min(plan["v1_main"].index(c) for c in by_bruto[f])):
        cuts = by_bruto[bruto_file]
        is_hook = any(_cut_slug(c).startswith("gancho") or _cut_slug(c).startswith("hook") for c in cuts)
        scene_name = "ganchos-" + derive_bruto_scene_name(cuts) if is_hook else derive_bruto_scene_name(cuts)
        if is_hook:
            hook_idx += 1
            dest = pkg / "01_brutos_hooks" / f"{hook_idx:02d}_{scene_name}.mp4"
        else:
            cena_idx += 1
            dest = pkg / "02_brutos_cenas" / f"{cena_idx:02d}_{scene_name}.mp4"
        src = args.brutos_dir / bruto_file
        if not src.exists():
            print(f"  ❌ Bruto não encontrado: {src}", file=sys.stderr)
            continue
        # HEVC com GOP longo causa dessincronia no CapCut quando source_in cai
        # entre keyframes. Transcoda pra H.264 all-I-frame se for HEVC.
        # Brutos H.264 já com short GOP passam direto (copy).
        if _is_hevc(src):
            print(f"  ↻ transcode HEVC→H.264 all-I: {bruto_file}")
            if not transcode_to_h264_all_keyframe(src, dest):
                print(f"  ⚠ Transcode falhou, copiando original (sync pode quebrar)",
                      file=sys.stderr)
                shutil.copy2(src, dest)
        else:
            shutil.copy2(src, dest)
        rename_map[bruto_file] = str(dest)
        cut_ids = [plan["v1_main"].index(c) + 1 for c in cuts]
        sz_mb = dest.stat().st_size / 1024 / 1024
        print(f"  ✓ {dest.parent.name}/{dest.name}  [{sz_mb:.1f} MB, cuts {cut_ids}]")

    # ── 2. SFX: reproduzir seleção seeded e copiar arquivos únicos ─────────────
    categories = sfx_index.get("categories", {})
    sfx_paths_in_pkg: dict[tuple, str] = {}  # (cat, file_rel) → abs path no pkg
    pack_sfx_index = {"root": str(pkg / "03_sfx"), "total_files": 0, "categories": {}}

    for sfx_item in plan.get("sfx", []):
        cat = sfx_item.get("category", "").upper()
        files = categories.get(cat, {}).get("files", [])
        if not files:
            print(f"  ⚠️  SFX category sem arquivos: {cat}")
            continue
        rng = random.Random()
        rng.seed(args.reel_name + cat)
        chosen_rel = rng.choice(files)
        key = (cat, chosen_rel)

        if key not in sfx_paths_in_pkg:
            chosen_name = Path(chosen_rel).name
            src = args.sfx_root / chosen_rel
            if not src.exists():
                folder = LEGACY_TO_FOLDER.get(cat)
                if folder:
                    src = args.sfx_root / folder / chosen_name
            if not src.exists():
                print(f"  ❌ SFX não encontrado: {chosen_rel}", file=sys.stderr)
                continue
            dest = pkg / "03_sfx" / f"{cat.lower()}_{chosen_name}"
            shutil.copy2(src, dest)
            sfx_paths_in_pkg[key] = str(dest)
            print(f"  ✓ 03_sfx/{dest.name}")

        # Adiciona ao package-aware sfx_index
        if cat not in pack_sfx_index["categories"]:
            pack_sfx_index["categories"][cat] = {
                "description": f"Package — {cat}",
                "use_cases": [],
                "files": [sfx_paths_in_pkg[key]],
                "count": 1,
                "duration_ms_avg": 0,
            }
        pack_sfx_index["total_files"] += 1

    # ── 3. Preview do Remotion ─────────────────────────────────────────────────
    if args.proxy and args.proxy.exists():
        dest = pkg / "04_animacoes" / "preview_com_overlays.mp4"
        shutil.copy2(args.proxy, dest)
        sz_mb = dest.stat().st_size / 1024 / 1024
        print(f"  ✓ 04_animacoes/preview_com_overlays.mp4  [{sz_mb:.1f} MB]")

    # ── 4. Plano package-aware: cut.clip → abs path do pkg ────────────────────
    import copy as _copy
    plan_pkg = _copy.deepcopy(plan)
    for cut in plan_pkg["v1_main"]:
        if cut["clip"] in rename_map:
            cut["clip"] = rename_map[cut["clip"]]
    args.out_plan.write_text(json.dumps(plan_pkg, indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_sfx.write_text(json.dumps(pack_sfx_index, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── 5. README ──────────────────────────────────────────────────────────────
    readme = pkg / "README.md"
    readme_lines = [
        f"# {args.reel_name} — CapCut Package",
        "",
        "Pasta autocontida com brutos, SFX e preview da edição. CapCut draft já está registrado.",
        "",
        "## Subpastas",
        "- `01_brutos_hooks/` — Brutos contendo os ganchos de abertura",
        "- `02_brutos_cenas/` — Brutos das cenas principais (renomeados por contexto)",
        "- `03_sfx/` — Efeitos sonoros usados (cópia dos arquivos selecionados)",
        "- `04_animacoes/` — Preview do render Remotion com overlays/captions",
        "",
        "## Como abrir",
        f"1. Abra o CapCut Desktop → o draft `{args.reel_name}` aparece em Drafts.",
        "2. Se pedir 'Link media', aponte para esta pasta — os arquivos linkam automaticamente.",
        "3. ⚠️ Não mova esta pasta sem refazer os links (caminhos são absolutos no draft).",
        "",
        "## Brutos → cuts",
    ]
    for orig, new in rename_map.items():
        cuts = by_bruto[orig]
        cut_ids = [plan["v1_main"].index(c) + 1 for c in cuts]
        readme_lines.append(f"- `{Path(new).relative_to(pkg)}` — cuts {cut_ids}")
    readme.write_text("\n".join(readme_lines), encoding="utf-8")

    print()
    print(f"✓ Pacote criado: {pkg}")
    print(f"✓ Plan package-aware: {args.out_plan}")
    print(f"✓ SFX index package-aware: {args.out_sfx}")
    print()
    print("Próximo passo: rode capcut_draft_builder.py apontando para:")
    print(f"  --plan {args.out_plan}")
    print(f"  --sfx-index {args.out_sfx}")
    print(f"  --clips-dir {pkg}/02_brutos_cenas   (ou /tmp — caminhos já são absolutos)")
    print(f"  --reel-name {args.reel_name}")
    print(f"  --draft-name {args.reel_name}")


if __name__ == "__main__":
    main()

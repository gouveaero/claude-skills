#!/usr/bin/env python3
"""
export_overlays.py — Fase 10 do pipeline video-editor
Renderiza cada rich_overlay como .mov ProRes 4444 com canal alpha, pra colar
no V2 do CapCut (overlay sobre os cuts de V1).

Uso:
  python export_overlays.py --remotion-dir <remotion/> --output-dir <capcut_ready/overlays/>

Pré-requisito: Root.tsx registra uma Composition por rich_overlay com id no
formato `overlay_{idx:02d}_{kind}` (padrão emitido por build_remotion.py).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

OVERLAY_ID_RE = re.compile(r"^overlay-\d{2,}-[a-zA-Z0-9-]+$")


def discover_compositions_via_cli(remotion_dir: Path) -> list[dict]:
    """Lista Compositions do projeto Remotion usando `npx remotion compositions`."""
    try:
        result = subprocess.run(
            ["npx", "remotion", "compositions", "--log=error"],
            cwd=str(remotion_dir), capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        print(f"  [overlays] erro ao listar compositions: {e}", file=sys.stderr)
        return []
    if result.returncode != 0:
        print(f"  [overlays] remotion compositions failed: {result.stderr[-300:]}", file=sys.stderr)
        return []
    comps = []
    # Stdout do remotion compositions vem em formato "id <tab> width x height <tab> fps <tab> dur".
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        cid = parts[0]
        if OVERLAY_ID_RE.match(cid):
            comps.append({"id": cid})
    return comps


def derive_compositions_from_plan(plan_path: Path) -> list[dict]:
    """Fallback: gera os ids esperados a partir do edit_plan.rich_overlays."""
    if not plan_path.exists():
        return []
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)
    out = []
    for i, ov in enumerate(plan.get("rich_overlays", [])):
        kind = re.sub(r"[^a-zA-Z0-9-]", "-", str(ov.get("kind", "overlay")))
        cid = f"overlay-{i:02d}-{kind}"
        out.append({"id": cid, "start": float(ov.get("start", 0)),
                    "end": float(ov.get("end", 0)),
                    "duration_s": float(ov.get("end", 0)) - float(ov.get("start", 0))})
    return out


def render_overlay(composition_id: str, remotion_dir: Path, output_dir: Path,
                   scale: int = 2) -> bool:
    out_file = output_dir / f"{composition_id}.mov"
    cmd = [
        "npx", "remotion", "render",
        composition_id, str(out_file),
        "--codec=prores",
        "--prores-profile=4444",
        "--pixel-format=yuva444p10le",
        "--image-format=png",
        f"--scale={scale}",  # supersampling 2x → SVG/icons sem serrilhado
        "--log=error",
    ]
    print(f"  → {composition_id}…", flush=True)
    result = subprocess.run(cmd, cwd=str(remotion_dir))
    if result.returncode != 0:
        print(f"  [overlays] FALHOU: {composition_id}", file=sys.stderr)
        return False
    # IMPORTANTE: dois fixes pós-render obrigatórios em ProRes 4444:
    # (1) Premultiply alpha — Remotion grava STRAIGHT alpha mas ProRes 4444
    #     espec. Apple = PREMULTIPLIED. CapCut/Premiere/AE tratam como
    #     premultiplied, então pixels translúcidos (bg-alpha low) aparecem
    #     com RGB cheio ("luz estourada") em vez de escalado pela alpha.
    # (2) Marcar BT.709 — sem isso CapCut adivinha BT.601 (SD) num conteúdo
    #     HD, expandindo highlights.
    _premultiply_and_tag_bt709(out_file)
    sz_mb = out_file.stat().st_size / 1_048_576 if out_file.exists() else 0
    print(f"    {out_file.name} ({sz_mb:.1f} MB)")
    return True


def _premultiply_and_tag_bt709(mov: Path) -> bool:
    """Pre-multiplica RGB por alpha + marca metadata BT.709. Re-encode obrigatório
    pra aplicar premultiply filter."""
    tmp = mov.parent / f".{mov.stem}.fixed.mov"
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(mov),
        "-vf", "premultiply=inplace=1",
        "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-bsf:v", "prores_metadata=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
        "-c:a", "copy",
        str(tmp),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode == 0 and tmp.exists():
        tmp.replace(mov)
        return True
    if tmp.exists():
        tmp.unlink()
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--remotion-dir", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--plan", type=Path, default=None,
                   help="edit_plan.json (default: <remotion-dir>/src/edit_plan.json)")
    args = p.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = args.plan or (args.remotion_dir / "src" / "edit_plan.json")

    comps = discover_compositions_via_cli(args.remotion_dir)
    if not comps:
        print("  [overlays] CLI sem resultados, derivando do plan...")
        comps = derive_compositions_from_plan(plan_path)
    if not comps:
        print("  [overlays] nenhuma overlay encontrada — pulando.")
        sys.exit(0)

    print(f"Exportando {len(comps)} overlay(s) com alpha em {args.output_dir}")
    ok = 0
    for c in comps:
        if render_overlay(c["id"], args.remotion_dir, args.output_dir):
            ok += 1
    print(f"\n{ok}/{len(comps)} overlays exportados.")


if __name__ == "__main__":
    main()

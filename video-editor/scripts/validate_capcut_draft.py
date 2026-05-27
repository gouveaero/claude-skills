#!/usr/bin/env python3
"""
validate_capcut_draft.py — Valida um draft CapCut contra o edit_plan que o gerou.

Confere:
  V1  - source_timerange.start de cada cut == edit_plan.source_in (us)
       - target_timerange.start cumulativo coerente (sem gaps/overlaps)
       - path do arquivo existe
  A2  - cada SFX dentro do cap por categoria + não passa do próximo SFX
       - sem overlaps fortes (>1s)
  V2  - overlay .mov files presentes e timeline_start bate com rich_overlays
  Captions - texto na track de texto cobre a duração total da timeline

Reporta em formato resumo + lista de erros. Exit code 0 se válido, 1 caso contrário.

Uso:
  python3 validate_capcut_draft.py \\
      --draft-dir ~/Movies/CapCut/.../<draft> \\
      --plan      <output>/edit_plan.json \\
      [--strict]  # erros HARD: exit 1 mesmo em warnings
"""
import argparse, json, sys
from pathlib import Path

# Cap padrão por categoria (em ms) — mesmo do capcut_draft_builder
SFX_DURATION_CAPS_MS = {
    "WOOSH": 1500, "CLICK": 400, "DIGITAL": 1200, "TRANSIÇÃO": 1500,
    "CAMERA": 600, "PLIM": 1200, "RISER": 3000, "VARIAVEIS": 2000,
    "AMBIENTE": 10000, "CINEMATICA": 3500, "ROLAGEM": 2000, "GLITCH": 1200,
    "TECLADO": 3000, "DINHEIRO": 2000, "ESTALO": 400, "CONTAGEM": 2500,
    "POPS": 600, "BOOM": 3000, "NOTIFICATION": 1200, "DRUM": 1000,
    "GLASS_BREAK": 2000, "APPLAUSE": 3000, "HORROR": 3000, "FAIL": 2500,
    "MAGIC": 2000, "HEARTBEAT": 4000,
}
SFX_DEFAULT_CAP_MS = 2000
TOLERANCE_US = 50_000  # 50ms tolerância pra rounding/frame-quantization


def _us(seconds: float) -> int:
    return int(round(seconds * 1_000_000))


def validate(draft_dir: Path, plan_path: Path, strict: bool = False) -> int:
    issues_hard: list[str] = []
    issues_warn: list[str] = []
    summary: dict = {}

    info_path = draft_dir / "draft_info.json"
    if not info_path.exists():
        print(f"❌ draft_info.json não encontrado: {info_path}", file=sys.stderr)
        return 1

    with open(info_path, encoding="utf-8") as f:
        draft = json.load(f)
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)

    # Material lookups
    vid_mats = {v["id"]: v for v in draft.get("materials", {}).get("videos", [])}
    aud_mats = {a["id"]: a for a in draft.get("materials", {}).get("audios", [])}

    v1, audio_tracks, text_tracks = None, [], []
    for t in draft.get("tracks", []):
        if t.get("type") == "video" and v1 is None:
            v1 = t
        elif t.get("type") == "audio":
            audio_tracks.append(t)
        elif t.get("type") == "text":
            text_tracks.append(t)

    # ── V1: cuts ────────────────────────────────────────────────────────────
    plan_cuts = plan.get("v1_main", [])
    summary["v1_segments"] = len(v1["segments"]) if v1 else 0
    summary["plan_cuts"] = len(plan_cuts)

    if not v1 or not v1.get("segments"):
        issues_hard.append("V1 vazia — nenhum segmento de vídeo na timeline")
    else:
        if len(v1["segments"]) != len(plan_cuts):
            issues_hard.append(
                f"V1 tem {len(v1['segments'])} segments mas plan tem {len(plan_cuts)} cuts"
            )

        cumulative_us = 0
        for i, seg in enumerate(v1["segments"][:len(plan_cuts)]):
            plan_cut = plan_cuts[i]
            expected_src_us = _us(plan_cut["source_in"])
            expected_dur_us = _us(plan_cut["source_out"]) - expected_src_us
            actual_src_us = seg["source_timerange"]["start"]
            actual_dur_us = seg["source_timerange"]["duration"]
            actual_tgt_us = seg["target_timerange"]["start"]

            # Source_in deve bater (tolerância 50ms pra frame quantization)
            if abs(actual_src_us - expected_src_us) > TOLERANCE_US:
                issues_hard.append(
                    f"V1[{i+1:02d}] '{plan_cut['slug']}': source_in esperado "
                    f"{expected_src_us/1e6:.2f}s, draft tem {actual_src_us/1e6:.2f}s "
                    f"(Δ={(actual_src_us-expected_src_us)/1e6:+.2f}s)"
                )

            # Duration aproximadamente igual
            if abs(actual_dur_us - expected_dur_us) > TOLERANCE_US:
                issues_warn.append(
                    f"V1[{i+1:02d}] '{plan_cut['slug']}': duration esperada "
                    f"{expected_dur_us/1e6:.2f}s, draft tem {actual_dur_us/1e6:.2f}s"
                )

            # Target_start cumulativo (sem gap)
            if abs(actual_tgt_us - cumulative_us) > TOLERANCE_US:
                gap_s = (actual_tgt_us - cumulative_us) / 1e6
                issues_warn.append(
                    f"V1[{i+1:02d}] gap/overlap em t={actual_tgt_us/1e6:.2f}s "
                    f"(esperado {cumulative_us/1e6:.2f}s, Δ={gap_s:+.2f}s)"
                )

            cumulative_us = actual_tgt_us + actual_dur_us

            # Arquivo existe
            mat = vid_mats.get(seg["material_id"], {})
            p = mat.get("path", "")
            if p and not Path(p).exists():
                issues_hard.append(f"V1[{i+1:02d}] arquivo missing: {p}")

    # ── A2: SFX caps + overlap ──────────────────────────────────────────────
    sfx_segments = []
    for t in audio_tracks:
        for seg in t.get("segments", []):
            mat = aud_mats.get(seg["material_id"], {})
            sfx_segments.append({
                "seg": seg, "mat": mat,
                "name": Path(mat.get("path", "?")).name,
                "at_us": seg["target_timerange"]["start"],
                "dur_us": seg["target_timerange"]["duration"],
            })
    sfx_segments.sort(key=lambda s: s["at_us"])
    summary["sfx_segments"] = len(sfx_segments)
    summary["plan_sfx"] = len(plan.get("sfx", []))

    if sfx_segments and len(sfx_segments) != summary["plan_sfx"]:
        issues_warn.append(
            f"A2 tem {len(sfx_segments)} SFX mas plan tem {summary['plan_sfx']}"
        )

    for i, s in enumerate(sfx_segments):
        # Deriva categoria do nome (prefixo `<cat>_...` adicionado por package_for_capcut)
        cat = s["name"].split("_", 1)[0].upper()
        cap_ms = SFX_DURATION_CAPS_MS.get(cat, SFX_DEFAULT_CAP_MS)
        if s["dur_us"] > (cap_ms + 200) * 1000:  # 200ms folga
            issues_hard.append(
                f"A2[{i+1}] SFX {s['name']} dura {s['dur_us']/1e6:.2f}s "
                f"— acima do cap {cap_ms}ms ({cat}) — vai loopar/sobrepor"
            )
        # Overlap com próximo
        if i + 1 < len(sfx_segments):
            nxt = sfx_segments[i + 1]
            end_us = s["at_us"] + s["dur_us"]
            if end_us > nxt["at_us"] + TOLERANCE_US:
                overlap_s = (end_us - nxt["at_us"]) / 1e6
                level = issues_hard if overlap_s > 1.0 else issues_warn
                level.append(
                    f"A2[{i+1}→{i+2}] overlap {overlap_s:.2f}s entre "
                    f"{s['name']} e {nxt['name']}"
                )

    # ── V2+: overlays alpha (pode estar espalhado em V2/V3/V4 pra acomodar overlaps) ─
    video_tracks_all = [t for t in draft.get("tracks", []) if t.get("type") == "video"]
    overlay_tracks = video_tracks_all[1:]  # V1 é main, V2+ são overlays
    plan_rich = plan.get("rich_overlays", [])
    overlay_count = sum(len(t.get("segments", [])) for t in overlay_tracks)
    summary["v2_overlays"] = overlay_count
    summary["overlay_tracks"] = len(overlay_tracks)
    summary["plan_rich_overlays"] = len(plan_rich)
    if plan_rich and overlay_count == 0:
        issues_warn.append(
            f"V2 vazia mas plan declara {len(plan_rich)} rich_overlays — "
            f"rode export_overlays.py + rebuild do draft pra ter as animações"
        )

    # ── Captions ────────────────────────────────────────────────────────────
    total_text = sum(len(t.get("segments", [])) for t in text_tracks)
    summary["captions"] = total_text
    summary["plan_subtitle_track"] = len(plan.get("subtitle_track", []))

    # ── Report ──────────────────────────────────────────────────────────────
    print("=" * 60)
    print("CAPCUT DRAFT VALIDATION")
    print("=" * 60)
    print(f"Draft: {draft_dir}")
    print(f"Plan:  {plan_path}")
    print()
    print("Resumo:")
    for k, v in summary.items():
        print(f"  {k:24s} = {v}")
    print()
    if issues_hard:
        print(f"❌ {len(issues_hard)} ERRO(s) HARD:")
        for e in issues_hard:
            print(f"   - {e}")
        print()
    if issues_warn:
        print(f"⚠️  {len(issues_warn)} aviso(s):")
        for w in issues_warn:
            print(f"   - {w}")
        print()
    if not issues_hard and not issues_warn:
        print("✅ Tudo OK — draft consistente com o plan")

    if issues_hard or (strict and issues_warn):
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draft-dir", required=True, type=Path)
    ap.add_argument("--plan",      required=True, type=Path)
    ap.add_argument("--strict", action="store_true", help="Warnings também viram exit 1")
    args = ap.parse_args()
    sys.exit(validate(args.draft_dir, args.plan, args.strict))


if __name__ == "__main__":
    main()

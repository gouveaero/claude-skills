#!/usr/bin/env python3
"""
build_pipeline.py — Orquestrador do pipeline video-editor-remotion (Remotion-only)
Executa as 9 fases do pipeline, cada uma skipável via --skip-<fase>.

Diferença vs skill pai (/video-editor): este pipeline renderiza o final.mp4 100%
dentro do Remotion. Não há export ProRes, draft CapCut, ou pacote autocontido —
o deliverable é um único final.mp4 self-contained.

Uso:
  python build_pipeline.py --input <pasta_brutos> [--roteiro <roteiro.md>]
                           [--aspect 9:16|16:9] [--target-duration 30]
                           [--reel-name <nome>]
                           [--codec h264|h265|prores|vp8|vp9] [--crf 18]
                           [--scale 2]                  # supersampling SVG
                           [--autonomous]               # skip human gate
                           [--thumbnail-frame-ms 80000] # also render cover
                           [--skip-setup] [--skip-transcribe] [--skip-filter]
                           [--skip-plan]  [--skip-assets] [--skip-remotion]
                           [--skip-preview] [--skip-final]
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS = Path(__file__).parent

def run_script(script_name, args_list, cwd=None):
    """Executa um script Python do mesmo diretório."""
    cmd = [sys.executable, str(SCRIPTS / script_name)] + args_list
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode

def find_video_editor_json(start_dir):
    """Busca .video-editor.json subindo na árvore de diretórios."""
    current = Path(start_dir).resolve()
    for _ in range(6):  # máx 6 níveis
        candidate = current / ".video-editor.json"
        if candidate.exists():
            return str(candidate)
        current = current.parent
    return None

def detect_roteiro(input_dir):
    """Auto-detecta roteiro.md na pasta de input."""
    for name in ["roteiro.md", "roteiro.txt", "script.md", "script.txt"]:
        p = Path(input_dir) / name
        if p.exists():
            return str(p)
    return None

def main():
    p = argparse.ArgumentParser(description="Pipeline 100% Remotion — raw clips → final.mp4 (no CapCut handoff)")
    p.add_argument("--input", required=True, help="Pasta com vídeos brutos")
    p.add_argument("--roteiro", help="Arquivo de roteiro (.md). Auto-detecta se omitido.")
    p.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    p.add_argument("--target-duration", type=int, default=30)
    p.add_argument("--reel-name", default="reel-01")
    p.add_argument("--skip-setup", action="store_true")
    p.add_argument("--skip-transcribe", action="store_true")
    p.add_argument("--skip-filter", action="store_true")
    p.add_argument("--skip-plan", action="store_true")
    p.add_argument("--skip-assets", action="store_true")
    p.add_argument("--skip-remotion", action="store_true")
    p.add_argument("--skip-preview", action="store_true")
    p.add_argument("--skip-visual-review", action="store_true")
    p.add_argument("--skip-final", action="store_true",
                   help="Skip phase 9 (final.mp4 render)")
    p.add_argument("--autonomous", action="store_true",
                   help="Skip human gate after preview — go straight to final render")
    # Final render options
    p.add_argument("--codec", default="h264", choices=["h264", "h265", "vp8", "vp9", "prores"],
                   help="Codec for final.mp4 (default: h264)")
    p.add_argument("--crf", type=int, default=18,
                   help="CRF for final render (lower=better quality, 18 is default)")
    p.add_argument("--scale", type=int, default=1,
                   help="Render scale multiplier (e.g. 2 for supersampling SVG)")
    p.add_argument("--concurrency", type=int, default=None,
                   help="Frame-encoding concurrency (default: auto)")
    p.add_argument("--thumbnail-frame-ms", type=int, default=None,
                   help="If set, also render a thumbnail at this many ms into the reel")
    p.add_argument("--agent-mode", action="store_true", help="Usa modo agent (sem chamadas API diretas)")
    p.add_argument("--refresh-nlm-cache", action="store_true", help="Regenera best-practices-notebooklm.md")
    args = p.parse_args()

    input_dir = Path(args.input).resolve()
    if not input_dir.exists():
        print(f"Erro: pasta de input não encontrada: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # Auto-detecta roteiro
    roteiro = args.roteiro or detect_roteiro(input_dir)
    if not roteiro:
        print("Nenhum roteiro encontrado. Continuando sem roteiro.")

    # Diretório de output
    output_dir = input_dir.parent / "output" / args.reel_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detecta brand config
    brand_config = find_video_editor_json(input_dir)
    if brand_config:
        print(f"Brand config: {brand_config}")

    # Atualiza cache NotebookLM se solicitado
    if args.refresh_nlm_cache:
        nlm_report = SKILL_DIR / "references" / "best-practices-notebooklm.md"
        print("Atualizando cache NotebookLM...")
        run_script("query_notebooklm.py", ["--generate-report", "--output", str(nlm_report)])

    proxies_dir = output_dir / "clips_proxy"
    transcripts_file = output_dir / "transcripts.json"
    filter_output = output_dir
    edit_plan_file = output_dir / "edit_plan.json"
    assets_dir = input_dir / "assets"
    assets_manifest = output_dir / "assets_needed.json"
    remotion_dir = output_dir / "remotion"
    proxy_mp4 = output_dir / "proxy.mp4"
    capcut_ready = output_dir / "capcut_ready"

    # -- Fase 1: Setup --
    if not args.skip_setup:
        print("\n[1/9] Setup & transcode...")
        rc = run_script("setup_project.py", [
            "--input", str(input_dir),
            "--name", args.reel_name,
        ])
        if rc != 0:
            print("Erro no setup.", file=sys.stderr); sys.exit(rc)
    else:
        print("[1/9] Setup — pulado")

    # -- Fase 2: Transcribe --
    if not args.skip_transcribe:
        print("\n[2/9] Transcrevendo clips...")
        rc = run_script("transcribe.py", [
            "--input", str(proxies_dir),
            "--output", str(transcripts_file)
        ])
        if rc != 0:
            print("Erro na transcrição.", file=sys.stderr); sys.exit(rc)
    else:
        print("[2/9] Transcribe — pulado")

    # -- Fase 3: Filter raws --
    if not args.skip_filter and transcripts_file.exists():
        print("\n[3/9] Filtrando clips relevantes...")
        filter_args = [
            "--transcripts", str(transcripts_file),
            "--clips-dir", str(proxies_dir),
            "--output", str(filter_output)
        ]
        if roteiro:
            filter_args += ["--roteiro", roteiro]
        if args.agent_mode:
            filter_args.append("--agent")
        rc = run_script("filter_raws.py", filter_args)
        if rc == 2:
            print("Aguardando preenchimento do brief de filtragem. Rerun com --skip-filter.")
            sys.exit(2)
        if rc != 0:
            print("Erro na filtragem.", file=sys.stderr); sys.exit(rc)
    else:
        print("[3/9] Filter — pulado")

    # -- Fase 4: Plan edit --
    if not args.skip_plan:
        print("\n[4/9] Gerando plano de edição...")
        selected_dir = filter_output / "selected"
        clips_for_plan = str(selected_dir) if selected_dir.exists() else str(proxies_dir)
        plan_args = [
            "--transcripts", str(transcripts_file),
            "--output", str(edit_plan_file),
            "--aspect", args.aspect,
            "--target-duration", str(args.target_duration),
            "--name", args.reel_name,
            "--sfx-index", str(SKILL_DIR / "assets" / "sfx_index.json"),
            "--best-practices", str(SKILL_DIR / "references" / "best-practices-notebooklm.md")
        ]
        if roteiro:
            plan_args += ["--script", roteiro]
        if brand_config:
            plan_args += ["--brand-config", brand_config]
        if args.agent_mode:
            plan_args.append("--planner=agent")
        rc = run_script("plan_edit.py", plan_args)
        if rc == 2:
            print("Modo agent: preencha o edit_plan.json e rerun com --skip-plan.")
            sys.exit(2)
        if rc != 0:
            print("Erro no plano.", file=sys.stderr); sys.exit(rc)
    else:
        print("[4/9] Plan edit — pulado")

    # -- Fase 5: Request assets --
    if not args.skip_assets and edit_plan_file.exists():
        print("\n[5/9] Verificando assets necessários...")
        rc = run_script("request_assets.py", [
            "--plan", str(edit_plan_file),
            "--assets-dir", str(assets_dir),
            "--output", str(assets_manifest)
        ])
        if rc == 2:
            print("\nColoque os assets faltantes em:", assets_dir)
            print("Depois rode: build_pipeline.py --skip-setup --skip-transcribe --skip-filter --skip-plan")
            sys.exit(2)
        if rc != 0:
            print("Erro na verificação de assets.", file=sys.stderr); sys.exit(rc)
    else:
        print("[5/9] Assets — pulado")

    # -- Fase 6: Build Remotion --
    if not args.skip_remotion and edit_plan_file.exists():
        print("\n[6/9] Construindo projeto Remotion...")
        remotion_args = [
            "--plan", str(edit_plan_file),
            "--remotion-dir", str(remotion_dir),
            "--skill-dir", str(SKILL_DIR)
        ]
        if brand_config:
            remotion_args += ["--brand-config", brand_config]
        rc = run_script("build_remotion.py", remotion_args)
        if rc != 0:
            print("Erro ao construir Remotion.", file=sys.stderr); sys.exit(rc)
    else:
        print("[6/9] Build Remotion — pulado")

    # -- Fase 7: Preview --
    if not args.skip_preview and remotion_dir.exists():
        print("\n[7/9] Preview (Studio + proxy MP4)...")
        import threading
        # Gera proxy em paralelo ao Studio
        def gen_proxy():
            run_script("render_proxy.py", [
                "--remotion-dir", str(remotion_dir),
                "--output", str(proxy_mp4),
                "--aspect", args.aspect
            ])
        proxy_thread = threading.Thread(target=gen_proxy)
        proxy_thread.start()

        # Abre Studio
        rc = run_script("preview.py", ["--remotion-dir", str(remotion_dir)])
        proxy_thread.join()

        print(f"\nPreview concluído.")
        if proxy_mp4.exists():
            size_mb = proxy_mp4.stat().st_size / 1_048_576
            print(f"  Proxy: {proxy_mp4} ({size_mb:.1f} MB)")
        # -- Fase 7.5: Visual Review (auto QA before showing human) --
        if not args.skip_visual_review and proxy_mp4.exists() and edit_plan_file.exists():
            print("\n[7.5/9] Visual review — extraindo frames p/ revisão automática...")
            review_args = [
                "--proxy", str(proxy_mp4),
                "--plan", str(edit_plan_file),
                "--output-dir", str(output_dir),
            ]
            if args.agent_mode:
                review_args.append("--agent")
            rc = run_script("visual_review.py", review_args)
            if rc == 2:
                print("\n[AGENT REVIEW REQUIRED] Leia visual_review_brief.md, revise frames em _review_frames/,")
                print("   conserte problemas em <remotion>/src/components/RichOverlays.tsx, re-renderize o proxy,")
                print("   e SÓ ENTÃO apresente ao humano. Não pule essa etapa.")
                sys.exit(2)

        if args.autonomous:
            print("\n--autonomous: pulando gate humano, indo direto pro render final.")
        else:
            print("\nGATE HUMANO: revise o proxy.mp4 e aprove antes de continuar.")
            print("   Quando pronto, rode novamente com --skip-setup --skip-transcribe --skip-filter --skip-plan --skip-assets --skip-remotion --skip-preview --skip-visual-review")
            print("   Ou rode com --autonomous para pular o gate completamente.")
            sys.exit(0)
    else:
        print("[7/9] Preview — pulado")

    # Autonomous mode skips the human gate; otherwise we already sys.exit(0) above
    # so that the user can manually resume after approving proxy.mp4.

    # -- Fase 9: Final render (Remotion → MP4) --
    if not args.skip_final and remotion_dir.exists():
        print("\n[9/9] Renderizando final.mp4 (Remotion)...")
        final_out = output_dir / "final.mp4"
        final_args = [
            "--remotion-dir", str(remotion_dir),
            "--out", str(final_out),
            "--codec", args.codec,
            "--crf", str(args.crf),
        ]
        if args.scale > 1:
            final_args += ["--scale", str(args.scale)]
        if args.concurrency:
            final_args += ["--concurrency", str(args.concurrency)]
        rc = run_script("final_render.py", final_args)
        if rc != 0:
            print("Erro no render final.", file=sys.stderr); sys.exit(rc)
        print(f"\n✓ Final MP4: {final_out}")

        # Optional thumbnail
        if args.thumbnail_frame_ms is not None:
            print("\n[9.5/9] Renderizando thumbnail...")
            thumb_out = output_dir / "thumbnail.png"
            rc = run_script("render_thumbnail.py", [
                "--remotion-dir", str(remotion_dir),
                "--out", str(thumb_out),
                "--frame-ms", str(args.thumbnail_frame_ms),
            ])
            if rc == 0:
                print(f"✓ Thumbnail: {thumb_out}")
    else:
        print("[9/9] Final render — pulado")

    print("\nPipeline completo! Final MP4 pronto pra upload.")

if __name__ == "__main__":
    main()

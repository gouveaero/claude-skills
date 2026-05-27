#!/usr/bin/env python3
"""
build_pipeline.py — Orquestrador principal do pipeline video-editor
Executa as 11 fases do pipeline, cada uma skipável via --skip-<fase>.

Uso:
  python build_pipeline.py --input <pasta_brutos> [--roteiro <roteiro.md>]
                           [--aspect 9:16|16:9] [--target-duration 30]
                           [--no-capcut] [--skip-setup] [--skip-transcribe]
                           [--skip-filter] [--skip-plan] [--skip-assets]
                           [--skip-remotion] [--skip-preview] [--skip-export]
                           [--skip-overlays] [--skip-capcut]
                           [--reel-name <nome>]
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
    p = argparse.ArgumentParser(description="Pipeline unificado video-editor (Remotion + CapCut)")
    p.add_argument("--input", required=True, help="Pasta com vídeos brutos")
    p.add_argument("--roteiro", help="Arquivo de roteiro (.md). Auto-detecta se omitido.")
    p.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    p.add_argument("--target-duration", type=int, default=30)
    p.add_argument("--reel-name", default="reel-01")
    p.add_argument("--no-capcut", action="store_true")
    p.add_argument("--skip-setup", action="store_true")
    p.add_argument("--skip-transcribe", action="store_true")
    p.add_argument("--skip-filter", action="store_true")
    p.add_argument("--skip-plan", action="store_true")
    p.add_argument("--skip-assets", action="store_true")
    p.add_argument("--skip-remotion", action="store_true")
    p.add_argument("--skip-preview", action="store_true")
    p.add_argument("--skip-visual-review", action="store_true")
    p.add_argument("--skip-export", action="store_true")
    p.add_argument("--skip-overlays", action="store_true")
    p.add_argument("--skip-capcut", action="store_true")
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
        print("\n[1/11] Setup & transcode...")
        rc = run_script("setup_project.py", [
            "--input", str(input_dir),
            "--name", args.reel_name,
        ])
        if rc != 0:
            print("Erro no setup.", file=sys.stderr); sys.exit(rc)
    else:
        print("[1/11] Setup — pulado")

    # -- Fase 2: Transcribe --
    if not args.skip_transcribe:
        print("\n[2/11] Transcrevendo clips...")
        rc = run_script("transcribe.py", [
            "--input", str(proxies_dir),
            "--output", str(transcripts_file)
        ])
        if rc != 0:
            print("Erro na transcrição.", file=sys.stderr); sys.exit(rc)
    else:
        print("[2/11] Transcribe — pulado")

    # -- Fase 3: Filter raws --
    if not args.skip_filter and transcripts_file.exists():
        print("\n[3/11] Filtrando clips relevantes...")
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
        print("[3/11] Filter — pulado")

    # -- Fase 4: Plan edit --
    if not args.skip_plan:
        print("\n[4/11] Gerando plano de edição...")
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
        print("[4/11] Plan edit — pulado")

    # -- Fase 5: Request assets --
    if not args.skip_assets and edit_plan_file.exists():
        print("\n[5/11] Verificando assets necessários...")
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
        print("[5/11] Assets — pulado")

    # -- Fase 6: Build Remotion --
    if not args.skip_remotion and edit_plan_file.exists():
        print("\n[6/11] Construindo projeto Remotion...")
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
        print("[6/11] Build Remotion — pulado")

    # -- Fase 7: Preview --
    if not args.skip_preview and remotion_dir.exists():
        print("\n[7/11] Preview (Studio + proxy MP4)...")
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
            print("\n[7.5/11] Visual review — extraindo frames p/ revisão automática...")
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

        print("\nGATE HUMANO: revise o proxy.mp4 e aprove antes de continuar.")
        print("   Quando pronto, rode novamente com --skip-setup --skip-transcribe --skip-filter --skip-plan --skip-assets --skip-remotion --skip-preview --skip-visual-review")
        sys.exit(0)
    else:
        print("[7/11] Preview — pulado")

    if args.no_capcut:
        print("\nModo --no-capcut: finalizando antes do export CapCut.")
        sys.exit(0)

    # -- Fase 9: Export clips --
    if not args.skip_export and edit_plan_file.exists():
        print("\n[9/11] Exportando clips para CapCut...")
        clips_out = capcut_ready / "clips"
        clips_out.mkdir(parents=True, exist_ok=True)
        rc = run_script("export_clips.py", [
            "--plan", str(edit_plan_file),
            "--clips-dir", str(input_dir),
            "--out-dir", str(clips_out),
        ])
        if rc != 0:
            print("Erro ao exportar clips.", file=sys.stderr)
    else:
        print("[9/11] Export clips — pulado")

    # -- Fase 10: Export overlays --
    if not args.skip_overlays and remotion_dir.exists():
        print("\n[10/11] Exportando overlays com alpha...")
        overlays_out = capcut_ready / "overlays"
        rc = run_script("export_overlays.py", [
            "--remotion-dir", str(remotion_dir),
            "--output-dir", str(overlays_out)
        ])
        if rc != 0:
            print("Erro ao exportar overlays (continuando).")
    else:
        print("[10/11] Export overlays — pulado")

    # -- Fase 11: Package + Build CapCut draft --
    # Cria uma pasta autocontida (capcut_package/) com brutos renomeados por
    # cena, ganchos separados, SFX usados e preview Remotion — então constrói
    # o draft apontando pros caminhos da pasta. Usuário pode levar/mover a
    # pasta inteira sem quebrar os links.
    if not args.skip_capcut and edit_plan_file.exists():
        print("\n[11/11] Empacotando + construindo draft CapCut...")
        proxy_path = output_dir / "proxy.mp4"
        pkg_plan = output_dir / "edit_plan_packaged.json"
        pkg_sfx = output_dir / "sfx_index_packaged.json"

        pkg_args = [
            "--plan", str(edit_plan_file),
            "--brutos-dir", str(input_dir),
            "--sfx-index", str(SKILL_DIR / "assets" / "sfx_index.json"),
            "--reel-name", args.reel_name,
            "--pkg-root", str(input_dir),
            "--out-plan", str(pkg_plan),
            "--out-sfx", str(pkg_sfx),
        ]
        if proxy_path.exists():
            pkg_args += ["--proxy", str(proxy_path)]
        rc = run_script("package_for_capcut.py", pkg_args)
        if rc != 0:
            print("Erro ao empacotar pasta CapCut.", file=sys.stderr); sys.exit(rc)

        draft_args = [
            "--plan", str(pkg_plan),
            "--clips-dir", "/tmp",  # placeholder: cut.clip é absoluto após package
            "--draft-name", args.reel_name,
            "--reel-name", args.reel_name,
            "--sfx-index", str(pkg_sfx),
        ]
        overlays_dir = capcut_ready / "overlays"
        if overlays_dir.exists():
            draft_args += ["--overlays-dir", str(overlays_dir)]
        rc = run_script("capcut_draft_builder.py", draft_args)
        if rc != 0:
            print("Erro ao criar draft CapCut.", file=sys.stderr); sys.exit(rc)
        print(f"\n✓ Pacote organizado: {input_dir / 'capcut_package'}")
        print(f"✓ Draft CapCut: ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/{args.reel_name}")

        # -- Fase 11.5: Valida draft contra plan --
        print("\n[11.5] Validando draft CapCut vs edit_plan...")
        draft_dir = Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft" / args.reel_name
        rc = run_script("validate_capcut_draft.py", [
            "--draft-dir", str(draft_dir),
            "--plan",      str(pkg_plan),
        ])
        if rc != 0:
            print("⚠️  Validação encontrou problemas — revise antes de abrir o CapCut.", file=sys.stderr)
        else:
            print("✓ Draft validado contra o plan")
    else:
        print("[11/11] CapCut draft — pulado")

    print("\nPipeline completo! Abra o CapCut Desktop para ajuste fino.")

if __name__ == "__main__":
    main()

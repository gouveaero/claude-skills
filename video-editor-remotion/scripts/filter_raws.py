#!/usr/bin/env python3
"""
filter_raws.py — Fase 3 do pipeline video-editor
Analisa transcripts + roteiro e seleciona quais clips entram no vídeo.
Transcript-first com fallback adaptativo para análise visual (frames) quando necessário.

Uso:
  python filter_raws.py --transcripts <transcripts.json> --roteiro <roteiro.md> \
                        --clips-dir <pasta_proxies> --output <dir_output> [--agent]

Saída:
  <output>/clips_selecionados.json  — lista de clips com score, motivo, needs_visual_check
  <output>/selected/                — symlinks para os clips selecionados

Exit codes:
  0 — sucesso
  2 — modo --agent: escreveu brief.md, aguarda preenchimento externo do JSON
"""
import argparse, json, os, subprocess, sys, base64, hashlib
from pathlib import Path

# ─── helpers ──────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)

def ffmpeg_extract_frames(clip_path, output_dir, n_frames=3):
    """Extrai n_frames distribuídos uniformemente do clip. Retorna lista de paths PNG."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(clip_path).stem
    # ffprobe pra duração
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(clip_path)],
        capture_output=True, text=True
    )
    duration = float(json.loads(result.stdout)["format"]["duration"])
    step = duration / (n_frames + 1)
    frames = []
    for i in range(1, n_frames + 1):
        t = step * i
        out = output_dir / f"{stem}_frame_{i}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", str(clip_path),
             "-vframes", "1", "-q:v", "2", str(out)],
            capture_output=True
        )
        if out.exists():
            frames.append(str(out))
    return frames

def image_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def call_anthropic_text(system_prompt, user_message, cache_key=None):
    """Chama Claude API com prompt caching. Retorna texto da resposta."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": user_message}]
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=[
                {"type": "text", "text": system_prompt,
                 "cache_control": {"type": "ephemeral"}}
            ],
            messages=messages
        )
        return response.content[0].text
    except ImportError:
        return None

def call_anthropic_multimodal(system_prompt, text_content, images_b64):
    """Chama Claude com imagens (frames do clip)."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        content = []
        for img_b64 in images_b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
            })
        content.append({"type": "text", "text": text_content})
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": content}]
        )
        return response.content[0].text
    except ImportError:
        return None

# ─── core logic ───────────────────────────────────────────────────────────────

SELECTION_SYSTEM = """Você é um editor de vídeo especialista. Analise os transcripts dos clips e o roteiro,
e decida quais clips são relevantes para o vídeo final.

Para cada clip retorne:
- score: 0.0 a 1.0 (relevância)
- motivo: por que incluir ou excluir (1-2 frases)
- needs_visual_check: true se for b-roll/cena sem fala/ambíguo

Retorne JSON válido com esta estrutura:
{
  "clips": [
    {"filename": "nome.mp4", "score": 0.8, "motivo": "...", "needs_visual_check": false},
    ...
  ]
}
"""

VISUAL_CHECK_SYSTEM = """Você é um editor de vídeo. Analise os frames deste clip de b-roll/cena visual
e decida se é relevante para o contexto do roteiro fornecido.

Retorne JSON: {"include": true/false, "motivo": "...", "score": 0.0-1.0}
"""

def filter_by_transcript(transcripts, roteiro_text):
    """Passa 1: seleciona clips por transcript + roteiro."""
    transcript_summary = []
    for fname, data in transcripts.items():
        words = data.get("words", [])
        text = " ".join(w["word"] for w in words) if words else data.get("text", "")
        has_speech = len(text.strip()) > 20
        transcript_summary.append({
            "filename": fname,
            "has_speech": has_speech,
            "transcript_preview": text[:300] if text else "(sem fala)"
        })

    user_msg = f"""ROTEIRO:\n{roteiro_text}\n\nCLIPS (transcripts):\n{json.dumps(transcript_summary, ensure_ascii=False, indent=2)}\n\nSelecione os clips relevantes."""

    result_text = call_anthropic_text(SELECTION_SYSTEM, user_msg)
    if not result_text:
        # fallback: inclui tudo
        return [{"filename": k, "score": 0.5, "motivo": "API indisponível — incluído por padrão",
                 "needs_visual_check": False} for k in transcripts.keys()]

    try:
        result = json.loads(result_text)
        return result["clips"]
    except Exception:
        # tenta extrair JSON do texto
        import re
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            return json.loads(match.group())["clips"]
        return [{"filename": k, "score": 0.5, "motivo": "Parse error — incluído por padrão",
                 "needs_visual_check": True} for k in transcripts.keys()]

def visual_check(clip_path, roteiro_text, frames_dir):
    """Passa 2: verifica clip visualmente via frames."""
    frames = ffmpeg_extract_frames(clip_path, frames_dir)
    if not frames:
        return {"include": True, "motivo": "Sem frames extraíveis — incluído por padrão", "score": 0.5}

    images_b64 = [image_to_b64(f) for f in frames]
    user_msg = f"ROTEIRO:\n{roteiro_text[:500]}\n\nAnalise os {len(frames)} frames deste clip."

    result_text = call_anthropic_multimodal(VISUAL_CHECK_SYSTEM, user_msg, images_b64)
    if not result_text:
        return {"include": True, "motivo": "API indisponível — incluído por padrão", "score": 0.5}

    try:
        return json.loads(result_text)
    except Exception:
        return {"include": True, "motivo": "Parse error — incluído", "score": 0.5}

# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Filtra clips brutos relevantes para o vídeo")
    p.add_argument("--transcripts", required=True)
    p.add_argument("--roteiro", required=True)
    p.add_argument("--clips-dir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--agent", action="store_true", help="Modo agent: escreve brief.md e sai")
    p.add_argument("--min-score", type=float, default=0.5)
    args = p.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = Path(args.clips_dir)

    transcripts = load_json(args.transcripts)
    roteiro_text = Path(args.roteiro).read_text() if Path(args.roteiro).exists() else ""

    if args.agent:
        brief_path = output_dir / "filter_brief.md"
        brief_path.write_text(
            f"# Brief de Filtragem de Clips\n\n"
            f"## Roteiro\n{roteiro_text}\n\n"
            f"## Clips disponíveis\n"
            + "\n".join(f"- `{k}`" for k in transcripts.keys())
            + "\n\n## Instrução\nPreencha `clips_selecionados.json` com os clips relevantes."
        )
        print(f"Brief escrito em {brief_path}. Preencha clips_selecionados.json para continuar.")
        sys.exit(2)

    print("Fase 1: análise por transcript...")
    selections = filter_by_transcript(transcripts, roteiro_text)

    # Fase 2: visual check adaptativo
    frames_dir = output_dir / "_frames_tmp"
    for sel in selections:
        if sel.get("needs_visual_check") and sel.get("score", 0) > 0.3:
            clip_path = clips_dir / sel["filename"]
            if clip_path.exists():
                print(f"  Verificação visual: {sel['filename']}...")
                check = visual_check(clip_path, roteiro_text, frames_dir)
                if not check.get("include", True):
                    sel["score"] = max(0.0, sel["score"] - 0.3)
                    sel["motivo"] += f" [visual: {check.get('motivo', '')}]"
                else:
                    sel["score"] = min(1.0, sel.get("score", 0.5) + 0.1)
                    sel["motivo"] += f" [visual: OK]"

    # Aplica threshold
    selected = [s for s in selections if s.get("score", 0) >= args.min_score]
    rejected = [s for s in selections if s.get("score", 0) < args.min_score]

    # Cria selected/ com symlinks
    selected_dir = output_dir / "selected"
    selected_dir.mkdir(exist_ok=True)
    for s in selected:
        src = clips_dir / s["filename"]
        if src.exists():
            dst = selected_dir / s["filename"]
            if not dst.exists():
                dst.symlink_to(src.resolve())

    # Salva JSON
    result = {"selected": selected, "rejected": rejected}
    out_path = output_dir / "clips_selecionados.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"\n{len(selected)} clips selecionados, {len(rejected)} rejeitados.")
    print(f"  Salvo em: {out_path}")

    # Limpa frames temporários
    import shutil
    if frames_dir.exists():
        shutil.rmtree(frames_dir)

if __name__ == "__main__":
    main()

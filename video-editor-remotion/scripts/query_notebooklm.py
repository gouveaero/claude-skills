#!/usr/bin/env python3
"""
query_notebooklm.py — Utilitário video-editor
Consulta um notebook NotebookLM e cacheia respostas por hash da pergunta.

Uso:
  python query_notebooklm.py --question "como usar SFX em Reels?" [--notebook-id <id>]
  python query_notebooklm.py --generate-report --output <path.md>
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "video-editor" / "nlm-queries"
NLM_CLI = str(Path.home() / "bin" / "notebooklm")

def cache_key(question):
    return hashlib.sha256(question.encode()).hexdigest()[:16]

def run_notebooklm(*args, timeout=120):
    """Executa o CLI notebooklm e retorna stdout."""
    env_path = str(Path.home() / "bin") + ":" + __import__("os").environ.get("PATH", "")
    result = subprocess.run(
        [NLM_CLI, *args],
        capture_output=True, text=True, timeout=timeout,
        env={**__import__("os").environ, "PATH": env_path}
    )
    if result.returncode != 0:
        print(f"notebooklm error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def query(question, notebook_id=None, force=False):
    """Consulta com cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = cache_key(question)
    cache_file = CACHE_DIR / f"{key}.json"

    if cache_file.exists() and not force:
        cached = json.loads(cache_file.read_text())
        print(f"(cache hit: {key})")
        return cached["answer"]

    if notebook_id:
        run_notebooklm("use", notebook_id)

    answer = run_notebooklm("ask", question)
    if answer:
        cache_file.write_text(json.dumps({"question": question, "answer": answer}))

    return answer

def generate_report(output_path, notebook_id=None):
    """Gera briefing-doc e faz download."""
    if notebook_id:
        run_notebooklm("use", notebook_id)

    print("Gerando relatório de best-practices...")
    instruction = (
        "Extraia best-practices acionáveis para edição de vídeo curto (Reels/TikTok) "
        "e longo (YouTube): cortes, ritmo, hooks, retenção, uso de SFX, zooms, "
        "motion-graphics, captions, b-roll, color, áudio. Estruture por seção temática."
    )
    result = run_notebooklm("generate", "report", "--format", "briefing-doc",
                            "--append", instruction, timeout=300)
    if not result:
        print("Erro ao gerar relatório.")
        return False

    # Aguarda artifact
    import time, re
    art_match = re.search(r'artifact[_\s]id[:\s]+(\S+)', result, re.IGNORECASE)
    if art_match:
        art_id = art_match.group(1)
        run_notebooklm("artifact", "wait", art_id, timeout=300)
        run_notebooklm("download", "report", output_path, timeout=60)
    else:
        # Tenta download direto
        run_notebooklm("download", "report", output_path, timeout=60)

    if Path(output_path).exists():
        print(f"Report salvo em: {output_path}")
        return True
    return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--question", help="Pergunta para consultar")
    p.add_argument("--notebook-id", help="ID do notebook (opcional se já configurado)")
    p.add_argument("--generate-report", action="store_true")
    p.add_argument("--output", help="Arquivo de saída para report")
    p.add_argument("--force", action="store_true", help="Ignora cache")
    args = p.parse_args()

    if args.generate_report:
        if not args.output:
            print("--output é obrigatório para --generate-report")
            sys.exit(1)
        success = generate_report(args.output, args.notebook_id)
        sys.exit(0 if success else 1)

    if args.question:
        answer = query(args.question, args.notebook_id, args.force)
        if answer:
            print(answer)
        else:
            print("Sem resposta.", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()

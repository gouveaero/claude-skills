#!/usr/bin/env python3
"""
request_assets.py — Fase 5 do pipeline video-editor
Lê edit_plan.json, verifica assets_needed[] contra pasta assets/, gera manifest.

Uso:
  python request_assets.py --plan <edit_plan.json> --assets-dir <assets/> \
                           --output <assets_needed.json>

Exit codes:
  0 — todos os assets presentes
  2 — assets faltando (escreve manifest, aguarda)
"""
import argparse, json, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--assets-dir", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    assets_dir = Path(args.assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    needed = plan.get("assets_needed", [])
    manifest = []
    missing = []

    for asset in needed:
        path = assets_dir / asset
        found = path.exists()
        manifest.append({
            "asset": asset,
            "expected_path": str(path),
            "found": found,
            "size_bytes": path.stat().st_size if found else None
        })
        if not found:
            missing.append(asset)

    out = {
        "total": len(needed),
        "found": len(needed) - len(missing),
        "missing_count": len(missing),
        "assets": manifest
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2))

    if missing:
        print(f"  {len(missing)} asset(s) faltando:")
        for m in missing:
            print(f"   - {m}  ->  coloque em: {assets_dir / m}")
        print(f"\nManifest salvo em: {args.output}")
        print("Quando todos os assets estiverem em assets/, rode novamente com --skip-request-assets")
        sys.exit(2)

    print(f"Todos os {len(needed)} assets encontrados em {assets_dir}")

if __name__ == "__main__":
    main()

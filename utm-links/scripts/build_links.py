#!/usr/bin/env python3
"""Monta o kit de links UTM de uma campanha Exos e cria os short links.

Uso:
    python3 build_links.py spec.json [--dry-run] [--exosgo /caminho/.exosgo.json]

O spec é um JSON:

    {
      "campaign": "onco_laser_ago26",
      "event_slug": "onco-laser",
      "destination": "https://leticialang.com.br/protocolo-onco-laser/",
      "tag": "[LL][LS][POS][AGO][26]",
      "links": [
        {"label": "Bio Instagram", "slug": "bio",
         "utm": {"source": "organic", "medium": "bio", "term": "instagram"}},
        {"label": "Grupo WhatsApp", "slug": "grupo",
         "url": "https://sndflw.com/i/XXXX"},           // sem UTM
        {"label": "Meta Ads", "slug": "meta", "raw_query":
         "utm_source=meta_ads&utm_medium={{adset.name}}&..."}
      ]
    }

Cada item vira: URL final + short link em exosgo.link. Sem `--dry-run` os
short links são criados de fato (idempotente via findIfExists).

Saída: markdown no formato da Central de Links + um JSON resumo em stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UTM_ORDER = ["source", "medium", "campaign", "content", "term"]


def sanitize(value: str) -> str:
    """Padrão Exos: minúsculas, sem acento, sem espaço, só [a-z0-9_-]."""
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.replace(" ", "_")
    value = re.sub(r"[^a-z0-9_-]", "", value)
    return re.sub(r"_+", "_", value).strip("_")


def build_url(destination: str, utm: dict, campaign: str) -> str:
    """Anexa os utm_* na ordem canônica, preservando query já existente."""
    params = []
    for key in UTM_ORDER:
        raw = campaign if key == "campaign" else utm.get(key)
        if not raw:
            continue
        # Macros de plataforma ({{campaign.name}}, {keyword}) passam intactas.
        value = raw if ("{" in raw) else sanitize(raw)
        params.append(f"utm_{key}={urllib.parse.quote(value, safe='{}.')}")
    if not params:
        return destination
    sep = "&" if "?" in destination else "?"
    return f"{destination}{sep}{'&'.join(params)}"


def shorten(api_base: str, api_key: str, long_url: str, slug: str,
            tag: str | None) -> tuple[str | None, str]:
    """Cria (ou reencontra) o short link. Devolve (url, status)."""
    body = {"longUrl": long_url, "customSlug": slug, "findIfExists": True}
    if tag:
        body["tags"] = [tag]
    req = urllib.request.Request(
        f"{api_base}/short-urls",
        data=json.dumps(body).encode(),
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=30))
        return data.get("shortUrl"), "ok"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:200]
        # Slug ocupado por OUTRO destino: nunca sobrescrever, só relatar.
        return None, f"erro {exc.code}: {detail}"
    except Exception as exc:  # rede fora, DNS, timeout
        return None, f"falha: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="monta as URLs sem criar short link")
    ap.add_argument("--exosgo", type=Path, default=None,
                    help="caminho do .exosgo.json (default: walk-up do cwd)")
    args = ap.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    campaign = sanitize(spec["campaign"])
    event = spec["event_slug"].strip("-")
    destination = spec["destination"]
    tag = spec.get("tag")

    api_base = api_key = None
    if not args.dry_run:
        cfg_path = args.exosgo
        if cfg_path is None:
            for parent in [Path.cwd(), *Path.cwd().parents]:
                candidate = parent / ".exosgo.json"
                if candidate.exists():
                    cfg_path = candidate
                    break
        if cfg_path is None or not cfg_path.exists():
            print("ERRO: .exosgo.json não encontrado — rode com --dry-run ou "
                  "passe --exosgo <caminho>", file=sys.stderr)
            return 1
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        api_base, api_key = cfg["api_base"], cfg["api_key"]

    rows, summary = [], []
    for item in spec["links"]:
        label = item["label"]
        # "slug": "" é intencional — é o link principal, sem sufixo de canal.
        suffix = item.get("slug")
        slug = None if suffix is None else (f"{event}-{suffix}" if suffix else event)

        if "url" in item:                       # link sem UTM (grupo, zoom)
            url = item["url"]
        elif "raw_query" in item:               # macros de plataforma
            sep = "&" if "?" in destination else "?"
            url = f"{destination}{sep}{item['raw_query']}"
        else:
            base = item.get("destination", destination)
            url = build_url(base, item.get("utm", {}), campaign)

        short, status = (None, "dry-run")
        if slug and not args.dry_run:
            short, status = shorten(api_base, api_key, url, slug, tag)

        # Só os links de anúncio precisam da URL completa à vista: as macros
        # ({{campaign.name}}, {keyword}) são coladas na plataforma, e o short
        # link não serve para elas — o encurtador escapa as chaves.
        is_ad = "raw_query" in item
        rows.append((label, short, url, is_ad))
        summary.append({"label": label, "slug": slug, "short": short,
                        "status": status, "url": url, "is_ad": is_ad})

    print("**Links UTM & Encurtados [padrão Exos]**\n")
    for label, short, url, is_ad in rows:
        if is_ad:
            continue
        print(f"*   {label}: {short or url}")

    ads = [r for r in rows if r[3]]
    if ads:
        print("\n**Parâmetros de URL para colar na plataforma de anúncio**\n")
        for label, _short, url, _ in ads:
            print(f"*   {label}: {url}")

    json.dump(summary, sys.stderr, ensure_ascii=False, indent=2)
    print(file=sys.stderr)
    failures = [s for s in summary if s["status"].startswith(("erro", "falha"))]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def md_link(url: str) -> str:
    """`[url](url)` — link de verdade na Central, não texto que parece link.

    URL solta num PUT do ClickUp entra como **texto puro**: no editor ela sai
    preta e não clicável, e ninguém percebe pela API, porque o export
    `content_format=text/md` renderiza QUALQUER URL como `[url](url)` — o
    Markdown de volta parece certo mesmo quando o doc está errado. Só a
    sintaxe explícita no PUT garante o anchor.

    O texto visível continua sendo a própria URL (padrão Daniela da Central,
    `rótulo: link`); o que muda é existir destino.

    Nada de destino entre `<>`: as URLs aqui não têm espaço nem parêntese, e o
    parser do ClickUp não trata a forma com colchete angular de maneira
    confiável. As macros de anúncio (`{{campaign.name}}`, `{keyword}`) passam
    intactas dentro dos parênteses — chave não é caractere especial de link.
    """
    return f"[{url}]({url})"


def shorten(api_base: str, api_key: str, long_url: str, slug: str,
            tags: list[str]) -> tuple[str | None, str]:
    """Cria o short link. Devolve (short_url, status).

    As tags vão no POST, na criação — é a única janela segura para gravá-las.
    Elas tornam o painel legível: o slug é opaco de propósito (`onco-laser-eq`),
    então sem `canal-email` a aba Tags vira uma lista de códigos. A tag é
    interna: só quem tem API key enxerga, o slug público segue discreto.

    ⚠️ NUNCA editar por HTTP (`PATCH /short-urls/{slug}`) numa instância com
    SQLite. O write fica preso em `database is locked`, o worker do RoadRunner
    nunca é devolvido ao pool e, depois de alguns, o Shlink responde 503 em
    TUDO — inclusive nos redirects já distribuídos. Para editar um link que já
    existe, use o CLI, que roda fora do pool:

        ssh vps-exos
        docker exec <container> shlink short-url:edit <slug> -t 'TAG1' -t 'TAG2'

    (`short-url:edit` substitui o conjunto de tags; repita `-t` para cada uma.)
    """
    body = {"longUrl": long_url, "customSlug": slug, "findIfExists": True}
    if tags:
        body["tags"] = tags
    req = urllib.request.Request(
        f"{api_base}/short-urls",
        data=json.dumps(body).encode(),
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=30)).get("shortUrl"), "ok"
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:200]
        if exc.code == 400:
            # `findIfExists` casa pelo conjunto inteiro de critérios, não só
            # pelo slug: se a URL ou as tags mudaram, ele não reconhece o link
            # antigo e esbarra no slug ocupado. Reportar e deixar a decisão com
            # o humano — sobrescrever destino de link já distribuído é pior.
            return None, f"slug ja existe (edite pelo CLI se for intencional): {detail}"
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

        tags = [t for t in (tag, item.get("channel") and f"canal-{sanitize(item['channel'])}") if t]
        short, status = (None, "dry-run")
        if slug and not args.dry_run:
            short, status = shorten(api_base, api_key, url, slug, tags)

        # Só os links de anúncio precisam da URL completa à vista: as macros
        # ({{campaign.name}}, {keyword}) são coladas na plataforma, e o short
        # link não serve para elas — o encurtador escapa as chaves.
        is_ad = "raw_query" in item
        rows.append((label, short, url, is_ad))
        summary.append({"label": label, "slug": slug, "short": short,
                        "status": status, "url": url, "is_ad": is_ad,
                        "tags": tags})

    print("**Links UTM & Encurtados [padrão Exos]**\n")
    for label, short, url, is_ad in rows:
        if is_ad:
            continue
        print(f"*   {label}: {md_link(short or url)}")

    ads = [r for r in rows if r[3]]
    if ads:
        print("\n**Parâmetros de URL para colar na plataforma de anúncio**\n")
        for label, _short, url, _ in ads:
            print(f"*   {label}: {md_link(url)}")

    json.dump(summary, sys.stderr, ensure_ascii=False, indent=2)
    print(file=sys.stderr)
    # "slug ja existe" também sai diferente de zero: o link não foi criado nem
    # atualizado e alguém precisa decidir o que fazer. Sair 0 aqui faria uma
    # reexecução parecer bem-sucedida com metade do kit faltando.
    pending = [s for s in summary
               if s["status"].startswith(("erro", "falha", "slug ja existe"))]
    if pending:
        print(f"\n⚠️  {len(pending)} link(s) exigem atenção:", file=sys.stderr)
        for s in pending:
            print(f"   {s['slug']}: {s['status'][:120]}", file=sys.stderr)
    return 1 if pending else 0


if __name__ == "__main__":
    raise SystemExit(main())

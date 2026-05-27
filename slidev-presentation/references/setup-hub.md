# Setup Hub — Inicialização única do slides-hub

Esse setup roda **uma vez**. Depois disso, todo `deploy-to-hub.sh` reusa a infra.

---

## O que é criado

1. **Repo GitHub** `slides-hub` (privado, org pessoal de Gabriel)
2. **App Coolify** em `coolify.gabrielgouvea.com.br` apontando pro repo
3. **DNS** `slides.gabrielgouvea.com.br` → VPS `187.127.2.180`
4. **Clone local** em `~/.slides-hub`

---

## Pré-requisitos

| Item | Como confirmar |
|---|---|
| `gh` CLI autenticado | `gh auth status` |
| Token Coolify | `~/.config/coolify/personal.env` com `COOLIFY_TOKEN=...` (ou usar API key default) |
| Acesso DNS Hostinger | painel <https://hpanel.hostinger.com/> |
| `.coolify-instance.json` | em `~/Library/CloudStorage/.../🚀_Projects/VPS_Hostinger/` |

---

## Anatomia do repo `slides-hub`

```
slides-hub/
├── decks/                # 1 subpasta por deck publicado
│   ├── lancamento-mba/
│   │   ├── index.html
│   │   ├── assets/...
│   │   └── ...
│   └── exos-pitch/
│       └── ...
├── Dockerfile            # nginx:alpine, sem build node
├── nginx.conf            # SPA routing por subpath
├── index.html            # root, lista decks (gerado pelo deploy)
└── README.md
```

---

## `nginx.conf`

Roteamento por subpath: `/<slug>/...` serve `decks/<slug>/...` com SPA fallback.

```nginx
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;

  # gzip
  gzip on;
  gzip_types text/css application/javascript application/json image/svg+xml;
  gzip_min_length 1024;

  # cache de assets
  location ~* \.(?:js|css|woff2?|ttf|otf|svg|png|jpg|jpeg|webp|avif)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
  }

  # SPA routing por subpath
  location ~ ^/([^/]+)/ {
    try_files $uri $uri/ /$1/index.html;
  }

  # root: lista de decks (index.html gerado)
  location = / {
    try_files /index.html =404;
  }
}
```

## `Dockerfile`

Sem build node — o conteúdo de `decks/<slug>/` já vem buildado.

```dockerfile
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY decks/ /usr/share/nginx/html/
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q --spider http://localhost/ || exit 1
```

---

## Script automatizado: `scripts/setup-hub.sh`

Faz tudo:

1. `gh repo create gouveaero/slides-hub --private --description "Slidev decks hosted at slides.gabrielgouvea.com.br"`
2. Cria local clone em `~/.slides-hub/`
3. Copia templates (`Dockerfile`, `nginx.conf`, `index.html` placeholder)
4. Inicial commit + push
5. Cria App no Coolify via API (precisa `COOLIFY_TOKEN`)
6. Configura domínio `slides.gabrielgouvea.com.br` no App
7. Aciona deploy inicial
8. Verifica DNS (instrui o usuário a adicionar A record no Hostinger se ainda não existir)
9. Aguarda HTTP 200

Execução:

```bash
./scripts/setup-hub.sh
```

---

## DNS manual (se necessário)

No Hostinger hPanel:

1. Domínio `gabrielgouvea.com.br` → DNS Zone Editor
2. Adicionar registro:
   - Type: A
   - Name: `slides`
   - Points to: `187.127.2.180`
   - TTL: 300

Propagar pode levar 10min. Confirmar:

```bash
dig +short slides.gabrielgouvea.com.br
# espera: 187.127.2.180
```

---

## Coolify App config

Via API (o script `setup-hub.sh` faz isso), mas se precisar manual:

| Campo | Valor |
|---|---|
| Project | `cg55ifzqy92nd5luuw3562xi` (Personal) |
| Environment | `ez0f01aercu1jre27k2cp4qq` |
| GitHub App | `uv6o87aad2vxs8ihdmgb122i` |
| Repo | `gouveaero/slides-hub` |
| Branch | `main` |
| Build pack | Dockerfile |
| Domains | `slides.gabrielgouvea.com.br` |
| Port | 80 |
| Healthcheck | HTTP GET `/` |
| Auto-deploy | ON |

---

## Verificação final

```bash
curl -I https://slides.gabrielgouvea.com.br/
# esperado: HTTP/2 200
```

Hub pronto. Daqui em diante, qualquer `deploy-to-hub.sh <slug>` funciona.

---

## Re-setup

Se o hub for destruído (rm -rf, repo deletado), rodar `setup-hub.sh` de novo. Decks publicados se perdem — re-deploy é necessário pra cada um (basta rodar `deploy-to-hub.sh <slug>` no projeto de cada deck).

Para evitar perda, **mantenha o repo `slides-hub` no GitHub** — ele é a fonte da verdade dos decks publicados.

---

## Página index do root (impeccable design)

A página em `/` lista todos os decks publicados em design alinhado com `gabrielgouvea.com.br`. O `setup-hub.sh` cria um placeholder; para o design definitivo "impeccable", roda `/impeccable` na hora do setup ou depois.

**Atualização do index**: cada `deploy-to-hub.sh` chama `regen-hub-index.mjs` (step 2.5) automaticamente — esse script lê todas as subpastas de `decks/`, extrai o `<title>` de cada `index.html` de deck, e regenera o bloco `<ul id="decks">...</ul>` no root `index.html`. Ordenação: mtime descendente (decks recentes no topo).

Pra rodar manualmente (ex: depois de deletar um deck, ou se algo dessincronizou):

```bash
node ~/.claude/skills/slidev-presentation/scripts/regen-hub-index.mjs ~/.slides-hub
cd ~/.slides-hub && git add index.html && git commit -m "chore: refresh hub index" && git push
```

O design custom do `index.html` (CSS embutido, cores, layout) é preservado — o script só substitui o conteúdo do `<ul id="decks">`.

#!/usr/bin/env bash
# setup-hub.sh — inicialização única do slides-hub.
# Cria repo GitHub privado, clone local em ~/.slides-hub, copia template
# Dockerfile + nginx.conf, faz primeiro commit/push, e instrui setup do app
# no Coolify.
#
# Uso: ./setup-hub.sh

set -euo pipefail

hub_dir="${SLIDES_HUB_DIR:-$HOME/.slides-hub}"
repo_org="gouveaero"
repo_name="slides-hub"
domain="slides.gabrielgouvea.com.br"
vps_ip="187.127.2.180"

echo "=== Slides Hub Setup ==="
echo ""

# 1) Verificar gh CLI
if ! command -v gh &>/dev/null; then
  echo "✗ gh CLI não encontrada. Instale: brew install gh" >&2
  exit 1
fi
if ! gh auth status &>/dev/null; then
  echo "✗ gh não autenticado. Rode: gh auth login" >&2
  exit 1
fi
echo "✓ gh CLI ok"

# 2) Verificar se hub já existe local
if [[ -d "$hub_dir" ]]; then
  echo "⚠ $hub_dir já existe. Pulando setup local."
  echo "  Para re-inicializar: rm -rf $hub_dir e rode novamente."
else
  echo ""
  echo ">>> Criando repo GitHub $repo_org/$repo_name"
  if gh repo view "$repo_org/$repo_name" &>/dev/null; then
    echo "  Repo já existe no GitHub."
  else
    gh repo create "$repo_org/$repo_name" --private \
      --description "Slidev decks hosted at $domain"
  fi

  echo ">>> Clonando para $hub_dir"
  gh repo clone "$repo_org/$repo_name" "$hub_dir"
fi

cd "$hub_dir"

# 3) Garantir arquivos base
echo ""
echo ">>> Criando Dockerfile, nginx.conf, index.html, README"

mkdir -p decks

cat > Dockerfile <<'EOF'
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY decks/ /usr/share/nginx/html/
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q --spider http://localhost/ || exit 1
EOF

cat > nginx.conf <<'EOF'
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  index index.html;

  gzip on;
  gzip_types text/css application/javascript application/json image/svg+xml;
  gzip_min_length 1024;

  location ~* \.(?:js|css|woff2?|ttf|otf|svg|png|jpg|jpeg|webp|avif)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
  }

  location ~ ^/([^/]+)/ {
    try_files $uri $uri/ /$1/index.html;
  }

  location = / {
    try_files /index.html =404;
  }
}
EOF

# Index placeholder (será regenerado pelo deploy-to-hub e refinado via /impeccable)
cat > index.html <<EOF
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slides · Gabriel Gouvêa</title>
<style>
  body { font-family: 'Inter', system-ui, sans-serif; background: #0b1020; color: #e2e8f0; margin: 0; padding: 4rem 2rem; min-height: 100vh; }
  .wrap { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 2.4rem; letter-spacing: -0.02em; margin-bottom: 0.5rem; }
  .sub { color: #94a3b8; margin-bottom: 3rem; font-size: 1.05rem; }
  ul { list-style: none; padding: 0; display: grid; gap: 0.8rem; }
  a { color: #5eead4; text-decoration: none; display: block; padding: 1rem 1.2rem; border: 1px solid rgba(94, 234, 212, 0.2); border-radius: 12px; transition: background 0.2s, border-color 0.2s; }
  a:hover { background: rgba(94, 234, 212, 0.08); border-color: rgba(94, 234, 212, 0.5); }
  .footer { margin-top: 4rem; color: #64748b; font-size: 0.85rem; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Slides</h1>
  <p class="sub">Decks publicados por Gabriel Gouvêa.</p>
  <ul id="decks">
    <!-- gerado dinamicamente pelo deploy-to-hub.sh -->
    <li><em>Nenhum deck publicado ainda.</em></li>
  </ul>
  <p class="footer">— <a href="https://gabrielgouvea.com.br" style="display:inline; padding:0; border:0; color:#94a3b8;">gabrielgouvea.com.br</a></p>
</div>
</body>
</html>
EOF

cat > README.md <<EOF
# slides-hub

Slidev decks publicados em <https://$domain>.

Cada subpasta de \`decks/\` é um deck. URL: \`https://$domain/<nome-da-pasta>/\`.

Deploy automatizado via \`slidev-presentation\` skill: \`scripts/deploy-to-hub.sh <slug>\`.

Setup inicial: \`scripts/setup-hub.sh\`.
EOF

# 4) Commit inicial
if [[ -z "$(git log --oneline 2>/dev/null)" ]]; then
  echo ">>> Commit inicial"
  git add Dockerfile nginx.conf index.html README.md
  mkdir -p decks
  touch decks/.gitkeep
  git add decks/.gitkeep
  git -c user.email="gabrielgouvea@noreply" -c user.name="setup-hub" commit -m "chore: initial hub setup"
  git push -u origin main
else
  echo "✓ Repo já tem commits, pulando initial commit"
fi

# 5) DNS check
echo ""
echo ">>> Verificando DNS de $domain"
resolved=$(dig +short "$domain" | head -1)
if [[ "$resolved" == "$vps_ip" ]]; then
  echo "✓ DNS resolvendo corretamente para $vps_ip"
else
  echo "⚠ DNS de $domain ainda não aponta para $vps_ip (resolveu: ${resolved:-vazio})."
  echo ""
  echo "  Vá no Hostinger hPanel → DNS Zone Editor → gabrielgouvea.com.br:"
  echo "    Type: A"
  echo "    Name: slides"
  echo "    Points to: $vps_ip"
  echo "    TTL: 300"
  echo ""
  echo "  Aguarde propagação (até 10min) e re-rode esse script para concluir."
fi

# 6) Coolify app (manual ou via API)
echo ""
echo "=== Próximo passo (Coolify) ==="
echo ""
echo "Crie o App no Coolify:"
echo "  https://coolify.gabrielgouvea.com.br"
echo ""
echo "Config:"
echo "  • Project: Personal (cg55ifzqy92nd5luuw3562xi)"
echo "  • Source: GitHub App → repo $repo_org/$repo_name → branch main"
echo "  • Build pack: Dockerfile"
echo "  • Port: 80"
echo "  • Domains: $domain"
echo "  • Auto-deploy: ON"
echo ""
echo "Após o primeiro deploy, verifique:"
echo "  curl -I https://$domain/"
echo ""
echo "=== Hub local pronto em $hub_dir ==="

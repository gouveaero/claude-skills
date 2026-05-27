# Deploy — Auto-deploy para slides.gabrielgouvea.com.br/<slug>

Fluxo de uma única invocação: `scripts/deploy-to-hub.sh <slug>`. O script faz tudo.

---

## Quando deploy acontece

Na **fase 2 (Discovery)** do workflow, a skill pergunta:

> "Esse deck vai pro ar em `slides.gabrielgouvea.com.br`? Se sim, qual slug você quer usar? (sugestão: `<slug-auto>`)"

Se sim, ao final da fase 4 (Generation + verificação visual), a skill executa o deploy automaticamente.

Se não, o deck fica só local.

---

## Pré-requisitos (uma única vez)

O hub `slides-hub` precisa estar inicializado. Se não estiver, rodar `scripts/setup-hub.sh` primeiro (instruções em [setup-hub.md](./setup-hub.md)).

A skill detecta automaticamente — se o hub não existe, oferece setup antes de prosseguir com deploy.

---

## Fluxo passo-a-passo

`./scripts/deploy-to-hub.sh <slug> [<path-do-deck>]` executa:

### 1. Build estático com base path correto

```bash
cd <deck-path>
npm run build -- --base /<slug>/
```

O flag `--base /<slug>/` faz o Slidev gerar URLs relativas com prefixo `/<slug>/` — necessário porque o deck será servido em subpath, não em raiz.

Output: pasta `dist/` no deck.

### 2. Sync para o slides-hub

```bash
rm -rf $SLIDES_HUB_DIR/decks/<slug>/
cp -r <deck-path>/dist $SLIDES_HUB_DIR/decks/<slug>/
```

Sobrescreve o slug se já existir (a checagem de colisão acontece **antes** do deploy, na fase de briefing — via `scripts/check-slug-collision.sh`).

### 2.5. Regenerar `index.html` do hub

```bash
node scripts/regen-hub-index.mjs $SLIDES_HUB_DIR
```

Atualiza `slides-hub/index.html` com a lista de todos os decks publicados em `decks/*` (ordenados por mtime descendente). Cada deck vira `<li><a href="/<slug>/">{title}</a></li>`. Sem esse passo, o root `slides.gabrielgouvea.com.br/` mostra placeholder estático apesar dos decks existirem.

### 3. Commit e push

```bash
cd $SLIDES_HUB_DIR
git add decks/<slug>/
git commit -m "deploy: <slug>"
git push origin main
```

### 4. Aguardar Coolify redeploy

GitHub App webhook → Coolify detecta push → builda imagem (apenas nginx; o `dist/` já vem pronto) → publica.

Script faz poll na URL pública até retornar 200 (até 180s).

### 5. Verificar

```bash
curl -I https://slides.gabrielgouvea.com.br/<slug>/
```

200 OK = sucesso. 4xx/5xx = falha (verifique Coolify dashboard).

---

## Variáveis de ambiente

| Env | Default | Descrição |
|---|---|---|
| `SLIDES_HUB_DIR` | `~/.slides-hub` | Onde o clone local do repo `slides-hub` vive |

Override:

```bash
SLIDES_HUB_DIR=/custom/path ./scripts/deploy-to-hub.sh meu-slug
```

---

## Re-deploy / overwrite

Roda o mesmo comando — `deploy-to-hub.sh <slug>` sobrescreve o conteúdo do slug em `decks/<slug>/`. Histórico fica no git.

Para rollback:

```bash
cd $SLIDES_HUB_DIR
git log decks/<slug>/      # encontra o commit anterior
git revert <commit-hash>   # ou git checkout <hash> -- decks/<slug>/ + commit
git push
```

---

## Troubleshooting

| Sintoma | Causa provável | Fix |
|---|---|---|
| 404 ao abrir a URL | nginx routing | confirme que `nginx.conf` tem `location ~ ^/([^/]+)/ { try_files $uri $uri/ /$1/index.html; }` |
| CSS/JS 404 | `--base` ausente ou diferente do slug | re-rodar build com `--base /<slug>/` exato |
| Slide preview funciona mas deploy fica branco | `theme:` no frontmatter referencia tema não instalado | confirmar que tema está em `dependencies` do `package.json` do deck |
| `git push` rejected | push paralelo de outro deploy | `git pull --rebase` no `slides-hub` e re-tentar |
| Deploy não dispara no Coolify | webhook não conectado | verificar GitHub App está ativo no repo `slides-hub` (settings → integrations) |

---

## Anatomia do `slides-hub` (referência)

Estrutura do repo (criado pelo setup-hub):

```
slides-hub/
├── decks/
│   ├── lancamento-mba/      # dist/ Slidev pronto
│   ├── exos-pitch/
│   └── ...
├── Dockerfile               # nginx:alpine
├── nginx.conf               # SPA routing por subpath
├── index.html               # root listing (regenerado por regen-hub-index.mjs em cada deploy)
└── README.md
```

Detalhes em [setup-hub.md](./setup-hub.md).

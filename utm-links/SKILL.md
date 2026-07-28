---
name: utm-links
description: Use quando o usuário quiser os links rastreáveis de uma campanha/lançamento Exos — "cria as UTMs do lançamento", "links de captação com UTM", "kit de links da campanha", "link encurtado do evento", "monta os links pro disparo/grupo/e-mail/Manychat", "link de suporte do evento", "atualiza a Central de Links". Gera o set completo de URLs no padrão Exos de UTM (exosmkt.com.br/padronizacao-utm), cria os short links em exosgo.link (Shlink), monta o link de suporte personalizado do evento e grava tudo na Central de Links do ClickUp. NÃO use para instalar pixel/CAPI (tracking-pixels) nem para configurar custom fields de atribuição no CRM (growai-utm).
---

# utm-links — kit de links rastreáveis de uma campanha Exos

Uma campanha só é mensurável se cada canal chega com a sua UTM. Na prática o
que trava isso não é a teoria — é a chatice de montar 15 URLs à mão sem errar
um `utm_medium`. Esta skill produz o kit inteiro de uma vez: URLs no padrão,
short links em `exosgo.link`, link de suporte do evento, e o registro na
Central de Links do lançamento.

**A saída é sempre mostrada no chat**, mesmo quando a Central é atualizada.

## Antes de começar: o que você precisa saber

Reúna estes cinco dados. Infira o que der dos arquivos do cliente; **pergunte
só o que não der para inferir** (uma pergunta só, agrupada):

| Dado | Como inferir |
|---|---|
| **Cliente** | pasta de trabalho atual (`Leticia_Lang/`, `Elen_Tolentino/`…) |
| **URL de destino** | a LP de captação do lançamento — geralmente já está na Central |
| **Tag do lançamento** | `[LL][LS][POS][AGO][26]` — de `.tracking.json` (`funis.*.tag_growai`), do nome da Central ou do usuário |
| **Slug do evento** | derive do nome do evento: "Workshop Protocolo ONCO+ Laser" → `onco-laser`. Curto (≤ 14 chars), reconhecível, kebab-case |
| **Nome do evento + data** | para a mensagem do link de suporte |

Configs relevantes, por walk-up a partir do cwd:

- `<Cliente>/.tracking.json` — `primary_domain`, `client_code`, bloco `funis`
- `Exos/.exosgo.json` — credencial do encurtador (**gitignored**)
- `~/.config/clickup/token.env` — token da API do ClickUp

## Passo 1 — Montar as URLs com UTM

Leia [references/utm-taxonomy.md](references/utm-taxonomy.md) (dicionário e
regras) e [references/channel-defaults.md](references/channel-defaults.md)
(a matriz de canais padrão).

`utm_campaign` é o mesmo em todos os canais: derive do evento em snake_case
com mês/ano — `onco_laser_ago26`. Sanitize **todo** valor: minúsculas, sem
acento, espaço vira `_`, só `[a-z0-9_-]`.

Gere um link por canal da matriz. Inclua os canais que o usuário pediu **e**
os essenciais que faltarem — bio, stories, e-mail e os dois de tráfego pago
raramente não se aplicam. Se o lançamento tem ativos com URL própria (pesquisa
Typebot, e-book, grupo de WhatsApp), gere link para eles também: eles também
são pontos de entrada.

⚠️ **Meta Ads e Google Ads não levam valores fixos** — levam as macros da
plataforma (`{{campaign.name}}`, `{keyword}`…), coladas no campo de parâmetros
de URL da conta. Ver a taxonomia para os dois templates completos.

## Passo 2 — Criar os short links em exosgo.link

Todo link do kit ganha um short link.

### O slug precisa passar confiança, não denunciar rastreio

Quem recebe o link tem que bater o olho e reconhecer **o evento**. Um
`exosgo.link/onco-laser-email-base-total` grita "você está sendo segmentado" e
derruba a taxa de clique; `exosgo.link/onco-laser` parece o link oficial —
porque é.

Regra: **o slug nomeia o destino, nunca o canal.** A distinção por canal vira
um sufixo curto e opaco, que só a agência decodifica (a legenda fica na Central
e no relatório de cliques do Shlink).

| Tipo | Slug | Exemplo |
|---|---|---|
| Link principal (bio, o mais visível) | `<evento>` | `onco-laser` |
| Demais canais | `<evento>-<código>` | `onco-laser-e` |
| Ativo com nome próprio | `<evento>-<ativo>` | `onco-laser-ebook`, `onco-laser-suporte`, `onco-laser-grupo`, `onco-laser-pesquisa` |

Ativos com nome próprio ficam por extenso de propósito: "suporte", "ebook" e
"grupo" descrevem o que a pessoa vai receber — isso **aumenta** a confiança.
O que não pode aparecer é a mecânica de segmentação (`-email-base-total`,
`-retargeting`, `-lista-fria`).

Códigos de canal (use estes; são estáveis entre campanhas):

| Código | Canal | Código | Canal |
|---|---|---|---|
| _(nenhum)_ | bio / principal | `w` | WhatsApp disparo |
| `ma` | Manychat | `g` | grupos WhatsApp |
| `s` | stories | `mt` | Meta Ads |
| `r` | reels / feed | `gg` | Google Ads |
| `d` | DM | `tk` | TikTok Ads |
| `y` | YouTube | `e` / `eq` | e-mail base / quentes |

```bash
KEY=$(python3 -c "import json;print(json.load(open('.exosgo.json'))['api_key'])")
curl -s -X POST https://exosgo.link/rest/v3/short-urls \
  -H "X-Api-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"longUrl":"<URL COM UTM>","customSlug":"<evento>-<canal>",
       "tags":["<tag-do-lancamento>"],"findIfExists":true}'
```

- **`findIfExists: true` é obrigatório** — torna a criação idempotente. Rodar
  a skill de novo devolve o link existente em vez de estourar erro de slug
  duplicado. Só omita se o usuário quiser deliberadamente um slug novo.
- Se ainda assim vier `INVALID_SLUG`/409, o slug já existe apontando para
  **outro** destino: relate ao usuário e proponha um sufixo (`-v2`), **nunca
  sobrescreva** — pode haver material distribuído apontando pra lá.
- `forwardQuery` é `true` por padrão: parâmetros extras no short link passam
  para o destino. É o que permite `exosgo.link/x?fbclid=...` continuar íntegro.

## Passo 3 — Link de suporte do evento

Cada expert tem **um** número oficial e uma rota `/suporte` no próprio domínio,
que aceita a mensagem por query string:

```
https://<dominio>/suporte?m=<mensagem do evento, URL-encoded>
```

Escreva a mensagem na voz do lead, identificando de onde ele veio — é isso que
faz o atendente saber o contexto sem perguntar:

> `Olá! Vim do Workshop Protocolo ONCO+ Laser (12/08) e preciso de ajuda.`

Encode com `urllib.parse.quote` (não monte a query na mão). Encurte como
`<evento>-suporte`. Sites em inglês (Kleber) levam a mensagem em inglês.

Dois detalhes que mordem:

- **Não termine a mensagem com ponto final.** O autolink do ClickUp (e de
  vários clientes de e-mail) deixa o `.` de fora do link, e a URL registrada
  fica truncada. Termine com `!` ou sem pontuação.
- Sites com `trailingSlash: true` (Letícia, Elen) devolvem 308 de `/suporte`
  para `/suporte/`. Use **`/suporte/?m=`** com a barra e economize um hop.

**Nunca** coloque o número cru, `wa.me/...` ou `api.whatsapp.com/send?...` no
material — sempre a URL do domínio do cliente. Quando o número muda, muda em
um arquivo só. Números oficiais: `<Cliente>/NUMEROS_OFICIAIS.md` e o CLAUDE.md
do workspace Exos.

Se a campanha for longa e merecer rota própria (`/suporte-<evento>`), diga isso
ao usuário — mas o `?m=` resolve sem deploy e é o caminho padrão.

## Passo 4 — Gravar na Central de Links

Ache o doc pela tag do lançamento (a lista é longa, precisa paginar):

```bash
source ~/.config/clickup/token.env
curl -s -H "Authorization: $CLICKUP_TOKEN" \
  "https://api.clickup.com/api/v3/workspaces/9013012202/docs?limit=100&next_cursor=<cursor>"
```

Filtre por nome contendo `Central de Link` **e** a tag. Havendo mais de um
match (existem duplicatas históricas no workspace), prefira o de `id` maior
(mais recente) e diga ao usuário qual você escolheu.

Pegue a página e o conteúdo atual, **anexe** a seção no final e faça PUT:

```bash
# GET das páginas
curl -s -H "Authorization: $CLICKUP_TOKEN" \
  "https://api.clickup.com/api/v3/workspaces/9013012202/docs/<docId>/pages?content_format=text%2Fmd"
# PUT (content_edit_mode append evita reescrever o que já existe)
curl -s -X PUT -H "Authorization: $CLICKUP_TOKEN" -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v3/workspaces/9013012202/docs/<docId>/pages/<pageId>" \
  -d '{"content":"<seção nova>","content_edit_mode":"append","content_format":"text/md"}'
```

Formato da seção — padrão Daniela da Central (bullets `rótulo: link`, **sem
tabelas, sem observações, sem blockquote**).

**Só o short link vai na lista.** A URL completa com UTM não entra: ela é
ilegível, quebra em duas linhas e ninguém copia da Central mesmo — quem quiser
auditar abre o link ou o painel do Shlink. As duas exceções são Meta e Google
Ads, que **precisam** da URL crua porque as macros vão coladas na plataforma —
essas ficam numa segunda seção, com o nome dizendo o que fazer com elas.

```
**Links UTM & Encurtados [padrão Exos]**

*   Bio Instagram: https://exosgo.link/onco-laser
*   E-mail — base total: https://exosgo.link/onco-laser-e
*   WhatsApp — grupos do evento: https://exosgo.link/onco-laser-g
*   Suporte do evento: https://exosgo.link/onco-laser-suporte

**Parâmetros de URL para colar na plataforma de anúncio**

*   Meta Ads: https://.../?utm_source=meta_ads&utm_medium={{adset.name}}&...
*   Google Ads: https://.../?utm_source=google_ads&utm_medium={adgroupid}&...
```

`scripts/build_links.py` já emite exatamente esse formato: itens com
`raw_query` (os de anúncio) caem na segunda seção, o resto vira short link.

Regras de segurança:

- **Mostre a seção montada no chat antes do PUT.** É escrita num doc que o time
  inteiro usa.
- Nunca substitua o conteúdo existente. Se a API não aceitar `append`, faça
  GET → concatene → PUT com o conteúdo completo.
- Se não existir Central para a tag, **não crie doc novo** — entregue o kit no
  chat e avise que a Central não foi encontrada.

## Passo 5 — Fechar

Entregue no chat no mesmo formato da Central: short links na lista, URL crua só
para Meta e Google. Diga explicitamente:

- quais slugs foram criados (e quais já existiam)
- o link de suporte gerado e a mensagem que ele preenche
- que Meta/Google Ads usam macros e onde colar (campo de parâmetros de URL da
  conta, não no link do anúncio)
- se a Central foi atualizada, com o nome do doc

## Coisas que dão errado

| Sintoma | Causa |
|---|---|
| Short link 404 | slug criado num domínio diferente do default; confira `DEFAULT_DOMAIN` do Shlink |
| UTM não aparece no CRM | a captura na origem é outro problema — ver skill `growai-utm`; a URL estar certa não basta |
| `utm_campaign` diferente entre canais | derive uma vez e reuse; divergência fragmenta o relatório |
| Acento quebrado na mensagem do suporte | montou a query na mão; use `urllib.parse.quote`/`URLSearchParams` |
| Central sobrescrita | fez PUT sem ler o conteúdo antes |

# Taxonomia UTM — padrão Exos

Espelho do dicionário canônico em
`Exos/Institucional/website/lib/utm-builder.ts` (fonte única da página pública
`exosmkt.com.br/padronizacao-utm` e do PDF `public/guia-padronizacao-utm-exos.pdf`).
Ao divergir, o `utm-builder.ts` vence — e este arquivo deve ser atualizado.

## Regras de formatação (inegociáveis)

1. **Sempre minúsculas.** O GA trata `Meta_Ads` e `meta_ads` como coisas
   diferentes e fragmenta o relatório.
2. **Sem espaços.** Underline `_` separa palavras dentro de um parâmetro.
   Hífen `-` separa conceitos hierárquicos (`2026-02-lancamento`).
3. **Sem acentos.** Só `a–z`, `0–9`, `_`, `-`.
4. **`meta_ads` unificado** — nunca `fb_ads`, `facebook_ads`, `facebook`,
   `meta`. A separação por plataforma vai no `utm_term`.
5. **Nunca UTM em link interno.** Só em links externos apontando pro site —
   UTM interno sobrescreve a origem real e corrompe a atribuição.
6. **Consistência absoluta.** Definido o padrão, não varie.

Ordem dos parâmetros na URL:
`utm_source → utm_medium → utm_campaign → utm_content → utm_term`

### Sanitizador canônico

```python
import re, unicodedata

def sanitize(v: str) -> str:
    v = unicodedata.normalize("NFD", v.lower())
    v = "".join(c for c in v if unicodedata.category(c) != "Mn")
    v = v.replace(" ", "_")
    v = re.sub(r"[^a-z0-9_-]", "", v)
    v = re.sub(r"_+", "_", v)
    return v.strip("_")
```

## utm_source (obrigatório)

| Valor | Plataforma |
|---|---|
| `organic` | tráfego orgânico (posts, stories, bio, grupos, DM) |
| `meta_ads` | Facebook, Instagram, Messenger, Audience Network |
| `google_ads` | Search, Display, YouTube Ads, PMax, Shopping |
| `email` | e-mail marketing (ActiveCampaign, GrowAI, Mailchimp) |
| `whatsapp` | WhatsApp — disparo oficial, grupos, SendFlow |
| `sms` | SMS — disparo de lista (GrowAI, operadora) |
| `youtube` | YouTube orgânico (descrição, cards, end screens) |
| `tiktok_ads` | TikTok Ads |
| `twitter_ads` | Twitter/X Ads |
| `linkedin_ads` | LinkedIn Ads |

## utm_medium (obrigatório)

É o que define o channel grouping. O conteúdo varia por tipo de tráfego:

| Tráfego | O que colocar | Exemplos |
|---|---|---|
| Pago | conjunto de anúncios / segmentação | `semelhante_1pct_alunos`, `retargeting_visitantes_30d` |
| E-mail | nome da lista ou segmento | `base_total`, `leads_quentes`, `compradores_ebook` |
| Orgânico | posicionamento (lista fechada abaixo) | `stories`, `bio`, `reels` |
| WhatsApp | lista ou segmento de envio | `disparo_lista`, `grupos`, `lista_vip` |
| SMS | lista ou segmento de envio | `disparo_lista`, `lista_vip` |

Lista fechada de mediums orgânicos (`ORGANIC_MEDIUMS`):
`stories`, `bio`, `reels`, `feed`, `dm`, `manychat`, `youtube`, `blog`,
`grupos`, `tiktok`, `threads`, `outros`

## utm_campaign (obrigatório)

Corresponde **exatamente** ao nome da campanha na plataforma quando é tráfego
pago. Nos demais canais, é o tema/lançamento — e deve ser **o mesmo valor em
todos os canais da campanha**, senão o relatório fragmenta.

Convenção Exos para lançamento: `<evento>_<mes><ano>` → `onco_laser_ago26`.

> A tag de colchetes (`[LL][LS][POS][AGO][26]`) **não** vai no `utm_campaign`.
> Ela é do SendFlow/GrowAI (nome de campanha WhatsApp e tag do contato) — outro
> namespace. Use-a como `tag` no Shlink, para agrupar os short links.

## utm_content (recomendado)

| Tráfego | O que colocar |
|---|---|
| Pago | nome do anúncio/criativo (`video_depoimento_v2`) |
| E-mail | nome do e-mail (`email_3_escassez`) |
| Orgânico | data do post ou ID (`2026-02-15`) |
| WhatsApp | tipo da mensagem (`msg_abertura`, `msg_lembrete`) |

## utm_term (opcional) — granularidade de posicionamento

| Source | Valores |
|---|---|
| `meta_ads` | `facebook`, `instagram`, `audience_network`, `messenger` |
| `google_ads` | `search`, `display`, `youtube_instream`, `youtube_discovery`, `performance_max`, `shopping` — ou a palavra-chave |
| `tiktok_ads` | `feed`, `topview`, `branded_hashtag` |
| `linkedin_ads` | `feed`, `inmail`, `sidebar` |
| orgânico | rede de origem: `instagram`, `youtube`, `tiktok`, `facebook` |
| `email` | não usa |

## Tráfego pago: macros, não valores fixos

Colar no campo de **parâmetros de URL** da conta (Meta: nível de anúncio;
Google: "opções de URL da campanha"). Assim cada anúncio se identifica sozinho
e ninguém precisa lembrar de trocar UTM ao duplicar criativo.

**Meta Ads:**

```
utm_source=meta_ads&utm_medium={{adset.name}}&utm_campaign={{campaign.name}}&utm_content={{ad.name}}&utm_term={{placement}}
```

**Google Ads (ValueTrack):**

```
utm_source=google_ads&utm_medium={adgroupid}&utm_campaign={campaignid}&utm_content={creative}&utm_term={keyword}
```

Os nomes de campanha/conjunto/anúncio na plataforma precisam já estar no
padrão (minúsculas, sem acento) — a macro copia o nome como ele está.

## Exemplos completos

```
?utm_source=meta_ads&utm_medium=semelhante_1pct_alunos&utm_campaign=lancamento_curso_open_bite&utm_content=video_depoimento_v2&utm_term=facebook
?utm_source=email&utm_medium=base_total&utm_campaign=sequencia_boas_vindas&utm_content=email_3_escassez
?utm_source=organic&utm_medium=stories&utm_campaign=conteudo_elasticos&utm_content=2026-02-15&utm_term=instagram
?utm_source=whatsapp&utm_medium=grupos&utm_campaign=promo_black_friday&utm_content=msg_abertura
```

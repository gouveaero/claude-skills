# Canais padrão de um lançamento Exos

Matriz de partida. Gere **todos** os que fizerem sentido para a campanha, não
só os que o usuário lembrou de pedir — o custo de um link a mais é zero e o
custo de um canal sem UTM é um lançamento inteiro sem atribuição.

`<campanha>` = o `utm_campaign` derivado uma vez e reusado em todos.
`<evento>` = o slug curto do evento, usado no short link. Os slugs abaixo
seguem a regra de discrição do SKILL.md: nomeiam o evento, não o canal.

## Orgânico próprio

| Canal | source | medium | term | content | slug |
|---|---|---|---|---|---|
| Bio Instagram | `organic` | `bio` | `instagram` | — | `<evento>` _(sem sufixo)_ |
| Stories | `organic` | `stories` | `instagram` | data do post | `<evento>-s` |
| Feed / Reels | `organic` | `reels` | `instagram` | — | `<evento>-r` |
| DM manual | `organic` | `dm` | `instagram` | — | `<evento>-d` |
| Manychat (automação IG) | `organic` | `manychat` | `instagram` | — | `<evento>-ma` |
| YouTube (descrição/cards) | `youtube` | `descricao` | — | — | `<evento>-y` |
| Bio YouTube / about | `youtube` | `bio` | — | — | `<evento>-yb` |

## E-mail

| Canal | source | medium | content | slug |
|---|---|---|---|---|
| Base total | `email` | `base_total` | nome do e-mail | `<evento>-e` |
| Leads quentes / segmento | `email` | `leads_quentes` | nome do e-mail | `<evento>-eq` |
| Compradores | `email` | `compradores` | nome do e-mail | `<evento>-ec` |

Quando a sequência tem muitos e-mails, varie o `utm_content` por e-mail
(`email_1_convite`, `email_2_lembrete`) mantendo um short link só, ou crie um
short por e-mail se o cliente quiser medir clique a clique.

## WhatsApp

| Canal | source | medium | content | slug |
|---|---|---|---|---|
| Disparo do aparelho oficial | `whatsapp` | `disparo_lista` | `msg_<n>` | `<evento>-w` |
| Grupos de WhatsApp | `whatsapp` | `grupos` | `msg_<n>` | `<evento>-g` |
| Suporte / atendimento 1:1 | `whatsapp` | `suporte` | — | `<evento>-ws` |

O **link do grupo** (roteador SendFlow `sndflw.com/i/...`) não leva UTM — ele
não é uma página do site. Encurte mesmo assim (`<evento>-grupo`): fica no
padrão e o clique vira métrica.

## Tráfego pago (macros — ver utm-taxonomy.md)

| Canal | slug | onde colar |
|---|---|---|
| Meta Ads | `<evento>-mt` | campo "parâmetros de URL" no nível do anúncio |
| Google Ads | `<evento>-gg` | "opções de URL da campanha" |
| TikTok Ads | `<evento>-tk` | parâmetros de URL do anúncio |

O short link de anúncio existe para registro na Central; **na plataforma cole
a URL completa com macros**, não o encurtado — encurtador em anúncio pode ser
reprovado na revisão e atrapalha a checagem de domínio.

## Ativos do lançamento (não são "canais", mas precisam de link)

| Ativo | Tratamento | slug |
|---|---|---|
| Pesquisa (Typebot) | UTM do canal que distribui a pesquisa | `<evento>-pesquisa` |
| E-book / isca | UTM do canal que distribui | `<evento>-ebook` |
| Página de vendas | UTM por canal, quando abrir | `<evento>-vendas` |
| Checkout | sem UTM (a plataforma tem a sua) | `<evento>-checkout` |
| Grupo de WhatsApp | sem UTM (roteador SendFlow) | `<evento>-grupo` |
| Suporte do evento | `/suporte?m=<mensagem>` | `<evento>-suporte` |
| Zoom / sala do evento | sem UTM | `<evento>-zoom` |

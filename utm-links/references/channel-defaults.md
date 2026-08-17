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
| **Página do Facebook** (posts e about) | `organic` | `feed` | `facebook` | — | `<evento>-fb` |
| **Área de membros** (base de alunos) | `organic` | `area_membros` | — | — | `<evento>-am` |

### Área de membros = origem, não destino

O link é da **página de captação**, colocado *dentro* da área de membros
(banner, aviso, aula) para a base de alunos que já comprou. É audiência quente e
gratuita, quase sempre esquecida no plano de mídia — e sem UTM própria ela
aparece no relatório como tráfego direto, escondendo o melhor canal da operação.

`utm_medium=area_membros` **estende** a lista fechada de mediums orgânicos do
guia publicado. É proposital: jogar em `outros` destrói a leitura. Ao usar pela
primeira vez num cliente, avise o usuário para incluir o valor em
`Institucional/website/lib/utm-builder.ts`, senão o padrão publicado e o que a
agência usa na prática divergem.

Se a plataforma de membros injeta token de acesso na URL, esse link é pessoal:
não encurte nem publique — vale só o link limpo da LP.

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

## SMS

| Canal | source | medium | content | slug |
|---|---|---|---|---|
| Disparo de lista (captação) | `sms` | `disparo_lista` | `msg_<n>` | `<evento>-sms` |
| Disparo de lista (fase de vendas) | `sms` | `disparo_lista` | `vendas` | `<evento>-oferta-sms` |
| Segmento / lista VIP | `sms` | `lista_vip` | `msg_<n>` | `<evento>-sms` |

**SMS entra sempre, nas duas fases** — captação e vendas. É o canal mais fácil
de esquecer porque quem dispara costuma ser outra pessoa (GrowAI ou operadora),
e o link chega pronto de algum lugar; sem UTM própria o SMS inteiro cai como
tráfego direto e o relatório credita o canal errado.

O SMS tem um agravante sobre os outros canais: **a mensagem é curta e o link é
quase todo o corpo dela**, então URL longa com UTM colada é impraticável — o
short link não é conveniência, é requisito. Gere-o mesmo quando o disparo ainda
não estiver contratado.

O sufixo de fase segue o que o lançamento já usa (`-oferta` é o padrão; alguns
lançamentos usam `-vendas`). Precedente validado: `wotf-sms` (Kleber, WOTF
ago/26) e os seis links de agosto/26 — Daniela (`clareamento-sms`), Letícia
(`onco-laser-sms`) e Elen (`estomato-laser-sms`), cada um com o par de vendas.

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
| Pesquisa pós-evento (certificado) | UTM do canal que distribui | `<evento>-pesquisa-pos` |
| E-book / isca | UTM do canal que distribui | `<evento>-ebook` |
| Página de vendas | UTM por canal, quando abrir | `<evento>-vendas` |
| Checkout | sem UTM (a plataforma tem a sua) | `<evento>-checkout` |
| Grupo de WhatsApp | sem UTM (roteador SendFlow) | `<evento>-grupo` |
| Suporte do evento | `/suporte?m=<mensagem>` | `<evento>-suporte` |
| Time de vendas (comercial) | `/comercial?m=<mensagem de matrícula>` — ver Passo 3b do SKILL.md | `<evento>-atendimento` |
| Zoom / sala do evento | sem UTM | `<evento>-zoom` |

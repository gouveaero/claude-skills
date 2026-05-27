# Carousel patterns — Instagram 2026

Pesquisa 2026 (Hootsuite, Pano, FlowShorts, MarketingAgent) confirma: carrosséis Instagram têm **1.9× mais alcance** e **3× mais engajamento, shares e comentários** que post único. O algoritmo recompensa **swipes**, não scrolls.

Esses padrões são **regras**, não sugestões. A skill rejeita o outline se forem violados.

---

## Estrutura AIDA (Attention → Interest → Desire → Action)

| Slide | Papel | Cap palavras | Exemplo |
|---|---|---|---|
| 1 | **Hook** — problema relatable ou linha provocativa | ≤12 | "Você está perdendo R$ 200k/ano e não sabe." |
| 2-3 | **Interest** — eleva curiosidade, contextualiza | ≤12 cada | "98% dos founders fazem isso errado." |
| 4-7 | **Education** — entrega passos, frameworks, prova | ≤12 cada | Steps numerados, mini-tutorials |
| Último | **Action** — CTA explícito + handle | ≤12 | "Salva esse post pra não perder. @gouveaero" |

Total recomendado: **6–13 slides**. <6 perde narrativa; >13 mata engajamento.

---

## Regra rígida — cap de 12 palavras por slide

Pesquisa Pano: se um slide exige >0.7s pra ler, **a audiência já foi**.

| Bad (18 palavras) | Good (8 palavras) |
|---|---|
| "Para entender por que carrosséis no Instagram performam tão melhor que posts únicos, precisamos olhar pro algoritmo" | "Por que carrosséis bombam? O algoritmo ama swipes." |

A skill conta palavras de cada slide (excluindo HTML tags e frontmatter) via `scripts/count-words-per-slide.sh`. Se algum slide ultrapassa 12, **rejeita o outline com a frase culpada citada**.

---

## Pattern interrupters (1-2 slides obrigatórios)

Quebra de ritmo no meio do carrossel pra **resetar atenção**. Sem isso, audiência swipa sem absorver.

3 tipos:

1. **Pergunta provocativa** — "Mas espera. E se eu te dissesse o oposto?"
2. **Visual inesperado** — slide cheio só com 1 número gigante, ou só com um ícone enorme
3. **Linha contraintuitiva** — "A maioria fala X. Vou te mostrar por que é Y."

Posicionar em ~50% do carrossel (slide 4 ou 5 num carrossel de 8).

---

## Continuidade panorâmica

Elemento visual que **atravessa todos os slides**, criando sensação de "continuidade panorâmica" — o cérebro do espectador é compelido a swipar pra ver "como continua".

Implementado via **global layer** Slidev (`global-bottom.vue`). Exemplos:

- **Linha que cresce** — barra horizontal embaixo que vai de 14% (slide 1) a 100% (último)
- **Persona caminhando** — silhueta que se desloca da esquerda pra direita ao longo dos slides
- **Gráfico que se completa** — bar chart que ganha 1 barra por slide
- **Número crescente** — counter no canto que sobe a cada slide
- **Fundo gradiente migrando** — gradiente que rota tonalidade conforme avança

O global layer é **a feature que mais distingue um carrossel cinematográfico de um carrossel "bullet list embelezada"**.

---

## Visual baseline

- **Alto contraste** — fundo escuro + texto claro (ou inverso); evitar mid-tones
- **Tipografia grande** — hook ≥80pt, body ≥48pt em portrait 1080×1350
- **Fundo limpo** — 1 foco visual por slide; sem ruído de background
- **Cor de accent única** — 1 cor "POP" (teal, indigo, pink, amber) usada com parcimônia para guiar olho

---

## Hook templates

Use como ponto de partida na fase de outline:

1. **Stat surpreendente** — "98% dos founders erram nisso."
2. **Pergunta provocativa** — "Você está perdendo dinheiro e não sabe?"
3. **Contra-intuitivo** — "Pare de fazer marketing. Faça isso."
4. **Negação** — "Não é falta de leads. É outra coisa."
5. **Promessa** — "5 minutos pra dobrar suas conversões."
6. **Confissão** — "Errei isso por 2 anos. Aqui está o aprendizado."
7. **Comparação** — "Antes: 4h/dia. Depois: 20min."
8. **Curiosidade explícita** — "O que ninguém te contou sobre X."
9. **Urgência** — "Faça isso essa semana ou perde o ciclo."
10. **Lista numerada** — "3 erros que estão te custando R$ 50k/mês."

---

## CTA templates

Final slide sempre tem CTA + handle.

1. **Salva pra não esquecer** — "Salva esse post pra revisitar depois."
2. **Compartilha** — "Compartilha com quem precisa ouvir isso."
3. **Comenta** — "Comenta '🚀' se já passou por isso."
4. **DM** — "Manda DM 'AJUDA' que te mando a planilha."
5. **Follow** — "Segue @handle pra mais conteúdo assim."
6. **Link na bio** — "Link na bio pra continuar lendo."
7. **Swipe back** — "Releia esse carrossel antes de seguir o feed."
8. **Marca um amigo** — "Marca o amigo que precisa ler isso."

---

## Anti-patterns (não faça)

- ❌ Slide 1 sem hook claro ("Olá pessoal, hoje vamos falar sobre…")
- ❌ Bullet lists de 5+ items por slide
- ❌ Paredes de texto (>12 palavras)
- ❌ Caps em paralelo (todos slides usando mesmo layout vira monótono)
- ❌ Sem CTA no último slide
- ❌ Handle ausente
- ❌ Pular pattern interrupter (carrossel vira lista chata)
- ❌ Continuidade panorâmica genérica ("⌚ 1/8" no canto) sem motivação visual

---

## Sources

- Hootsuite — *How to make the most of Instagram carousels in 2025*
- Pano — *Best Practices for First-Slide Carousel Hooks*
- FlowShorts — *Instagram Carousel Posts: Engagement Guide (2026)*
- MarketingAgent — *Mastering Instagram Carousel Strategy in 2026: Algorithm Demands Swipes, Not Just Scrolls*
- PostNitro — *15 Strategies for Viral Instagram Carousels in 2025*

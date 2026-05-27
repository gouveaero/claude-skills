---
theme: default
title: '{{TITLE}}'
info: |
  {{INFO}}
aspectRatio: '4/5'
canvasWidth: 1080
mdc: true
highlighter: shiki
clickAnimation: up
drawings:
  persist: false
fonts:
  sans: 'Inter'
  mono: 'JetBrains Mono'
---

<HookSlide
  hook="{{HOOK}}"
  subhook="{{SUBHOOK}}"
  variant="gradient"
/>

<!-- Slide 1 — hook. Pare o scroll. <12 palavras, alto contraste. -->

---
layout: fact
---

# {{STAT}}

<div class="text-2xl opacity-80 mt-6">{{STAT_LABEL}}</div>

<!-- Slide 2 — eleva curiosidade com uma estatística ou pergunta. -->

---
layout: quote
---

<QuoteReveal
  text="{{QUOTE_OR_HOOK_LINE_2}}"
  :auto-play="true"
/>

<!-- Slide 3 — continua erguendo curiosidade. Outra abordagem (citação, contra-intuitivo). -->

---
layout: default
---

<StepCard
  :step="1"
  title="{{STEP_1_TITLE}}"
  body="{{STEP_1_BODY}}"
  icon='<mdi-lightbulb-on />'
/>

<!-- Slide 4 — primeiro passo / framework / educação concreta. -->

---
layout: default
---

<StepCard
  :step="2"
  title="{{STEP_2_TITLE}}"
  body="{{STEP_2_BODY}}"
  icon='<mdi-target />'
/>

<!-- Slide 5 — segundo passo. -->

---
layout: statement
---

# {{PATTERN_INTERRUPTER}}

<CalloutBadge variant="alert">spoiler</CalloutBadge>

<!-- Slide 6 — pattern interrupter. Quebra de ritmo. Pergunta provocativa OU contra-intuitivo. -->

---
layout: default
---

<StepCard
  :step="3"
  title="{{STEP_3_TITLE}}"
  body="{{STEP_3_BODY}}"
  icon='<mdi-rocket-launch />'
/>

<!-- Slide 7 — terceiro passo. -->

---
layout: end
---

<CTASlide
  cta="Salva esse post pra revisitar."
  handle="@gouveaero"
  :back-arrow="true"
/>

<!-- Slide 8 — CTA explícito + handle. Convida swipe back. -->

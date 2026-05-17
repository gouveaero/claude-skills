---
theme: seriph
background: https://cover.sli.dev
title: '{{TITLE}}'
info: |
  {{INFO}}
class: text-center
transition: view-transition
mdc: true
highlighter: shiki
drawings:
  persist: false
fonts:
  sans: 'Inter'
  mono: 'JetBrains Mono'
---

# {{TITLE}}

{{SUBTITLE}}

<div class="pt-12 opacity-70 text-sm">
  <carbon:arrow-right class="inline" /> Space para avançar
</div>

<!--
Notas do apresentador — contexto, gancho inicial, quanto tempo ficar neste slide.
-->

---
transition: fade-out
layout: center
---

# Exemplo — QuoteReveal

<QuoteReveal
  text="A melhor arquitetura é aquela que pode ser refeita."
  author="Martin Fowler"
  :auto-play="true"
/>

---

# Exemplo — lista progressiva

<v-clicks>

- Primeiro ponto aparece com o primeiro click
- Segundo ponto em seguida
- Terceiro ponto fecha a ideia

</v-clicks>

---

# Exemplo — StatNumber

<div class="flex gap-16 justify-center items-end mt-12">
  <StatNumber :value="99.9" suffix="%" label="uptime" :decimals="1" />
  <StatNumber :value="3.2" suffix="x" label="mais rápido" :decimals="1" />
  <StatNumber :value="420" prefix="+" label="deploys/dia" />
</div>

---
layout: center
---

# Obrigado

<div class="opacity-70 mt-8">
  @user · email@exemplo.com
</div>

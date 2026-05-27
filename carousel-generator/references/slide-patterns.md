# Slide Patterns — HTML Snippets

Each pattern is a `<section class="slide [modifier]">` block ready to paste. Replace ALL-CAPS placeholders. Variables like `--c-bg-deep` come from the brand injection.

---

## 1. hook-deep
Capa com fundo escuro. Marca + eyebrow + título grande com `<em>` em accent.

```html
<section class="slide deep active">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>SERIES_LABEL</span></div>
    <div class="foot"><span>SERIES_LABEL</span><span class="slide-pageno">i</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:40px;">
    <!-- optional mark/logo -->
    <div class="s-eyebrow">EYEBROW_TEXT</div>
    <h1 class="s-h1">HOOK_LINE_1<em>HOOK_ITALIC</em></h1>
    <p class="s-body" style="opacity:.8;font-size:26px;">HOOK_SUBTITLE — max 18 words</p>
  </div>
</section>
```

---

## 2. hook-light
Capa em fundo claro (argila/branco). Alternativa para marcas sem fundo escuro.

```html
<section class="slide active">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>SERIES_LABEL</span></div>
    <div class="foot"><span></span><span class="slide-pageno">i</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:40px;">
    <div class="s-eyebrow">EYEBROW_TEXT</div>
    <h1 class="s-h1">HOOK_LINE_1<br/><em>HOOK_ITALIC</em></h1>
    <p class="s-body">HOOK_SUBTITLE</p>
  </div>
</section>
```

---

## 3. qualification
"Para quem é este conteúdo." Curto, direto. Qualifica a audiência antes de entrar no conteúdo técnico.

```html
<section class="slide alt">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>ii</span></div>
    <div class="foot"><span></span><span class="slide-pageno">ii</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:32px;">
    <div class="s-eyebrow">Para quem</div>
    <h2 class="s-h3">QUALIFICATION_HEADING</h2>
    <p class="s-body">QUALIFICATION_BODY — 2–3 linhas, audiência + contexto</p>
  </div>
</section>
```

---

## 4. problem-1frase
Dor do cliente em uma frase de impacto. Sem solução ainda.

```html
<section class="slide">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>iii</span></div>
    <div class="foot"><span></span><span class="slide-pageno">iii</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:36px;">
    <div class="s-eyebrow">O problema</div>
    <h2 class="s-h2">PROBLEM_STATEMENT.<em>PROBLEM_EMPHASIS</em></h2>
    <p class="s-body">PROBLEM_CONTEXT — expande a dor, 2 frases</p>
  </div>
</section>
```

---

## 5. villain-loop
Nomeia o vilão (norma ilegal, prática errada, crença falsa) + loop aberto no final.

```html
<section class="slide">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>iv</span></div>
    <div class="foot"><span></span><span class="slide-pageno">iv</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:36px;">
    <div class="s-eyebrow">O vilão</div>
    <h2 class="s-h2">VILLAIN_NAME</h2>
    <p class="s-body">VILLAIN_CONTEXT. <em style="color:var(--c-accent);">LOOP_OPEN_PHRASE…</em></p>
    <!-- Loop aberto: termina com "…mas a lei nunca disse isso" ou equivalente -->
    <div class="s-mono" style="margin-top:8px;border-top:1px solid rgba(0,0,0,.12);padding-top:20px;">
      VILLAIN_CITATION — ex: "IN 247/2002 e 404/2004"
    </div>
  </div>
</section>
```

---

## 6. turn-authority
A virada: decisão de tribunal, lei, dado concreto. Cita a fonte em mono.

```html
<section class="slide deep">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>v</span></div>
    <div class="foot"><span></span><span class="slide-pageno">v</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:36px;">
    <div class="s-eyebrow">A virada</div>
    <h2 class="s-h2">TURN_STATEMENT<em>TURN_EMPHASIS</em></h2>
    <p class="s-body" style="opacity:.85;">TURN_EXPLANATION — o que isso significa na prática</p>
    <div class="s-mono" style="border-top:1px solid rgba(231,222,201,0.16);padding-top:20px;margin-top:8px;">
      AUTHORITY_CITATION — ex: "REsp 1221170/PR · STJ · Tema 779"
    </div>
  </div>
</section>
```

---

## 7. numeral-quote
Numeral romano gigante em accent + frase curta. Ideal para listar erros/princípios/critérios.

```html
<section class="slide alt">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>vi</span></div>
    <div class="foot"><span></span><span class="slide-pageno">vi</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;height:100%;gap:28px;">
    <div class="s-numeral">ROMAN_NUMERAL</div><!-- i, ii, iii, iv … -->
    <h2 class="s-h3">QUOTE_HEADING</h2>
    <p class="s-body">QUOTE_BODY — explicação em 2–3 linhas</p>
  </div>
</section>
```

---

## 8. examples-grid
3 ou 4 cards com exemplos concretos. Ótimo para listar itens depois de uma regra.

```html
<section class="slide">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>vii</span></div>
    <div class="foot"><span></span><span class="slide-pageno">vii</span></div>
  </div>
  <div style="display:flex;flex-direction:column;height:100%;gap:36px;justify-content:center;">
    <div>
      <div class="s-eyebrow">Exemplos práticos</div>
      <h3 class="s-h3" style="margin-top:16px;">EXAMPLES_HEADING</h3>
    </div>
    <div class="s-grid-2" style="gap:24px;">
      <div class="s-card">
        <div class="s-card-num">→</div>
        <div class="s-card-label">LABEL_1</div>
        <div class="s-card-text">EXAMPLE_1</div>
      </div>
      <div class="s-card">
        <div class="s-card-num">→</div>
        <div class="s-card-label">LABEL_2</div>
        <div class="s-card-text">EXAMPLE_2</div>
      </div>
      <div class="s-card">
        <div class="s-card-num">→</div>
        <div class="s-card-label">LABEL_3</div>
        <div class="s-card-text">EXAMPLE_3</div>
      </div>
      <div class="s-card">
        <div class="s-card-num">→</div>
        <div class="s-card-label">LABEL_4</div>
        <div class="s-card-text">EXAMPLE_4</div>
      </div>
    </div>
  </div>
</section>
```

For 3 items use `s-grid-3` and remove 4th card. For 2 items use a single column with `flex-direction:column`.

---

## 9. voice-pair
Do/don't ou say this/not that. Duas colunas lado a lado.

```html
<section class="slide">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>viii</span></div>
    <div class="foot"><span></span><span class="slide-pageno">viii</span></div>
  </div>
  <div style="display:flex;flex-direction:column;height:100%;gap:36px;justify-content:center;">
    <div>
      <div class="s-eyebrow">PAIR_EYEBROW</div>
      <h3 class="s-h3" style="margin-top:16px;">PAIR_HEADING</h3>
    </div>
    <div class="s-grid-2">
      <div class="s-voice-col">
        <h4>POSITIVE_LABEL</h4><!-- ex: "Dizer assim" / "✓ correto" -->
        <div class="yes">POSITIVE_EXAMPLE_1</div>
        <div class="yes" style="margin-top:20px;">POSITIVE_EXAMPLE_2</div>
      </div>
      <div class="s-voice-col">
        <h4>NEGATIVE_LABEL</h4><!-- ex: "Nunca assim" / "✕ evitar" -->
        <div class="no">NEGATIVE_EXAMPLE_1</div>
        <div class="no" style="margin-top:20px;">NEGATIVE_EXAMPLE_2</div>
      </div>
    </div>
  </div>
</section>
```

---

## 10. cta-double
Slide final. Dois CTAs: salvar + comentar palavra-chave.

```html
<section class="slide deep">
  <div class="slide-chrome">
    <div class="head"><span>BRAND_HANDLE</span><span>LAST_PAGENO</span></div>
    <div class="foot"><span>SERIES_LABEL</span><span class="slide-pageno">LAST_PAGENO</span></div>
  </div>
  <div style="display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;gap:40px;text-align:center;">
    <!-- optional brand mark SVG here -->
    <div class="s-eyebrow" style="justify-content:center;">EYEBROW_CTA</div>
    <div class="s-cta-word">CTA_KEYWORD</div><!-- ex: "TEMA779" -->
    <div style="display:flex;flex-direction:column;gap:16px;">
      <p class="s-body" style="opacity:.85;text-align:center;">
        📌 Salva esse carrossel — referência técnica.<br/>
        💬 Comenta <strong>CTA_KEYWORD</strong> e recebemos o guia completo por DM.
      </p>
    </div>
    <div class="s-footer-bar">
      <span>BRAND_HANDLE</span>
      <span>BRAND_WEBSITE</span>
    </div>
  </div>
</section>
```

---

## Tips

- **Slide length**: aim for 5–8 words per line in titles. Break with `<br/>` if needed.
- **Font size check**: in `s-h1` at 120px, a 1080px slide fits ~9–10 characters per line.
- **Em tags**: use `<em>` for the word/phrase that carries the most emotional weight — never more than 1 `<em>` cluster per heading.
- **Pageno**: use roman numerals in lowercase (i, ii, iii, iv, v…) in the `slide-pageno` span. Match the position of the slide in the deck.
- **Deep slides**: class `deep` on the `<section>` → dark background, all variables auto-switch. No extra inline color needed.

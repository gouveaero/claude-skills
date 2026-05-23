# Code features — Reference

Slidev tem 6 sistemas para mostrar código: **Shiki Magic Move** (transição animada granular), **line highlighting** (focar linhas em estágios), **Twoslash** (tipos TS inline), **Monaco editor** (bloco editável ao vivo), **Monaco runner** (executa JS), **import snippets** (carregar código do disco). Use o sistema correto para o propósito — não use Magic Move pra slide estático, não use Monaco pra mostrar estado fixo.

---

## Decision tree

| Slide é... | Use |
|---|---|
| Código estático, sem reveal | bloco ` ```ts ` simples |
| Walkthrough passo-a-passo do MESMO código (mesma versão, foco em linhas diferentes) | Line highlighting `{2-3\|5\|all}` ou componente custom `<CodeReveal>` |
| **Refactoring story** (mesmo bloco evoluindo: V1 → V2 → V3) | **Shiki Magic Move** ⭐ |
| Tipos TypeScript inline + erros de compilação visíveis | Twoslash ` ```ts twoslash ` |
| Demo ao vivo (audiência vê você editar e o output mudar) | Monaco editor `{monaco}` + opcional `{monaco-run}` |
| Código real do projeto (não duplicar nos slides) | Import snippet `<<< @/snippets/file.ts {2-5}` |

---

## Shiki Magic Move ⭐

**A feature mais subutilizada.** Transição animada granular entre versões de código — caractere a caractere, palavra a palavra, linha a linha. Cada estado vira um click do slide.

Resultado visual: o audiência **acompanha a transformação**, em vez de comparar dois snapshots estáticos lado a lado. Para histórias de refactoring, antes/depois de optimization, evolução de API, é Keynote-grade.

### Sintaxe

````md
```ts magic-move
// V1 — versão original
function process(data) {
  const result = []
  for (let i = 0; i < data.length; i++) {
    result.push(transform(data[i]))
  }
  return result
}
```

```ts
// V2 — refator para map
function process(data) {
  return data.map(item => transform(item))
}
```

```ts
// V3 — currying + nome melhor
const transformAll = data => data.map(transform)
```
````

Cada bloco subsequente vira um click. O Slidev anima a transição entre as versões: tokens iguais permanecem, novos aparecem, removidos somem com animação suave.

### Dica

Para chamar atenção a uma linha específica enquanto a transição rola, combine com line highlighting:

````md
```ts magic-move {2-4}
// V1
function process(data) {
  const result = []
  for (let i = 0; i < data.length; i++) {
    result.push(transform(data[i]))
  }
  return result
}
```
````

---

## Line highlighting (staged)

Use para focar linhas diferentes do **mesmo bloco** ao longo de vários clicks. Diferente do Magic Move, não é mudança de versão — é mudança de foco.

```` ```ts {2-3|5|all} ````

3 estágios: primeiro destaca linhas 2-3, depois 5, por fim mostra tudo. Cada `|` é um click.

Exemplo completo:

````md
```ts {1|3-5|7|all}
function handler(req) {
  // ← click 1: highlight linha 1
  const token = req.headers.get('auth')
  if (!token) return unauthorized()  
  // ← click 2: highlight linhas 3-5
  return json({ user: verify(token) })
  // ← click 3: highlight linha 7 (não existe, mas highlight pode ser hipotético)
}
// ← click 4: tudo destacado
```
````

---

## Twoslash — tipos TS inline

Ativa o compilador TS e mostra tipos inferidos ao hover OU exibe erros como pop-ups.

````md
```ts twoslash
const greet = (name: string) => `Hello, ${name}`

const result = greet(42)
//             ^?
//             ⚠ Argument of type 'number' is not assignable to parameter of type 'string'
```
````

O `^?` cria um hover persistente mostrando o tipo. Erros aparecem inline com sublinhado vermelho + tooltip.

Indispensável em palestras técnicas de TypeScript ou treinamentos de tipos.

---

## Monaco editor — bloco editável ao vivo

Transforma o bloco em um Monaco (editor do VS Code) — audiência vê você editar em tempo real.

````md
```ts {monaco}
function double(n: number) {
  return n * 2
}
```
````

Suporta IntelliSense completo (autocomplete, tipos, jump-to-definition).

---

## Monaco runner — executa JS

Executa o código e mostra output abaixo do editor.

````md
```js {monaco-run}
const fib = n => n < 2 ? n : fib(n-1) + fib(n-2)
console.log(fib(10))
```
````

O output aparece live; editar o código re-executa.

Para apresentações onde a audiência precisa ver "o que esse código faz?" sem context-switch pro terminal.

---

## Import snippets — carregar arquivo do disco

Em vez de duplicar código real do projeto nos slides, importe direto:

````md
<<< @/snippets/auth-handler.ts
````

Com linhas específicas:

````md
<<< @/snippets/auth-handler.ts#L10-L20
````

Com sintaxe específica:

````md
<<< @/snippets/component.vue {2-5|7|all}
````

O snippet vive em `snippets/` na raiz do projeto Slidev. Vantagem: o arquivo é o **mesmo** que o projeto real importa — slides nunca ficam desatualizados em relação ao código.

---

## Configuração Shiki — escolher tema

No frontmatter global:

```md
---
highlighter: shiki
shikiOptions:
  themes:
    dark: vitesse-dark
    light: vitesse-light
---
```

Temas populares: `vitesse-dark`, `vitesse-light`, `nord`, `dracula`, `github-dark`, `min-light`. Lista completa: <https://shiki.style/themes>.

---

## Quando NÃO usar

| Não use | Use em vez |
|---|---|
| Magic Move pra slide com 1 código só | Bloco normal ` ```ts ` |
| Monaco editor se a audiência só vai ler (sem você editar) | Bloco estático com line highlighting |
| Twoslash em código não-TS | Bloco normal |
| Import snippet pra código <5 linhas | Inline (poluído manter `snippets/`) |

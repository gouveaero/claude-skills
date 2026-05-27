# Icon Resources — Banco Local + Bibliotecas Online

Animações desenhadas à mão em SVG raramente ficam tão boas quanto **PNGs/SVGs já produzidos** por bibliotecas. Quando um overlay precisa de um elemento reconhecível (busto, edifício, pessoa, símbolo institucional), USE ESTAS FONTES antes de tentar desenhar do zero.

## 1. Banco local de PNGs (prioritário)

**Caminho:** `/Users/gabriel/Documents/PNGS PARA EDICAO/`

**Como usar:**
1. Leia `INDEX.md` (catálogo scanável de todos os ícones com `id`, descrição, tags, mood, casos de uso).
2. Para programmatic search use `manifest.json`.
3. Cada item: `**id** — descrição. \`tags\` · *mood* · use: casos de uso · qualidade`
4. 8 categorias: `01_pessoas`, `02_celebridades`, `03_dinheiro`, `04_veiculos`, `05_animais`, `06_objetos`, `07_reacoes_memes`, `08_misc`
5. Todos os PNGs têm alpha channel.

**Workflow no Remotion:**
```bash
# Copiar PNG escolhido pro projeto
cp "/Users/gabriel/Documents/PNGS PARA EDICAO/<categoria>/<id>.png" \
   "<remotion_dir>/public/icons/<id>.png"
```

```tsx
// No componente Remotion
import { Img, staticFile } from "remotion";

<Img src={staticFile("icons/<id>.png")} style={{ ... }} />
```

**Regras de seleção:**
- Cite o `id` exato do INDEX (não invente nomes).
- Prefira `quality_tier: high`.
- Não polua cenas — só insira se o ícone realmente ilustra o conceito.
- Não repita o mesmo ícone em cenas próximas (busque alternativa).

## 2. Bibliotecas de SVG online (quando o banco não tem)

Se o banco local NÃO tem um ícone adequado, busque em bibliotecas públicas open-source. Tem `WebFetch` e `WebSearch` disponíveis.

| Biblioteca | URL | Licença | Forte em |
|---|---|---|---|
| **Heroicons** | https://heroicons.com | MIT | UI geral, business, edifícios |
| **Lucide** | https://lucide.dev | ISC | UI geral, ícones simples |
| **Tabler Icons** | https://tabler-icons.io | MIT | Variedade ampla, 4000+ ícones |
| **SVGRepo** | https://www.svgrepo.com | varia (filtre por CC0/MIT) | Tudo (50k+ SVGs) |
| **Simple Icons** | https://simpleicons.org | CC0 | Logos de marca |
| **Material Icons** | https://fonts.google.com/icons | Apache 2.0 | Google design system |
| **Game Icons** | https://game-icons.net | CC BY 3.0 | Conceitos abstratos (espada, escudo, balança, etc) |
| **Wikimedia Commons** | https://commons.wikimedia.org | varia (filtre por PD/CC) | Imagens históricas/clássicas |

**Workflow:**
```python
# Via WebFetch — pegar o path SVG inline
WebFetch(url="https://heroicons.com/24/outline/scale", 
        prompt="Extract the raw SVG path d= value for the scale icon")
```

Ou diretamente baixar:
```bash
curl -o "<remotion_dir>/public/icons/scale.svg" \
  "https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/outline/scale.svg"
```

**Quando preferir SVG online sobre PNG do banco:**
- Conceito abstrato (engrenagem, lupa, escudo) — SVG vetorial fica perfeito em qualquer tamanho
- Quer cor da marca (SVG aceita `stroke={COPPER}` fácil; PNG é fixo)
- Banco local não tem o conceito

**Quando preferir PNG do banco:**
- Pessoa, celebridade, objeto específico, cena fotografada/3D
- Imagem com texturas complexas
- Estilo "fotografia"/render 3D

## 3. Quando criar SVG do zero (last resort)

Só desenhe SVG à mão se:
- O conceito é MUITO específico (latrina romana antiga, busto Vespasiano com louros)
- Não tem opção boa nem no banco nem nas bibliotecas
- Tem certeza que vai conseguir um resultado RECONHECÍVEL

**Princípio:** Se uma animação não é IMEDIATAMENTE reconhecível como o que deveria ser (sem precisar do label de texto), está ruim. Volte e use uma fonte real.

**Tip pra SVG complexo:** Use heroicons como base + adicione detalhes. Ex: `building-library` icon + capitel romano em cima = templo romano.

## 4. Reporting

Ao final da edição, reporte:
- Lista de cenas modificadas (timestamp + id do ícone + razão)
- Cenas onde faltou ícone (descreva o ideal — pode virar issue pra expandir o banco)
- SVGs baixados de bibliotecas externas (URL + licença)

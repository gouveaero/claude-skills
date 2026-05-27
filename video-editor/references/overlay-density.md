# Overlay Density — Minimum Requirements

**Feedback TriboTax 2026-05-12:** "poucos overlays no atual" e "mais fullscreen com animação cobrindo tela inteira nos momentos-chave."

## Regras de densidade

| Duração | Mínimo de `rich_overlays` | SFX cadence |
|---|---|---|
| Reel 3min (9:16) | **20** | 1 a cada 10-15s |
| Reel 60s | **10** | 1 a cada 6-10s |
| Reel 30s | **6** | 1 a cada 5-8s |

**Média:** 1 overlay novo a cada 8-10s de vídeo. Um reel "vazio" (< 15 overlays em 3min) sempre parece amador.

## Momentos que EXIGEM fullscreen overlay

| Momento | Tipo recomendado |
|---|---|
| Hook (0–5s) | `statue_money`, `icon_punch`, ou fullscreen dramático com PNG |
| Revelação de número importante | `counter_number` fullscreen |
| Dato/tese jurídica citada | `code_document` ou `tese_reveal` |
| Virada narrativa / pattern interrupt | `cinematic_title` fullscreen + CINEMATICA SFX |
| Clímax emocional (perda do direito, injustiça) | `lady_justice`, `split_comparison` fullscreen |
| CTA final | `comment_bubble_cta` ou `tribotax_logo_finale` |

## PNG sob demanda — pedir ao Gabriel

Se (1) banco local e (2) Wikimedia/bibliotecas não cobrem o visual desejado, **PARAR e pedir ao Gabriel um PNG específico.** Formule o pedido assim:

> "Para o overlay X precisamos de uma imagem de [descrição detalhada — estilo, composição, fundo preferido escuro ou branco, elementos principais]. Você consegue gerar?"

Gabriel usa ferramentas de geração de imagem (Midjourney, Flux, etc.). Os PNGs gerados devem:
- Ir para `/Users/gabriel/Documents/PNGS PARA EDICAO/<categoria>/`
- Ser copiados para `<remotion>/public/icons/`
- Ser documentados no `INDEX.md`

## Icon library — REGRA OBRIGATÓRIA (não negociável)

**Antes de QUALQUER `rich_overlay` que envolva figura/ícone/objeto reconhecível, siga esta ordem rígida:**

1. **PNG local primeiro** — `/Users/gabriel/Documents/PNGS PARA EDICAO/` (232 ícones, 9 categorias). Ler `INDEX.md` integralmente. Buscar por keywords semânticas (`balanca`, `justi`, `estatua`, `busto`, `dinheiro`, `doc`, `mao`). Copiar pra `<remotion>/public/icons/` e usar via `<Img src={staticFile('icons/<id>.png')} />`.

2. **Wikimedia Commons + bibliotecas SVG** — Brasões/bandeiras/símbolos oficiais via Wikimedia (PD/CC). Ícones genéricos via heroicons/lucide/tabler/svgrepo. Use `WebFetch`.

3. **Pedir ao Gabriel PNG novo** — Se (1) e (2) não cobrem, PARAR e solicitar imagem específica. Não tentar desenhar.

4. **SVG na mão = ÚLTIMO recurso** — Só pra formas geométricas puras (linhas, retângulos, gradientes, frames). **PROIBIDO** pra: figura humana, busto, balança, brasão oficial, animal, objeto reconhecível.

**Por que essa regra existe (Gabriel, TriboTax 2026-05-12):** Geramos `scale_of_justice` em SVG cru → balança virou palitos + pratos retangulares. Geramos `stf_stamp` em SVG → brasão virou selo amador. Feedback explícito: "a balança ficou bem feia", "STF não ficou legal". O banco PNG tinha `blindfolded-statue-woman-spike-crown` (Lady Justice) e o brasão STF estava no Wikimedia — ambos pulados. **Erro repetido = falha grave.**

## Padrão de extensão com `icon?` prop

Quando um componente existente precisa aceitar PNGs diferentes por projeto (ex: `StatueMoney`, `StatueDoubt`, `LadyJustice`), adicionar prop opcional:

```tsx
export const MeuComponente: React.FC<BaseProps & { icon?: string }> = ({ icon }) => {
  const imgSrc = staticFile(icon ? `icons/${icon}` : "icons/default.png");
  return <Img src={imgSrc} ... />;
};
// No dispatcher:
if (k === "meu_componente") return <MeuComponente {...base} icon={overlay.icon} />;
// No edit_plan.json:
{ "kind": "meu_componente", "icon": "novo-png.png" }
```

Isso permite trocar o PNG por projeto sem alterar o componente.

Detalhes (workflow, licenças): [icon-resources.md](./icon-resources.md).

# Inspiração — Prompts e Padrões Remotion

Digest curado de 5 fontes de referência para criar componentes Remotion personalizados.

## Princípios extraídos das fontes

### Da remotion.dev/templates
- **TalkingHead**: sincroniza zoom/pan com transcript word-level; usa `useCurrentFrame` + índice de palavras para animar câmera programaticamente
- **Subtitles template**: usa `getSubtitles()` com timestamp preciso, animação de entrada por palavra (não por frase)
- **SaaS Explainer**: combina screen recording + animated callouts + lower thirds — padrão para vídeos de produto/tutorial

### Da sabrina.dev — 5 prompts criativos
1. **"Kinetic Word Reveal"**: cada palavra entra com `spring()` escalonado, saindo antes da próxima aparecer — efeito de máquina de escrever acelerada
2. **"Data Story"**: gráfico animado construindo linha por linha, sincronizado com narração
3. **"Split Screen Comparison"**: dois clips lado a lado com transição de wipe progressivo
4. **"Countdown Timer"**: círculo SVG animado + número central via `interpolate`
5. **"Testimonial Card"**: avatar + texto + rating, todos animados com spring sequencial

### De deepakness.com — Prompts crus para componentes
- Ao pedir um componente novo: especifique `fps`, `durationInFrames`, `width`, `height` no prompt
- Use `AbsoluteFill` como container raiz sempre
- `spring({ fps, frame, config: { damping: 200, stiffness: 80 } })` para animações suaves
- `interpolate(value, [0,1], [from, to], { extrapolateRight: "clamp" })` para controle preciso

### De manalkaff/remotion-prompts (GitHub)
- **Pattern Interrupt**: corte abrupto + glitch de 3 frames + zoom rápido 1.0→1.3→1.0
- **Text Burst**: texto explode do centro, escala 0→1.5→1.0 em 15 frames
- **Loop seamless**: composição onde último frame = primeiro frame (para Stories em loop)
- **Overlay animado**: componente que aceita `src` de vídeo + transparent background → renderizado como .mov alpha

### De remotion.dev/prompts — Prompts oficiais
- Sempre inclua no prompt: propósito do vídeo, aspecto, duração em segundos, estilo visual
- Para timing preciso: "aos Xs do vídeo, mostre X animação por Ys"
- Mencione explicitamente: "use `<AbsoluteFill>`, `useCurrentFrame`, `useVideoConfig`"
- Para reutilização: "aceite props `startFrame` e `endFrame` para controlar quando o componente aparece e desaparece"

## Templates reutilizáveis (snippets disponíveis)

| Snippet | Uso ideal | Props principais |
|---|---|---|
| `CountUp` | Revelar número com impacto | `target`, `prefix`, `suffix`, `accentColor` |
| `KenBurns` | B-roll estático com movimento | `src`, `zoomFrom`, `zoomTo`, `panX`, `panY` |
| `GlitchText` | Pattern interrupt textual | `text`, `intensity`, `durationFrames` |
| `CalloutArrow` | Apontar para elemento na tela | `label`, `targetX`, `targetY`, `direction` |
| `LowerThird` | Identificar pessoa / empresa | `name`, `detail`, `accentColor` |
| `PiPBroll` | B-roll no canto enquanto fala | `src`, `corner`, `sizePercent` |

## Componentes custom — como pedir ao Claude

Para pedir um componente novo durante o `plan_edit`, declare em `overlays_v2`:

```json
{
  "id": "meu_componente",
  "component": "custom/MeuComponente",
  "start_frame": 60,
  "end_frame": 120,
  "filename": "overlay_custom_01",
  "props": { "prop1": "valor1" },
  "custom_component_description": "Componente que mostra um gráfico de pizza animado com fatias coloridas. Cada fatia entra com spring sequencial. Cores: verde #2D6A4F, dourado #C8A96E. Props: data=[{label, value, color}]"
}
```

O `build_remotion.py` detecta `component` começando com `"custom/"` e pede ao Claude Code para gerar o arquivo TSX antes de montar o projeto.

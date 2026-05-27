# 3D, Lottie & Rive

Three rendering surfaces for richer visuals beyond SVG/PNG: 3D models, vector animations from After Effects (Lottie), and interactive vector animations (Rive).

## When to use which

| Use case | Pick |
|---|---|
| Aircraft / car / product rotation from `.glb` | `ThreeReveal` (`@remotion/three`) |
| Animated logo / icon reveal designed in After Effects | `LottieScene` (`@remotion/lottie`) |
| State-machine vector animation (loaders, character rigs) | `RiveScene` (`@remotion/rive`) |
| Static SVG with stroke-draw animation | `ShapeMorph` (`@remotion/shapes` + `@remotion/paths`) |

## 1. `<ThreeReveal>` — 3D models

Render `.glb` or `.gltf` models via React Three Fiber, with the model rotating into view.

### Plan declaration

```json
{
  "kind": "three_reveal",
  "start": 12,
  "end": 18,
  "glb": "models/su-35.glb",
  "rotation_speed": 0.6,
  "auto_rotate": true,
  "camera_z": 5,
  "scale": 1.2,
  "background_color": "#0A1A0F",
  "env_preset": "sunset"
}
```

### Setup

```bash
# build_remotion.py auto-installs when plan contains "three_reveal":
#   @remotion/three @react-three/fiber @react-three/drei three @types/three
```

Place `.glb` files in `<remotion>/public/models/`. Optimize models with [gltfpack](https://github.com/zeux/meshoptimizer/tree/master/gltf) before commit — reduces bundle from 50MB to ~5MB.

### Performance

Three.js renders inside `<ThreeCanvas>` (which is a Remotion-aware `<Canvas>`). Each frame is rendered server-side via WebGL in Puppeteer/Chrome. Heavy scenes (PBR, normal maps, many polygons) can slow renders to 1fps. Mitigations:

- Pre-bake lighting; avoid real-time shadows.
- Use `<Environment preset="sunset" />` instead of an HDRI.
- Limit polygon count to <100k.
- For multi-camera reveals, use `useCurrentFrame` to interpolate camera position instead of physics simulation.

### Where to find models

- [Sketchfab](https://sketchfab.com/) (free + paid, .glb downloadable)
- [Khronos glTF Sample Models](https://github.com/KhronosGroup/glTF-Sample-Models) (CC0 reference)
- [Poly Haven](https://polyhaven.com/) (CC0 PBR-ready)
- For aviation specifically: Quixel Megascans (subscription) or community .glb hubs

## 2. `<LottieScene>` — After Effects animations

Render `.json` (and `.lottie` bundles) directly. Animation timeline syncs to Remotion's frame automatically.

### Plan declaration

```json
{
  "kind": "lottie",
  "start": 0,
  "end": 3,
  "lottie_src": "animations/logo-reveal.json",
  "position": "center",
  "scale": 1.0,
  "loop": false
}
```

### Setup

```bash
# Auto-installed: @remotion/lottie
```

Place `.json` files in `<remotion>/public/animations/`.

### Sourcing Lottie files

- [LottieFiles](https://lottiefiles.com/) (community library — many free)
- Export from After Effects via [Bodymovin plugin](https://aescripts.com/bodymovin/)
- Convert from Figma via [Figma to Lottie plugin](https://www.figma.com/community/plugin/856171493281373423)

### Performance

Lottie is generally fast — vector ops are GPU-friendly. Heavy effects (gaussian blur, expressions, large masks) can stall. Test with `--scale=2` to verify quality at high res.

### When NOT to use Lottie

- **Animations that need to react to data at render time** — Lottie animations are pre-baked. Use a Remotion React component instead.
- **Animations longer than ~5 seconds** — JSON file size balloons. Consider video file instead.

## 3. `<RiveScene>` — interactive vector animations

Rive is more efficient than Lottie for interactive states. State machines mean one `.riv` can render different animations depending on props.

### Plan declaration

```json
{
  "kind": "rive",
  "start": 8,
  "end": 12,
  "rive_src": "rive/loader.riv",
  "artboard": "Main",
  "state_machine": "State Machine 1",
  "position": "center",
  "size": 600
}
```

### Setup

```bash
# Auto-installed: @remotion/rive
```

Place `.riv` files in `<remotion>/public/rive/`.

### Sourcing Rive files

- [Rive Community](https://rive.app/community) (free + paid)
- Author your own via [Rive Editor](https://editor.rive.app/) (free for individuals)

## 4. `<ShapeMorph>` — geometric morphs

Pure-SVG path interpolation between geometric primitives. No external assets.

### Plan declaration

```json
{
  "kind": "shape_morph",
  "start": 4,
  "end": 7,
  "from_shape": "circle",
  "to_shape": "star",
  "size": 320,
  "stroke_color": "#B87333",
  "fill_color": "transparent",
  "stroke_width": 8,
  "position": "center",
  "stroke_draw_seconds": 1.0
}
```

Shapes available: `circle`, `triangle`, `rect`, `star`, `polygon`.

### Setup

```bash
# Auto-installed: @remotion/shapes @remotion/paths
```

### Use cases

- Animated dividers between scenes (square → diamond)
- Brand icon reveal (circle → custom polygon)
- Abstract intro/outro stinger

## Combining surfaces

Multiple surfaces can render at the same time — they live in different overlay tracks (V2, V3, V4...) handled by the greedy track-assignment in `capcut_draft_builder.py`. Example for Vhoe:

```
V1: cockpit footage (cuts)
V2: ThreeReveal of aircraft (overlay 0-6s)
V3: ShapeMorph crosshair (overlay 2-4s)
V4: LottieScene engine schematic (overlay 8-12s)
A1: voice narration
A2: SFX (RISER, BOOM, AMBIENTE)
```

## Anti-patterns

- **`<ThreeReveal>` with HDRI** — slow renders. Use `<Environment preset>` presets instead.
- **Loading `.glb` from external URL** — fails offline + slow first frame. Always use `staticFile()`.
- **Loading Lottie JSON inside the React component without `delayRender`** — first frame renders before JSON parses. Use the `delayRender` pattern (already in `LottieScene.tsx`).
- **Rive state machines with inputs that change at runtime** — Rive expects user input. For Remotion, pre-set the state machine to the desired animation in the Rive Editor.

## See also

- [remotion-feature-catalog.md](./remotion-feature-catalog.md) — packages reference
- [data-driven-videos.md](./data-driven-videos.md) — generate 50 Vhoe reels each with different `.glb`

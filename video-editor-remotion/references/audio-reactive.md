# Audio-Reactive Visuals

Drive overlay animations from the audio waveform itself — narration TTS, music, engine sounds. Powered by `@remotion/media-utils`.

## When to use

- **Vhoe**: engine-frequency bars during cockpit shots
- **Telesapiens / TriboTax**: narration-driven waveform for podcast-style reels
- **Music videos**: full-spectrum visualization

## Setup

Place audio file in `<remotion>/public/`. Reference it via `staticFile()` (or pass relative path to the component prop — `AudioWaveform.tsx` calls `staticFile()` internally).

## Edit plan declaration

```json
{
  "rich_overlays": [
    {
      "kind": "audio_waveform",
      "start": 5,
      "end": 28,
      "audio_src": "voice/narration.mp3",
      "bars": 48,
      "color": "#B87333",
      "position": "bottom",
      "height_px": 200,
      "smoothing": 0.7,
      "frequency_range": "voice"
    }
  ]
}
```

## Props reference

| Prop | Type | Default | Notes |
|---|---|---|---|
| `audio_src` | string | required | Path relative to `public/` |
| `bars` | number | 48 | Bar count |
| `color` | hex string | `#B87333` | Bar color (gets glow shadow) |
| `position` | `top \| bottom \| center` | `bottom` | Vertical placement |
| `height_px` | number | 200 | Max bar height |
| `smoothing` | 0..1 | 0.7 | Temporal smoothing (higher = less twitchy) |
| `frequency_range` | `full \| voice \| bass` | `full` | Slice of FFT bins to show |

## Internals (for extending)

The component uses:

```tsx
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

const audioData = useAudioData(staticFile(audio_src));
const samples = visualizeAudio({
  fps, frame, audioData,
  numberOfSamples: bars * 2,
  smoothing,
});
```

`useAudioData` returns null on first render (async load) — wrap in `if (!audioData) return null;` to skip the frame cleanly.

`visualizeAudio` returns an array of amplitudes (0..1) per FFT bin. Higher `numberOfSamples` → finer detail but more CPU. `smoothing` reduces frame-to-frame jitter.

## Patterns

### Pulse animation (single element)
Use the average amplitude across bars to drive a single pulse scale:

```tsx
const avg = samples.reduce((a, b) => a + b, 0) / samples.length;
const scale = 1 + avg * 0.4;
return <div style={{ transform: `scale(${scale})` }}>{...}</div>;
```

### Radial waveform
Map bar amplitudes to polar coordinates:

```tsx
{samples.map((a, i) => {
  const angle = (i / samples.length) * Math.PI * 2;
  const radius = 200 + a * 100;
  const x = 540 + Math.cos(angle) * radius;
  const y = 960 + Math.sin(angle) * radius;
  return <circle cx={x} cy={y} r={4} fill={color} />;
})}
```

### Beat-driven SFX trigger
For now SFX timing is declared in `edit_plan.json` and resolved in `capcut_draft_builder.py`. Beat-detection from audio (auto-place SFX on kicks) is out of scope — Whisper word timings are the existing rhythmic source.

## Anti-patterns

- **`<Audio src={...}>` inside the AudioWaveform component** — the component only visualizes; play the audio in a parallel `<Audio>` track at the Reel composition level so timing matches.
- **`numberOfSamples` not double `bars`** — wasted CPU. Use `bars * 2`.
- **No `smoothing`** (smoothing=0) — bars jitter wildly per frame. Default 0.7 is good for voice; 0.5 for music.

## See also

- [remotion-feature-catalog.md](./remotion-feature-catalog.md) — `@remotion/media-utils` reference
- [`templates/components/AudioWaveform.tsx`](../templates/components/AudioWaveform.tsx) — full component

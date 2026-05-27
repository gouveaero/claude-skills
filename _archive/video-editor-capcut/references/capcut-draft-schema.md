# CapCut Draft Schema Reference

Source: reverse-engineered via pyJianYingDraft v0.2.6 + CapCut 8.5.0 macOS (com.lemon.lvoverseas).

## Timing

All time values are **microseconds** (int).

```python
SEC = 1_000_000   # 1 second
# edit_plan.json uses seconds (float) → multiply by SEC to convert
target_start_us = int(timeline_start_seconds * SEC)
duration_us     = int((source_out - source_in) * SEC)
```

## Draft folder structure (macOS)

```
~/Library/Containers/com.lemon.lvoverseas/Data/Library/Application Support/
  CapCut/User Data/Projects/com.lveditor.draft/
    <draft-name>/
      draft_content.json     ← main project file
      draft_meta_info.json   ← name, thumbnail, timestamps
```

If that path doesn't exist yet (CapCut never opened), the builder creates it.

## Top-level draft_content.json structure

Key fields set by the builder:

```json
{
  "canvas_config": { "width": 1080, "height": 1920, "ratio": "original" },
  "fps": 30.0,
  "duration": <total_duration_us>,
  "materials": { ... },
  "tracks": [ ... ],
  "config": { "maintrack_adsorb": true, ... },
  "platform": { "app_id": 3704, "app_source": "lv", "app_version": "5.9.0", "os": "windows" }
}
```

Note: `platform.app_version` is fixed at `"5.9.0"` in the pyJianYingDraft template — this is intentional and does NOT affect playback in CapCut 8+.

## Video Material

```json
{
  "id": "<uuid>",
  "material_id": "<uuid>",
  "path": "/absolute/path/to/clip.mp4",
  "duration": <clip_total_duration_us>,
  "width": 1080,
  "height": 1920,
  "type": "video",
  "material_name": "clip_name.mp4",
  "local_material_id": "",
  "crop_ratio": "free",
  "crop_scale": 1.0,
  "category_name": "local",
  "check_flag": 63487
}
```

## Video Track Segment

Each cut from `edit_plan.json` `v1_main[]`:

```json
{
  "id": "<uuid>",
  "material_id": "<video_material_id>",
  "source_timerange": { "start": <source_in_us>, "duration": <cut_duration_us> },
  "target_timerange": { "start": <timeline_pos_us>, "duration": <cut_duration_us> },
  "speed": 1.0,
  "volume": 1.0,
  "clip": { "alpha": 1.0, "flip": {"horizontal": false, "vertical": false},
            "rotation": 0.0, "scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": 0.0} },
  "uniform_scale": { "on": true, "value": 1.0 },
  "extra_material_refs": ["<speed_object_id>"],
  "render_index": 0
}
```

## Text Material (captions)

Each word-group from `subtitle_track[]`:

```json
{
  "id": "<uuid>",
  "type": "text",
  "content": "{\"styles\":[...], \"text\":\"PALAVRA\"}",
  ...
}
```

TextStyle for subtitles:
- `size = 8.0` (relative to canvas)
- `bold = True`
- `color = (1.0, 1.0, 1.0)` (white)
- `align = 1` (center)
- Position: `transform_y = -0.8` (bottom third, as CapCut imported subtitles use this)

## Track structure

```json
{
  "id": "<uuid>",
  "type": "video",   // or "text"
  "name": "video",
  "attribute": 0,    // 0 = not muted
  "flag": 0,
  "segments": [ ... ],
  "is_default_name": true,
  "render_index": 0  // video=0, text=15000
}
```

## Transition mapping (edit_plan → TransitionType)

| edit_plan.json | pyJianYingDraft TransitionType | Notes |
|---|---|---|
| `"fade"` | `叠化` | Standard dissolve |
| `"slide_up"` | `向上` | Slide up |
| `"wipe"` | `渐变擦除` | Gradient wipe |
| `"none"` | (no transition) | Hard cut |

Transitions attach to the EARLIER segment via `segment.add_transition(type, duration=frames*33333)`.

## edit_plan.json → CapCut mapping summary

| edit_plan field | CapCut element |
|---|---|
| `v1_main[].clip` + `source_in/out` | VideoMaterial + VideoSegment source_timerange |
| `v1_main[].timeline_start` | VideoSegment target_timerange.start |
| `subtitle_track[]` | TextSegment on text track (bottom third) |
| `overlays_v2[]` | TextSegment (large, centered, no border) |
| `transitions[].type` | VideoSegment.add_transition() |
| `transitions[].duration_frames` | duration_us = frames * (1_000_000 / fps) |
| `color_correction` | Not supported — note in manifest only |
| `fps` | ScriptFile fps parameter |
| `resolution` | ScriptFile width/height |

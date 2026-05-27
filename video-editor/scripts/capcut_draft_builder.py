#!/usr/bin/env python3
"""
capcut_draft_builder.py

Converts edit_plan.json (from plan_edit.py) into a CapCut Desktop draft.

Usage:
  python3 capcut_draft_builder.py \
    --plan <output>/edit_plan.json \
    --clips-dir <path/to/clips> \
    --draft-name "reel_tribotax_01" \
    [--draft-root /path/to/capcut/projects/]  # auto-detected if omitted
    [--overlays-dir <path/to/overlays/>]      # folder with .mov ProRes alpha overlays
    [--sfx-index <path/to/sfx_index.json>]   # SFX category index
    [--reel-name <name>]                      # used for random seed in SFX selection
    [--open]  # launch CapCut after writing

CapCut 8.x compatibility notes (macOS):
  - Projects folder: ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/
  - Uses root_meta_info.json as project index (must register each new draft)
  - Requires draft_info.json (CapCut 8 format), not just draft_content.json
  - Platform must be "mac" — Windows-origin drafts are rejected with "unusual path"
  - Each video material needs a local_material_id UUID set
  - First open will show "Link media" dialog: click it, select the clips folder,
    CapCut auto-links all files. One-time step per project.
"""

import sys
import json
import uuid
import random
import argparse
import subprocess
from pathlib import Path

try:
    from pyJianYingDraft import (
        DraftFolder, VideoSegment, VideoMaterial, TextSegment, TextStyle,
        TrackType, Timerange, ClipSettings
    )
    from pyJianYingDraft.metadata import TransitionType
except ImportError:
    print("ERROR: pyJianYingDraft not installed. Run: pip3 install pyJianYingDraft")
    sys.exit(1)

SEC = 1_000_000  # microseconds per second

# Cap por categoria de SFX — sem isso, sons longos (riser 19s, cinematica 5s)
# tocam até o fim e ficam fora de contexto / sobrepostos.
# Valores em ms. Ajuste no plan_edit se um caso específico precisar de mais.
SFX_DURATION_CAPS_MS = {
    "WOOSH":      1500, "CLICK":         400, "DIGITAL":     1200,
    "TRANSIÇÃO":  1500, "CAMERA":         600, "PLIM":        1200,
    "RISER":      3000, "VARIAVEIS":     2000, "AMBIENTE":   10000,
    "CINEMATICA": 3500, "ROLAGEM":       2000, "GLITCH":      1200,
    "TECLADO":    3000, "DINHEIRO":      2000, "ESTALO":       400,
    "CONTAGEM":   2500, "POPS":           600, "BOOM":        3000,
    "NOTIFICATION": 1200, "DRUM":        1000, "GLASS_BREAK": 2000,
    "APPLAUSE":   3000, "HORROR":        3000, "FAIL":        2500,
    "MAGIC":      2000, "HEARTBEAT":     4000,
}
SFX_DEFAULT_CAP_MS = 2000

TRANSITION_MAP = {
    "fade":     "叠化",
    "slide_up": "向上",
    "wipe":     "渐变擦除",
    "none":     None,
}

# Extra top-level fields present in CapCut 8.x draft_info.json
_EXTRA_TOP_FIELDS = {
    "draft_type": "",
    "function_assistant_info": {},
    "is_drop_frame_timecode": False,
    "lyrics_effects": [],
    "path": "",
    "smart_ads_info": {},
    "uneven_animation_template_info": {},
}


def find_capcut_projects_dir() -> Path:
    """Auto-detect CapCut's macOS projects folder."""
    candidates = [
        # CapCut 8.x on macOS uses ~/Movies/CapCut (has root_meta_info.json)
        Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft",
        Path.home() / "Library/Containers/com.lemon.lvoverseas/Data/Library/Application Support/CapCut/User Data/Projects/com.lveditor.draft",
        Path.home() / "Library/Application Support/CapCut/User Data/Projects/com.lveditor.draft",
    ]
    for c in candidates:
        if c.exists():
            return c
    target = candidates[0]
    target.mkdir(parents=True, exist_ok=True)
    print(f"[capcut] Created projects folder: {target}")
    return target


def get_mac_platform(projects_dir: Path) -> dict:
    """Read macOS platform info from an existing native CapCut project, or use defaults."""
    for folder in sorted(projects_dir.iterdir()):
        if not folder.is_dir():
            continue
        info = folder / "draft_info.json"
        if info.exists():
            try:
                data = json.loads(info.read_text(encoding="utf-8"))
                plat = data.get("platform", {})
                if plat.get("os") == "mac" and plat.get("app_source") == "cc":
                    return plat
            except Exception:
                pass
    return {"os": "mac", "app_id": 359289, "app_source": "cc", "app_version": "8.5.0"}


def patch_to_draft_info(projects_dir: Path, draft_name: str) -> None:
    """
    Post-process pyJianYingDraft's draft_content.json → draft_info.json for CapCut 8.x:
      - Patches platform from 'windows/5.9.0' to native macOS
      - Gives the draft a unique id
      - Adds local_material_id + source_platform to each video material
      - Adds extra top-level fields expected by CapCut 8
    """
    draft_dir    = projects_dir / draft_name
    content_path = draft_dir / "draft_content.json"
    info_path    = draft_dir / "draft_info.json"

    if not content_path.exists():
        print(f"  [WARN] draft_content.json not found in {draft_dir}")
        return

    with open(content_path, encoding="utf-8") as f:
        data = json.load(f)

    # Platform: must be mac or CapCut rejects with "unusual path"
    mac_platform = get_mac_platform(projects_dir)
    data["platform"] = mac_platform
    data["last_modified_platform"] = mac_platform

    # Unique id so multiple drafts don't collide
    data["id"] = str(uuid.uuid4()).upper()

    # Extra top-level fields
    for k, v in _EXTRA_TOP_FIELDS.items():
        if k not in data:
            data[k] = v

    # Video materials: add local_material_id + source_platform
    for v in data.get("materials", {}).get("videos", []):
        if not v.get("local_material_id"):
            v["local_material_id"] = str(uuid.uuid4())
        if v.get("source_platform") is None:
            v["source_platform"] = 0
        if not v.get("category_name"):
            v["category_name"] = "local"

    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[capcut] draft_info.json written ({info_path.stat().st_size // 1024}KB)")


def verify_draft(projects_dir: Path, draft_name: str) -> bool:
    """
    Verify every video segment in the timeline has an accessible file on disk.
    Returns True if all OK, False if any file is missing.
    """
    info_path = projects_dir / draft_name / "draft_info.json"
    if not info_path.exists():
        print(f"  [VERIFY] draft_info.json not found")
        return False

    with open(info_path, encoding="utf-8") as f:
        data = json.load(f)

    # Build id → path map for video materials only
    mat_map = {
        v["id"]: v.get("path", "")
        for v in data.get("materials", {}).get("videos", [])
    }

    # Collect material_ids used by video tracks only
    video_mat_ids = set()
    for track in data.get("tracks", []):
        if track.get("type") == "video":
            for seg in track.get("segments", []):
                mid = seg.get("material_id")
                if mid:
                    video_mat_ids.add(mid)

    missing = []
    for mid in video_mat_ids:
        p = mat_map.get(mid, "NOT_IN_MATERIALS")
        if not p or not Path(p).exists():
            missing.append(p or f"(no path for id {mid[:8]})")

    if missing:
        for p in missing:
            print(f"  [VERIFY] missing: {p}")
        return False

    print(f"[capcut] verify: {len(video_mat_ids)} video clips all accessible on disk")
    return True


def register_in_root_meta(projects_dir: Path, draft_name: str, duration_us: int) -> None:
    """Add draft to root_meta_info.json so CapCut 8.x lists it in the Drafts tab."""
    import time as _time
    root_meta = projects_dir / "root_meta_info.json"
    if not root_meta.exists():
        return  # older CapCut layout — no index needed

    try:
        with open(root_meta, encoding="utf-8") as f:
            root = json.load(f)
    except Exception as e:
        print(f"  [WARN] Could not read root_meta_info.json: {e}")
        return

    fold_path = str(projects_dir / draft_name)
    existing = {e.get("draft_fold_path") for e in root.get("all_draft_store", [])}
    if fold_path in existing:
        print(f"[capcut] root_meta_info.json: '{draft_name}' already registered")
        return

    now_us = int(_time.time() * 1_000_000)
    entry = {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": f"{fold_path}/draft_cover.jpg",
        "draft_fold_path": fold_path,
        "draft_id": str(uuid.uuid4()).upper(),
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_json_file": f"{fold_path}/draft_info.json",
        "draft_name": draft_name,
        "draft_new_version": "",
        "draft_root_path": str(projects_dir),
        "draft_timeline_materials_size": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "streaming_edit_draft_ready": True,
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": duration_us,
    }
    root.setdefault("all_draft_store", []).insert(0, entry)

    with open(root_meta, "w", encoding="utf-8") as f:
        json.dump(root, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[capcut] root_meta_info.json: registered '{draft_name}'")


def us(seconds: float) -> int:
    """Convert seconds (float) to microseconds (int)."""
    return int(round(seconds * SEC))


# ── NEW: overlay alpha track (V2) ──────────────────────────────────────────────

import re as _re

def _build_overlay_timeline_map(plan: dict) -> dict:
    """
    Mapeia overlay-id (stem do .mov) → timeline_start_us, batendo com o padrão
    que Root.tsx gera (`overlay_{idx:02d}_{kind_normalized}`) a partir de
    plan.rich_overlays. Compat com overlays_v2 (legacy) também.
    """
    result: dict = {}

    # 1. rich_overlays (preferido) — IDs no formato Remotion-safe (apenas hifens)
    for i, ov in enumerate(plan.get("rich_overlays", [])):
        kind = _re.sub(r"[^a-zA-Z0-9-]", "-", str(ov.get("kind", "overlay")))
        cid = f"overlay-{i:02d}-{kind}"
        result[cid] = us(float(ov.get("start", 0.0)))

    # 2. overlays_v2 legado (filename ou text como chave)
    for i, ov in enumerate(plan.get("overlays_v2", [])):
        key = Path(ov.get("filename") or ov.get("text", f"overlay_{i}")).stem
        result.setdefault(key, us(float(ov.get("start", 0.0))))
    return result


def add_overlay_alpha_track(script, overlays_dir: Path, plan: dict) -> int:
    """
    V2: VideoSegment por .mov ProRes 4444 alpha em overlays_dir.

    Timeline position do plan.rich_overlays[i].start (segundos) mapeada via
    stem do arquivo (overlay_{i:02d}_{kind}). Sem match, vai pra 0 e avisa.
    """
    mov_files = sorted(overlays_dir.glob("*.mov"))
    if not mov_files:
        print(f"  [V2-overlays] No .mov files found in {overlays_dir}")
        return 0

    timeline_map = _build_overlay_timeline_map(plan)

    # Overlays podem sobrepor (e.g. roman_columns_bg dura 14s atrás de
    # vespasian_bust 5.6s + roman_latrine 2.6s). pyJianYingDraft rejeita
    # overlap dentro da mesma track, então criamos tracks V2,V3,V4...
    # conforme necessário (greedy: cada overlay vai pra primeira track livre).
    tracks_in_use: list[tuple[str, int]] = []  # (track_name, end_us)

    def get_track_for(start_us: int, end_us: int) -> str:
        for i, (name, t_end) in enumerate(tracks_in_use):
            if start_us >= t_end - 1000:  # 1ms folga
                tracks_in_use[i] = (name, end_us)
                return name
        # nova track necessária
        idx = len(tracks_in_use) + 2  # V2, V3, V4...
        track_name = f"overlays_alpha_v{idx}"
        try:
            script.add_track(TrackType.video, track_name, relative_index=idx - 1)
        except Exception as e:
            print(f"  [V2-overlays] Não consegui criar {track_name}: {e}")
            raise
        tracks_in_use.append((track_name, end_us))
        return track_name

    # Ordena por start_us — greedy track assignment funciona melhor
    sorted_movs = sorted(mov_files, key=lambda m: timeline_map.get(m.stem, 0))

    added = 0
    for mov in sorted_movs:
        stem = mov.stem
        if stem not in timeline_map:
            print(f"  [V2-overlays] WARN sem timeline match: {mov.name} → 0s")
        timeline_start_us = timeline_map.get(stem, 0)
        duration_us = _probe_duration_us(mov)
        end_us = timeline_start_us + duration_us
        source_tr = Timerange(0, duration_us)
        target_tr = Timerange(timeline_start_us, duration_us)

        try:
            track_name = get_track_for(timeline_start_us, end_us)
            seg = VideoSegment(str(mov), target_tr, source_timerange=source_tr, volume=0.0)
            script.add_segment(seg, track_name=track_name)
            added += 1
            print(f"  [V2-overlays] [{track_name}] {mov.name} @ "
                  f"{timeline_start_us / SEC:.2f}s ({duration_us / SEC:.2f}s)")
        except Exception as e:
            print(f"  [V2-overlays] WARN: could not add {mov.name}: {e}")

    if tracks_in_use:
        print(f"  [V2-overlays] usou {len(tracks_in_use)} track(s) "
              f"({', '.join(n for n,_ in tracks_in_use)}) pra acomodar overlaps")
    return added


def _probe_duration_us(path: Path, fallback_s: float = 3.0) -> int:
    """Use ffprobe to get clip duration in microseconds, with a safe fallback."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10
        )
        dur_s = float(result.stdout.strip())
        return us(dur_s)
    except Exception:
        return us(fallback_s)


# ── NEW: SFX audio track (A2) ──────────────────────────────────────────────────

def add_sfx_track(script, sfx_plan: list, sfx_index: dict, reel_name: str) -> int:
    """
    Add Track A2: one AudioSegment per item in edit_plan["sfx"].

    sfx_plan items: {"at_ms": int, "category": str, "intent": str, "volume_db": float}
    sfx_index:      {"categories": {"WOOSH": {"files": ["path1.wav", ...]}, ...}}

    Uses random.seed(reel_name + category) for reproducible file selection.
    Falls back to direct JSON patch on draft_content.json if pyJianYingDraft
    does not expose an AudioSegment API.

    Returns number of SFX segments added.
    """
    if not sfx_plan:
        return 0

    categories = sfx_index.get("categories", {})
    added = 0

    # Try pyJianYingDraft's AudioSegment import (may not be available in all versions)
    try:
        from pyJianYingDraft import AudioSegment as _AudioSegment  # type: ignore
        _has_audio_api = True
    except ImportError:
        _has_audio_api = False

    if _has_audio_api:
        try:
            script.add_track(TrackType.audio)
        except Exception as e:
            print(f"  [A2-sfx] Could not add audio track via API: {e}")
            _has_audio_api = False

    sfx_patches = []  # collect for JSON-patch fallback

    # Pré-computa o "próximo at_ms" pra cada SFX. Se um SFX longo (riser 19s)
    # for colocado a 0ms e o próximo SFX está a 8500ms, o primeiro é cortado em
    # 8500ms pra não sobrepor — preserva a intenção do plano e evita audio
    # caótico/loopado.
    sorted_indexed = sorted(enumerate(sfx_plan), key=lambda p: int(p[1].get("at_ms", 0)))
    next_at_ms: dict[int, int] = {}
    for idx_in_sorted, (orig_idx, item) in enumerate(sorted_indexed):
        if idx_in_sorted + 1 < len(sorted_indexed):
            next_at_ms[orig_idx] = int(sorted_indexed[idx_in_sorted + 1][1].get("at_ms", 0))
        else:
            next_at_ms[orig_idx] = None  # sem limite à direita

    for sfx_idx, item in enumerate(sfx_plan):
        category = item.get("category", "").upper()
        at_ms = int(item.get("at_ms", 0))
        volume_db = float(item.get("volume_db", -10.0))
        volume_linear = min(1.0, max(0.0, 10 ** (volume_db / 20.0)))

        cat_data = categories.get(category, {})
        files = cat_data.get("files", [])
        if not files:
            print(f"  [A2-sfx] WARN: no files for category '{category}', skipping")
            continue

        rng = random.Random()
        rng.seed(reel_name + category)
        chosen = rng.choice(files)
        chosen_path = Path(chosen)

        at_us = at_ms * 1000
        source_duration_us = _probe_duration_us(chosen_path, fallback_s=1.0)

        # Aplica cap por categoria + limite até o próximo SFX
        cap_ms = SFX_DURATION_CAPS_MS.get(category, SFX_DEFAULT_CAP_MS)
        cap_us = cap_ms * 1000
        nxt = next_at_ms.get(sfx_idx)
        gap_to_next_us = (nxt * 1000 - at_us - 50_000) if nxt is not None else None  # 50ms folga
        # Trim ao mínimo entre: source_duration, cap_por_categoria, gap_ate_proximo
        candidates = [source_duration_us, cap_us]
        if gap_to_next_us is not None and gap_to_next_us > 0:
            candidates.append(gap_to_next_us)
        duration_us = min(candidates)
        # Floor pra ms inteiro (evita timeranges não-quantizadas que rejeitam o API)
        duration_us = (duration_us // 1000) * 1000

        if _has_audio_api:
            try:
                from pyJianYingDraft import AudioSegment as _AudioSegment  # type: ignore
                source_tr = Timerange(0, duration_us)
                target_tr = Timerange(at_us, duration_us)
                seg = _AudioSegment(str(chosen_path), target_tr, source_timerange=source_tr,
                                    volume=volume_linear)
                script.add_segment(seg)
                added += 1
                print(f"  [A2-sfx] {category} → {chosen_path.name} @ {at_ms}ms vol={volume_db}dB")
                continue
            except Exception as e:
                print(f"  [A2-sfx] AudioSegment API failed ({e}), will patch JSON directly")
                _has_audio_api = False  # disable for remaining items

        # Fallback: record for JSON patch
        sfx_patches.append({
            "path": str(chosen_path.resolve()),
            "at_us": at_us,
            "duration_us": duration_us,
            "volume_linear": volume_linear,
            "category": category,
        })

    if sfx_patches:
        added += _patch_sfx_into_draft_content(script, sfx_patches)

    return added


def _patch_sfx_into_draft_content(script, sfx_patches: list) -> int:
    """
    Directly patch draft_content.json (after script.save()) to add audio segments.
    Called only when pyJianYingDraft's AudioSegment API is unavailable.

    NOTE: script.save() must have been called before this function is invoked.
    We collect patches and apply them in a post-save hook (see build_draft).
    """
    # Store patches on the script object for deferred application
    if not hasattr(script, "_sfx_patches"):
        script._sfx_patches = []
    script._sfx_patches.extend(sfx_patches)
    return 0  # actual count reported after apply_sfx_patches_to_json


def apply_sfx_patches_to_json(draft_dir: Path, sfx_patches: list) -> int:
    """
    Apply SFX audio patches directly to draft_content.json / draft_info.json.
    Called after script.save() in build_draft().

    CapCut audio segment structure (draft_content.json):
      materials.audios[]: {id, path, duration, name, ...}
      tracks[type==audio].segments[]: {id, material_id, target_timerange, source_timerange, volume, ...}
    """
    content_path = draft_dir / "draft_content.json"
    if not content_path.exists():
        print(f"  [A2-sfx-patch] draft_content.json not found, skipping SFX patch")
        return 0

    with open(content_path, encoding="utf-8") as f:
        data = json.load(f)

    mats = data.setdefault("materials", {})
    audios = mats.setdefault("audios", [])

    # Find or create audio track
    tracks = data.setdefault("tracks", [])
    audio_track = None
    for t in tracks:
        if t.get("type") == "audio":
            audio_track = t
            break
    if audio_track is None:
        audio_track = {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()).upper(),
            "is_default_name": True,
            "name": "",
            "segments": [],
            "type": "audio",
        }
        tracks.append(audio_track)

    added = 0
    for patch in sfx_patches:
        mat_id = str(uuid.uuid4()).upper()
        seg_id = str(uuid.uuid4()).upper()

        # Add audio material
        audios.append({
            "audio_fade": None,
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
            "duration": patch["duration_us"],
            "effect_id": "",
            "formula_id": "",
            "id": mat_id,
            "intensifies_sound": False,
            "local_material_id": str(uuid.uuid4()),
            "music_id": "",
            "name": Path(patch["path"]).stem,
            "path": patch["path"],
            "request_id": "",
            "resource_id": "",
            "source_platform": 0,
            "team_id": "",
            "text": "",
            "tone_category_id": "",
            "tone_category_name": "",
            "tone_effect_id": "",
            "tone_effect_name": "",
            "tone_platform": 0,
            "tone_second_category_id": "",
            "tone_second_category_name": "",
            "tone_speaker_id": "",
            "tone_type": 0,
            "type": "extract_music",
            "video_id": "",
            "wave_points": [],
        })

        # Add audio segment on the track
        audio_track["segments"].append({
            "caption_info": None,
            "cartoon": False,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "transform": {"x": 0.0, "y": 0.0},
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_correct_adjust": False,
            "enable_color_match_adjust": False,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": None,
            "id": seg_id,
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "key_frames": [],
            "loop": False,
            "material_id": mat_id,
            "render_index": 11000,
            "reverse": False,
            "source_timerange": {"duration": patch["duration_us"], "start": 0},
            "speed": 1.0,
            "target_timerange": {"duration": patch["duration_us"], "start": patch["at_us"]},
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 1,
            "uniform_scale": None,
            "visible": True,
            "volume": patch["volume_linear"],
        })

        added += 1
        print(f"  [A2-sfx-patch] {patch['category']} @ {patch['at_us'] // 1000}ms → {Path(patch['path']).name}")

    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[capcut] SFX patch: {added} segments written to draft_content.json")
    return added


# ── NEW: zoom keyframes patch ──────────────────────────────────────────────────

def apply_zoom_keyframes_to_json(draft_dir: Path, zoom_keyframes: list, plan_cuts: list, fps: int) -> None:
    """
    Apply zoom keyframes to VideoSegments in draft_content.json.

    zoom_keyframes items:
      {"clip_idx": int, "at_ms": int, "scale": float, "transform_x": float, "transform_y": float}

    clip_idx refers to the index in plan["v1_main"].
    We locate the corresponding segment in the first video track (by order).

    CapCut keyframe format (uniform_scale_keyframe type "KFTypeScaleX/Y"):
    We use "common_keyframes" with property_type "KFTypeScaleX" and "KFTypeScaleY".
    """
    content_path = draft_dir / "draft_content.json"
    if not content_path.exists():
        return

    with open(content_path, encoding="utf-8") as f:
        data = json.load(f)

    # Locate first video track segments
    video_segments = []
    for track in data.get("tracks", []):
        if track.get("type") == "video":
            video_segments = track.get("segments", [])
            break

    if not video_segments:
        print("  [zoom-kf] No video segments found, skipping zoom keyframes")
        return

    # Group keyframes by clip_idx
    by_clip: dict[int, list] = {}
    for kf in zoom_keyframes:
        idx = int(kf.get("clip_idx", 0))
        by_clip.setdefault(idx, []).append(kf)

    modified = 0
    for clip_idx, kf_list in by_clip.items():
        if clip_idx >= len(video_segments):
            print(f"  [zoom-kf] WARN: clip_idx={clip_idx} out of range ({len(video_segments)} segments)")
            continue

        seg = video_segments[clip_idx]
        kf_store = seg.setdefault("common_keyframes", [])

        for kf in kf_list:
            at_ms = int(kf.get("at_ms", 0))
            at_us = at_ms * 1000
            scale = float(kf.get("scale", 1.0))
            tx = float(kf.get("transform_x", 0.0))
            ty = float(kf.get("transform_y", 0.0))

            # CapCut uses separate keyframe entries per property
            # Scale: KFTypeScaleX and KFTypeScaleY (or "uniform_scale")
            for prop, value in [("KFTypeScaleX", scale), ("KFTypeScaleY", scale)]:
                kf_store.append({
                    "curveType": "Line",
                    "graphValue": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "property_type": prop,
                    "time_offset": at_us,
                    "values": [value],
                })

            # Transform X/Y (position offset, normalized -1..1)
            if tx != 0.0:
                kf_store.append({
                    "curveType": "Line",
                    "graphValue": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "property_type": "KFTypePositionX",
                    "time_offset": at_us,
                    "values": [tx],
                })
            if ty != 0.0:
                kf_store.append({
                    "curveType": "Line",
                    "graphValue": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "property_type": "KFTypePositionY",
                    "time_offset": at_us,
                    "values": [ty],
                })

        modified += 1
        print(f"  [zoom-kf] clip[{clip_idx}]: {len(kf_list)} keyframe(s) added")

    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[capcut] Zoom keyframes: {modified} clip(s) patched in draft_content.json")


# ── MAIN BUILD ─────────────────────────────────────────────────────────────────

def build_draft(plan_path: str, clips_dir: str, draft_name: str,
                draft_root=None, open_capcut=False,
                overlays_dir=None, sfx_index_path=None, reel_name=None):

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    clips_dir = Path(clips_dir)
    fps: int = int(plan.get("fps", 30))
    resolution: list = plan.get("resolution", [1080, 1920])
    width, height = resolution[0], resolution[1]

    reel_name = reel_name or draft_name

    projects_dir = Path(draft_root) if draft_root else find_capcut_projects_dir()
    draft_folder = DraftFolder(str(projects_dir))

    print(f"[capcut] Building draft '{draft_name}' -> {projects_dir / draft_name}")
    script = draft_folder.create_draft(
        draft_name, width, height, fps, allow_replace=True
    )

    # ── VIDEO TRACK (V1) ─────────────────────────────────────────────────────
    script.add_track(TrackType.video)

    cuts = plan.get("v1_main", [])
    transitions_list = plan.get("transitions", [])
    trans_by_index = {t["after_cut_index"]: t for t in transitions_list}

    timeline_cursor = 0  # microseconds, accumulated

    # IMPORTANTE: dedupa VideoMaterial por path. Sem isso, cada VideoSegment
    # cria sua própria VideoMaterial e o CapCut, ao abrir o draft, dedupa
    # silenciosamente por path zerando source_timerange.start de alguns
    # segmentos (bug observado: cuts 3,4,6 do mesmo bruto ficavam com src=0
    # enquanto cut 5 mantinha — CapCut confunde-se ao ver múltiplas materials
    # pro mesmo arquivo). Compartilhando uma só material por arquivo, cada
    # segmento mantém seu próprio source_timerange independentemente.
    material_cache: dict[str, VideoMaterial] = {}

    for i, cut in enumerate(cuts):
        clip_file = clips_dir / cut["clip"]
        if not clip_file.exists():
            clip_file = Path(cut["clip"])
        if not clip_file.exists():
            print(f"  [WARN] clip not found: {cut['clip']} — skipping")
            continue

        source_in  = us(cut["source_in"])
        source_out = us(cut["source_out"])
        duration   = source_out - source_in

        source_tr = Timerange(source_in, duration)
        target_tr = Timerange(timeline_cursor, duration)

        path_key = str(clip_file.resolve())
        if path_key not in material_cache:
            material_cache[path_key] = VideoMaterial(path_key)
        seg = VideoSegment(material_cache[path_key], target_tr,
                           source_timerange=source_tr, volume=1.0)

        if i in trans_by_index:
            t_cfg = trans_by_index[i]
            t_type_name = TRANSITION_MAP.get(t_cfg.get("type", "none"))
            if t_type_name:
                dur_frames = t_cfg.get("duration_frames", 6)
                dur_us = int(dur_frames * SEC / fps)
                try:
                    t_type = TransitionType[t_type_name]
                    seg.add_transition(t_type, duration=dur_us)
                except (KeyError, AttributeError):
                    print(f"  [WARN] transition '{t_type_name}' not found, skipping")

        script.add_segment(seg)
        timeline_cursor += duration

    # ── VIDEO TRACK (V2) — alpha overlays ────────────────────────────────────
    overlays_added = 0
    if overlays_dir:
        overlays_dir = Path(overlays_dir)
        if overlays_dir.exists() and overlays_dir.is_dir():
            overlays_added = add_overlay_alpha_track(script, overlays_dir, plan)
            print(f"[capcut] V2-overlays: {overlays_added} overlay(s) added")
        else:
            print(f"  [WARN] --overlays-dir not found: {overlays_dir}")

    # ── TEXT TRACK (subtitles) ────────────────────────────────────────────────
    subtitle_track = plan.get("subtitle_track", [])
    if subtitle_track:
        script.add_track(TrackType.text)

        caption_style = TextStyle(
            size=8.0,
            bold=True,
            color=(1.0, 1.0, 1.0),
            alpha=1.0,
            align=1,
            auto_wrapping=True,
            max_line_width=0.82,
        )
        caption_clip = ClipSettings(transform_y=-0.8)

        for i, cap in enumerate(subtitle_track):
            t_start = us(cap["start"])
            next_start = us(subtitle_track[i + 1]["start"]) if i + 1 < len(subtitle_track) else None
            t_end = us(cap["end"])
            if next_start is not None and t_end >= next_start:
                t_end = max(t_start + 1, next_start - 1)
            duration = max(t_end - t_start, 1)
            if "text" in cap:
                raw = cap["text"]
            else:
                raw = " ".join(w["text"] for w in cap.get("words", []))
            text = raw.upper() if cap.get("style", "") != "minimal" else raw

            seg = TextSegment(
                text,
                Timerange(t_start, duration),
                style=caption_style,
                clip_settings=caption_clip,
            )
            try:
                script.add_segment(seg)
            except Exception as e:
                print(f"  [WARN] caption '{text}' skipped: {e}")

    # ── OVERLAYS (big stats / titles) ─────────────────────────────────────────
    overlays = plan.get("overlays_v2", [])
    if overlays:
        if TrackType.text not in [track.track_type for track in script.tracks.values()]:
            script.add_track(TrackType.text)

        overlay_style = TextStyle(
            size=14.0, bold=True, color=(1.0, 1.0, 1.0), alpha=1.0, align=1,
        )

        for ov in overlays:
            t_start  = us(ov["start"])
            t_end    = us(ov["end"])
            duration = max(t_end - t_start, 1)
            full_text = ov["text"]
            if ov.get("subtext"):
                full_text += f"\n{ov['subtext']}"
            seg = TextSegment(full_text, Timerange(t_start, duration), style=overlay_style)
            try:
                script.add_segment(seg)
            except Exception as e:
                print(f"  [WARN] overlay '{full_text[:30]}' skipped: {e}")

    # ── AUDIO TRACK (A2) — SFX ───────────────────────────────────────────────
    sfx_plan = plan.get("sfx", [])
    sfx_patches_deferred = []
    sfx_added = 0

    if sfx_plan and sfx_index_path:
        sfx_index_path = Path(sfx_index_path)
        if sfx_index_path.exists():
            with open(sfx_index_path, encoding="utf-8") as f:
                sfx_index = json.load(f)
            sfx_added = add_sfx_track(script, sfx_plan, sfx_index, reel_name)
            # Collect deferred patches if API was unavailable
            if hasattr(script, "_sfx_patches"):
                sfx_patches_deferred = script._sfx_patches
        else:
            print(f"  [WARN] --sfx-index not found: {sfx_index_path}")
    elif sfx_plan:
        print("  [WARN] edit_plan has sfx[] but --sfx-index not provided — skipping SFX")

    # ── SAVE ──────────────────────────────────────────────────────────────────
    script.save()
    draft_path = projects_dir / draft_name
    print(f"[capcut] Draft files written to: {draft_path}")
    print(f"[capcut]    Cuts: {len(cuts)}  |  Captions: {len(subtitle_track)}  |  Overlays: {len(overlays)}")
    print(f"[capcut]    V2-overlays: {overlays_added}  |  SFX: {sfx_added}")

    # Post-save: apply deferred SFX JSON patches (if AudioSegment API was unavailable)
    if sfx_patches_deferred:
        extra = apply_sfx_patches_to_json(draft_path, sfx_patches_deferred)
        sfx_added += extra

    # Post-save: apply zoom keyframes via JSON patch
    zoom_keyframes = plan.get("zoom_keyframes", [])
    if zoom_keyframes:
        apply_zoom_keyframes_to_json(draft_path, zoom_keyframes, cuts, fps)

    # Post-process: create CapCut 8.x compatible draft_info.json
    patch_to_draft_info(projects_dir, draft_name)

    # Register in the project index so CapCut lists it in Drafts tab
    total_duration_us = sum((us(c["source_out"]) - us(c["source_in"])) for c in cuts)
    register_in_root_meta(projects_dir, draft_name, total_duration_us)

    # Verify all clip paths are accessible on disk before declaring done
    ok = verify_draft(projects_dir, draft_name)
    if not ok:
        print("[capcut] Some clips not found — check --clips-dir path")
    else:
        print(f"[capcut] Draft ready: '{draft_name}'")
        print(f"[capcut]    On first open, CapCut shows 'Link media' — click it,")
        print(f"[capcut]    select the clips folder, and it auto-links all files.")

    if open_capcut:
        subprocess.Popen(["open", "-a", "/Applications/CapCut.app"])

    return draft_path


def main():
    parser = argparse.ArgumentParser(description="Build a CapCut draft from edit_plan.json")
    parser.add_argument("--plan",          required=True,  help="Path to edit_plan.json")
    parser.add_argument("--clips-dir",     required=True,  help="Directory containing clips (raw or proxy)")
    parser.add_argument("--draft-name",    required=True,  help="Name of the CapCut project")
    parser.add_argument("--draft-root",    default=None,   help="Override CapCut projects folder")
    parser.add_argument("--overlays-dir",  default=None,   help="Folder with .mov ProRes alpha overlay files (Track V2)")
    parser.add_argument("--sfx-index",     default=None,   help="Path to sfx_index.json (for Track A2 SFX)")
    parser.add_argument("--reel-name",     default=None,   help="Reel name used as random seed for SFX selection")
    parser.add_argument("--open",          action="store_true", help="Launch CapCut after writing")
    args = parser.parse_args()

    build_draft(
        plan_path=args.plan,
        clips_dir=args.clips_dir,
        draft_name=args.draft_name,
        draft_root=args.draft_root,
        open_capcut=args.open,
        overlays_dir=args.overlays_dir,
        sfx_index_path=args.sfx_index,
        reel_name=args.reel_name,
    )


if __name__ == "__main__":
    main()

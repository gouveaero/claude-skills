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
import argparse
import subprocess
from pathlib import Path

try:
    from pyJianYingDraft import (
        DraftFolder, VideoSegment, TextSegment, TextStyle,
        TrackType, Timerange, ClipSettings
    )
    from pyJianYingDraft.metadata import TransitionType
except ImportError:
    print("ERROR: pyJianYingDraft not installed. Run: pip3 install pyJianYingDraft")
    sys.exit(1)

SEC = 1_000_000  # microseconds per second

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
        print(f"  [VERIFY] ❌ draft_info.json not found")
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
            print(f"  [VERIFY] ❌ missing: {p}")
        return False

    print(f"[capcut] ✅ verify: {len(video_mat_ids)} video clips all accessible on disk")
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


def build_draft(plan_path: str, clips_dir: str, draft_name: str,
                draft_root=None, open_capcut=False):
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    clips_dir = Path(clips_dir)
    fps: int = int(plan.get("fps", 30))
    resolution: list = plan.get("resolution", [1080, 1920])
    width, height = resolution[0], resolution[1]

    projects_dir = Path(draft_root) if draft_root else find_capcut_projects_dir()
    draft_folder = DraftFolder(str(projects_dir))

    print(f"[capcut] Building draft '{draft_name}' → {projects_dir / draft_name}")
    script = draft_folder.create_draft(
        draft_name, width, height, fps, allow_replace=True
    )

    # ── VIDEO TRACK ──────────────────────────────────────────────────────────
    script.add_track(TrackType.video)

    cuts = plan.get("v1_main", [])
    transitions_list = plan.get("transitions", [])
    trans_by_index = {t["after_cut_index"]: t for t in transitions_list}

    timeline_cursor = 0  # microseconds, accumulated

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

        seg = VideoSegment(str(clip_file), target_tr, source_timerange=source_tr, volume=1.0)

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

    # ── SAVE ──────────────────────────────────────────────────────────────────
    script.save()
    draft_path = projects_dir / draft_name
    print(f"[capcut] Draft files written to: {draft_path}")
    print(f"[capcut]    Cuts: {len(cuts)}  |  Captions: {len(subtitle_track)}  |  Overlays: {len(overlays)}")

    # Post-process: create CapCut 8.x compatible draft_info.json
    patch_to_draft_info(projects_dir, draft_name)

    # Register in the project index so CapCut lists it in Drafts tab
    total_duration_us = sum((us(c["source_out"]) - us(c["source_in"])) for c in cuts)
    register_in_root_meta(projects_dir, draft_name, total_duration_us)

    # Verify all clip paths are accessible on disk before declaring done
    ok = verify_draft(projects_dir, draft_name)
    if not ok:
        print("[capcut] ⚠️  Some clips not found — check --clips-dir path")
    else:
        print(f"[capcut] ✅ Draft ready: '{draft_name}'")
        print(f"[capcut]    On first open, CapCut shows 'Link media' — click it,")
        print(f"[capcut]    select the clips folder, and it auto-links all files.")

    if open_capcut:
        subprocess.Popen(["open", "-a", "/Applications/CapCut.app"])

    return draft_path


def main():
    parser = argparse.ArgumentParser(description="Build a CapCut draft from edit_plan.json")
    parser.add_argument("--plan",       required=True,  help="Path to edit_plan.json")
    parser.add_argument("--clips-dir",  required=True,  help="Directory containing clips (raw or proxy)")
    parser.add_argument("--draft-name", required=True,  help="Name of the CapCut project")
    parser.add_argument("--draft-root", default=None,   help="Override CapCut projects folder")
    parser.add_argument("--open",       action="store_true", help="Launch CapCut after writing")
    args = parser.parse_args()

    build_draft(
        plan_path=args.plan,
        clips_dir=args.clips_dir,
        draft_name=args.draft_name,
        draft_root=args.draft_root,
        open_capcut=args.open,
    )


if __name__ == "__main__":
    main()

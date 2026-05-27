#!/usr/bin/env python3
"""
color_grade_davinci.py — color grade clips via DaVinci Resolve Studio's RCM.

Better than ffmpeg for HLG sources because Resolve's color management is
production-grade. Phases:

  Phase 1: Connect, create project, configure RCM (Rec.2020 HLG → Rec.709 Gamma 2.4)
  Phase 2: Import a single test clip, render a quick preview, verify visually
  Phase 3: If preview looks good, import all clips, render batch

Usage:
  # Phase 1+2 (test single clip):
  python3 color_grade_davinci.py --input <dir> --test-clip <filename>

  # Phase 3 (batch all clips):
  python3 color_grade_davinci.py --input <dir> --output <dir> --batch
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resolve_helpers import connect, get_or_create_project, ResolveError  # noqa


def configure_rcm(project) -> bool:
    """Enable Resolve Color Management with HLG → Rec.709 conversion.

    Returns True if all settings stuck.
    """
    settings = {
        "colorScienceMode": "davinciYRGBColorManaged",
        "rcmPresetMode": "Custom",
        "separateColorSpaceAndGamma": "0",
        "colorSpaceInput": "Rec.2020 HLG ARIB STD-B67",
        "colorSpaceTimeline": "Rec.709 Gamma 2.4",
        "colorSpaceOutput": "Rec.709 Gamma 2.4",
    }
    print("\n━━━ Phase 1: Configure RCM ━━━")
    all_ok = True
    for key, value in settings.items():
        ok = bool(project.SetSetting(key, value))
        actual = project.GetSetting(key)
        match = (str(actual) == value) or (value.lower() in str(actual).lower())
        flag = "✓" if (ok and match) else "✗"
        print(f"  {flag} {key} = {actual!r} (wanted {value!r})")
        if not (ok and match):
            all_ok = False
    return all_ok


def import_clip(project, clip_path: Path):
    """Import a single clip via local /tmp shadow (avoids cloud-storage issues)."""
    mp = project.GetMediaPool()
    tmp_root = Path("/tmp") / "video_editor_davinci_imports"
    tmp_root.mkdir(parents=True, exist_ok=True)
    dst = tmp_root / clip_path.name
    if not dst.exists() or dst.stat().st_size != clip_path.stat().st_size:
        print(f"  Copying to /tmp shadow: {dst}")
        shutil.copy2(clip_path, dst)
    items = mp.ImportMedia([str(dst)])
    if not items:
        raise ResolveError(f"Failed to import {clip_path.name}")
    return items[0]


def add_clips_to_timeline(project, items: list, timeline_name: str = "color_grade_tl",
                          width: int = 3840, height: int = 2160, fps: str = "24"):
    """Create timeline at explicit format then append items.

    Project-level settings don't reliably propagate to new timelines, so we
    override at the timeline level via useCustomSettings=1.
    """
    mp = project.GetMediaPool()
    timeline = mp.CreateEmptyTimeline(timeline_name)
    if timeline is None:
        raise ResolveError(f"Failed to create timeline '{timeline_name}'")
    timeline.SetSetting("useCustomSettings", "1")
    timeline.SetSetting("timelineResolutionWidth", str(width))
    timeline.SetSetting("timelineResolutionHeight", str(height))
    timeline.SetSetting("timelineOutputResolutionWidth", str(width))
    timeline.SetSetting("timelineOutputResolutionHeight", str(height))
    timeline.SetSetting("timelineFrameRate", fps)
    actual_w = timeline.GetSetting("timelineResolutionWidth")
    actual_h = timeline.GetSetting("timelineResolutionHeight")
    print(f"  Timeline format: {actual_w}x{actual_h} @ {timeline.GetSetting('timelineFrameRate')}fps")
    if not mp.AppendToTimeline(items):
        raise ResolveError("AppendToTimeline failed")
    return timeline


def render_test_clip(project, output_dir: Path, duration_seconds: float = 4.0) -> Path | None:
    """Render the first 4s of the current timeline as a quick test preview."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        raise ResolveError("No current timeline")

    fps = float(timeline.GetSetting("timelineFrameRate") or 30)
    start_frame = timeline.GetStartFrame()
    end_frame = start_frame + int(round(duration_seconds * fps))

    print(f"\n━━━ Render test preview ({duration_seconds}s) ━━━")
    project.DeleteAllRenderJobs()
    settings = {
        "TargetDir": str(output_dir),
        "CustomName": "_test_preview",
        "ExportVideo": True,
        "ExportAudio": True,
        "FormatWidth": 3840,
        "FormatHeight": 2160,
        "VideoCodec": "H264",
        "AudioCodec": "aac",
        "VideoQuality": 0,
        "MarkIn": start_frame,
        "MarkOut": end_frame,
        "SelectAllFrames": False,
    }
    if not project.SetRenderSettings(settings):
        print("  ⚠️  SetRenderSettings returned False")
    job_id = project.AddRenderJob()
    if not job_id:
        raise ResolveError("AddRenderJob failed")
    print(f"  Render job: {job_id}")
    project.StartRendering([job_id])
    while project.IsRenderingInProgress():
        time.sleep(0.5)
    status = project.GetRenderJobStatus(job_id)
    print(f"  Status: {status}")

    # DaVinci may export as .mov even when we ask for H.264 — accept both
    for ext in (".mp4", ".mov"):
        candidate = output_dir / f"_test_preview{ext}"
        if candidate.exists():
            return candidate
    for f in output_dir.iterdir():
        if f.suffix.lower() in (".mp4", ".mov") and "preview" in f.stem.lower():
            return f
    return None


def extract_frame(mp4_path: Path, jpg_path: Path, time_offset: float = 1.0) -> bool:
    ffmpeg = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
    if not Path(ffmpeg).exists():
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-ss", str(time_offset),
           "-i", str(mp4_path), "-frames:v", "1",
           "-vf", "scale=480:-1", str(jpg_path)]
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and jpg_path.exists()


def cmd_test(args):
    """Phase 1+2: configure RCM, import single clip, render 4s preview, extract frame."""
    input_dir = args.input.expanduser().resolve()
    test_clip = input_dir / args.test_clip
    if not test_clip.exists():
        sys.exit(f"❌ Test clip not found: {test_clip}")

    output_dir = input_dir / "samples_color"
    output_dir.mkdir(exist_ok=True)

    resolve = connect()
    print(f"✓ Connected to Resolve {resolve.GetVersionString()}")

    project = get_or_create_project(resolve, args.project_name, folder=args.folder)
    print(f"✓ Project '{args.project_name}' ready")

    if not configure_rcm(project):
        print("\n⚠️  Some RCM settings didn't apply — proceeding anyway, check output")

    # Match source resolution (3840x2160 24fps) so we can evaluate color cleanly
    # without pillarboxing distorting the preview
    project.SetSetting("timelineFrameRate", "24")
    project.SetSetting("timelineResolutionWidth", "3840")
    project.SetSetting("timelineResolutionHeight", "2160")
    project.SetSetting("timelineOutputResolutionWidth", "3840")
    project.SetSetting("timelineOutputResolutionHeight", "2160")

    print("\n━━━ Phase 2: Import test clip & render preview ━━━")
    item = import_clip(project, test_clip)
    print(f"  ✓ Imported {test_clip.name}")
    timeline = add_clips_to_timeline(project, [item], "test_timeline")
    print(f"  ✓ Timeline '{timeline.GetName()}' created")

    preview_mp4 = render_test_clip(project, output_dir, duration_seconds=4.0)
    if not preview_mp4:
        sys.exit("❌ Test render failed — no MP4 produced")
    print(f"\n✓ Preview: {preview_mp4}")

    frame_jpg = output_dir / "frame_davinci_rcm.jpg"
    if extract_frame(preview_mp4, frame_jpg, time_offset=1.5):
        print(f"✓ Frame: {frame_jpg}")
    else:
        print("⚠️  Frame extract failed")


def cmd_batch(args):
    """Phase 3: render all clips with RCM."""
    input_dir = args.input.expanduser().resolve()
    output_dir = (args.output or (input_dir.parent / f"{input_dir.name}_graded")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    clips = sorted(p for p in input_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in {".mp4", ".mov"} and not p.name.startswith("."))
    if not clips:
        sys.exit(f"❌ No clips in {input_dir}")

    resolve = connect()
    project = get_or_create_project(resolve, args.project_name, folder=args.folder)
    configure_rcm(project)

    project.SetSetting("timelineFrameRate", "24")
    project.SetSetting("timelineResolutionWidth", "3840")
    project.SetSetting("timelineResolutionHeight", "2160")

    print(f"\n━━━ Importing {len(clips)} clips ━━━")
    items = []
    for clip in clips:
        item = import_clip(project, clip)
        items.append(item)
        print(f"  ✓ {clip.name}")

    timeline = add_clips_to_timeline(project, items, "batch_timeline")
    print(f"\n✓ Timeline '{timeline.GetName()}' with {len(items)} clips")

    # Render: each clip gets its own MP4 via "Individual Clips" mode
    project.DeleteAllRenderJobs()
    project.SetRenderSettings({
        "TargetDir": str(output_dir),
        "ExportVideo": True,
        "ExportAudio": True,
        "FormatWidth": 3840,
        "FormatHeight": 2160,
        "VideoCodec": "H264",
        "AudioCodec": "aac",
        "VideoQuality": 0,
        "ExportAlpha": False,
        "RenderMode": "Individual clips",
        "SelectAllFrames": True,
    })
    job_id = project.AddRenderJob()
    print(f"✓ Render job queued: {job_id}")
    print(f"  Output: {output_dir}")
    print("  Starting render — this will take a while for 24 4K clips...")
    project.StartRendering([job_id])
    last = -1
    while project.IsRenderingInProgress():
        st = project.GetRenderJobStatus(job_id)
        pct = st.get("CompletionPercentage", 0) if isinstance(st, dict) else 0
        if pct != last:
            print(f"    {pct}%")
            last = pct
        time.sleep(2)
    print(f"\n✓ Done. Files in {output_dir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", type=Path, help="(batch) Output dir")
    ap.add_argument("--test-clip", help="(test mode) Filename to test")
    ap.add_argument("--batch", action="store_true", help="Run batch mode (all clips)")
    ap.add_argument("--project-name", default="agiota_color_grade")
    ap.add_argument("--folder", default="TriboTax_Reels")
    args = ap.parse_args()

    if args.batch:
        cmd_batch(args)
    else:
        if not args.test_clip:
            sys.exit("❌ --test-clip required (or use --batch)")
        cmd_test(args)


if __name__ == "__main__":
    main()

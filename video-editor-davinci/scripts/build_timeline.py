#!/usr/bin/env python3
"""
build_timeline.py — turns an edit_plan.json into a real DaVinci Resolve project + timeline.

Usage:
    python3 build_timeline.py --plan edit_plan.json --clips-dir <dir>
                              [--brand-config /path/to/.video-editor.json]
                              [--project-name <name>]

Pre-requisites:
- DaVinci Resolve Studio must be running
- Env vars set (RESOLVE_SCRIPT_API, RESOLVE_SCRIPT_LIB, PYTHONPATH)
- Run scripts/check_setup.py to verify

What it does:
1. Connects to Resolve, creates/opens project (under brand's project_folder)
2. Configures fps + resolution from plan
3. Imports all source clips referenced in plan to MediaPool
4. Creates an empty timeline with the right format
5. Appends V1 cuts in order with source IN/OUT
6. Generates SRT from subtitle_track and imports as subtitle track
7. Saves the project
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import timedelta
from pathlib import Path

# Make resolve_helpers importable when running this script directly
sys.path.insert(0, str(Path(__file__).parent))
from resolve_helpers import (  # noqa: E402
    SCALE_FILL,
    ResolveError,
    append_audio_with_in_out,
    append_clip_with_in_out,
    apply_cdl,
    configure_project,
    connect,
    create_empty_timeline,
    get_or_create_project,
    import_clips,
    set_clip_scaling,
)


def srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp HH:MM:SS,mmm."""
    td = timedelta(seconds=max(0.0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hh, rem = divmod(total_ms, 3600_000)
    mm, rem = divmod(rem, 60_000)
    ss, ms = divmod(rem, 1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def write_srt(subtitle_track: list[dict], path: Path) -> None:
    lines: list[str] = []
    for i, entry in enumerate(subtitle_track, start=1):
        text = entry["text"].strip()
        if not text:
            continue
        lines.append(str(i))
        lines.append(f"{srt_timestamp(entry['start'])} --> {srt_timestamp(entry['end'])}")
        lines.append(text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def import_srt_to_timeline(project, srt_path: Path) -> bool:
    """Import an SRT file and append it to the current timeline as subtitles.

    Resolve's AppendToTimeline only routes to a subtitle track if one exists.
    We add a subtitle track first, then try a few payload variants.
    """
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        return False

    # Add a subtitle track if there isn't one
    if timeline.GetTrackCount("subtitle") == 0:
        timeline.AddTrack("subtitle")

    mp = project.GetMediaPool()
    items = mp.ImportMedia([str(srt_path)])
    if not items:
        return False

    # Try with explicit subtitle track + mediaType
    sub_idx = timeline.GetTrackCount("subtitle")
    for payload in (
        [{"mediaPoolItem": items[0], "trackIndex": sub_idx, "mediaType": 4}],
        [{"mediaPoolItem": items[0], "trackIndex": sub_idx}],
        items,  # bare items as final fallback
    ):
        try:
            if mp.AppendToTimeline(payload):
                return True
        except Exception:
            continue
    return False


_KEYWORD_RE = re.compile(r"^[\d★+\-]+%?$|%$|\$$|R\$")
_EMPHASIS_WORDS = {
    "AGIOTA", "MULTA", "SELIC", "FALÊNCIA", "FALENCIA", "DÍVIDA", "DIVIDA", "ATIVA",
    "GOVERNO", "BRASILEIRO", "EMPRESÁRIO", "EMPRESARIO", "PUNIR", "PENHORA",
    "DIAGNÓSTICO", "DIAGNOSTICO",
}


def _classify_word(w: str) -> str:
    """Return 'keyword' (big copper), 'emphasis' (medium yellow), or 'normal' (white)."""
    s = w.strip().upper().rstrip(".,!?")
    if not s:
        return "normal"
    # Numbers, percentages, currencies, ★-marked stats
    if _KEYWORD_RE.match(s) or "%" in s or "$" in s or "60%" in s:
        return "keyword"
    if any(c.isdigit() for c in s):
        return "keyword"
    if s in _EMPHASIS_WORDS:
        return "emphasis"
    return "normal"


def _import_via_tmp(mp, src_path: Path, tmp_root: Path):
    """Resolve refuses to import from cloud-storage paths (Google Drive / iCloud).
    Copy to a local /tmp shadow first, then import from there."""
    import shutil
    tmp_root.mkdir(parents=True, exist_ok=True)
    dst = tmp_root / src_path.name
    if not dst.exists() or dst.stat().st_size != src_path.stat().st_size:
        shutil.copy2(src_path, dst)
    return mp.ImportMedia([str(dst)])


def prerender_speed_clips(plan: dict, clips_dir: Path, cache_dir: Path) -> None:
    """Pre-render speed-ramped hero shots via ffmpeg and repoint the plan at them.

    DaVinci's scripting API has no exposed clip-speed/retime property: the
    official README's TimelineItem:SetProperty key list has `RetimeProcess` and
    `MotionEstimation`, but those only tune the interpolation QUALITY of a
    retime that already exists — there's no key to CREATE one, and there's no
    `ChangeClipSpeed` method anywhere in the API. So speed ramps for montage
    'hero shots' are done by pre-rendering a sped-up/slowed-down copy with
    ffmpeg and swapping the plan entry to point at it (same category of
    workaround as prerender_audio_duck below for the same underlying reason:
    the thing we need isn't scriptable, so we do it before Resolve gets involved).

    Mutates plan['v1_main'] in place: any cut with speed != 1.0 gets its 'clip'
    rewritten to an absolute path, with 'source_in'/'source_out' reset to
    0/new_duration (the whole pre-rendered file IS the trimmed shot).
    """
    import subprocess

    cache_dir.mkdir(parents=True, exist_ok=True)
    for cut in plan["v1_main"]:
        speed = float(cut.get("speed", 1.0))
        if speed == 1.0:
            continue

        src = Path(cut["clip"])
        if not src.is_absolute():
            src = clips_dir / src
        in_s, out_s = float(cut["source_in"]), float(cut["source_out"])
        orig_dur = out_s - in_s
        if orig_dur <= 0:
            continue
        new_dur = orig_dur / speed

        tag = f"{speed:g}".replace(".", "p").replace("-", "m")
        out_path = cache_dir / f"{src.stem}_{in_s:.2f}_{out_s:.2f}_x{tag}.mov"
        if not (out_path.exists() and out_path.stat().st_size > 0):
            vf = f"setpts=PTS/{speed}"
            if speed < 0.5:
                # Optical-flow interpolation avoids judder on deep slow-mo from a
                # 23.976fps source; skip it for milder ramps (slower + unnecessary).
                vf += ",minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc"
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-hwaccel", "videotoolbox",
                "-ss", f"{in_s:.3f}", "-i", str(src), "-t", f"{orig_dur:.3f}",
                "-vf", vf, "-an",
                "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le",
                str(out_path),
            ]
            print(f"   🐢 Pre-rendering speed x{speed:g} for {src.name} [{in_s:.2f}-{out_s:.2f}s] ...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Speed pre-render timed out for {src.name} — keeping original speed")
                continue
            if result.returncode != 0 or not out_path.exists():
                print(f"   ⚠️  Speed pre-render failed, keeping original speed: {(result.stderr or '')[-300:]}")
                continue

        cut["clip"] = str(out_path)
        cut["source_in"] = 0.0
        cut["source_out"] = round(new_dur, 3)


def duck_audio_segment(src: Path, in_s: float, out_s: float, cache_dir: Path, duck_db: float) -> Path | None:
    """Extract + attenuate ONLY the [in_s, out_s) audio for one cut — never the
    whole source file.

    Resolve's scripting API has no clip/track Volume or Gain property exposed
    to scripting (confirmed against the official README: MediaPoolItem has
    SetClipProperty for a fixed set of non-audio clip attributes like 'Super
    Scale', and Timeline has SetTrackEnable which only mutes/unmutes a WHOLE
    track — nothing sets a level). So ducking is done with ffmpeg.

    Earlier version of this ducked the ENTIRE source file once (video
    stream-copied) and reused it across cuts — cheap in time, but on a ~16GB
    4K source that's a ~16GB copy per unique clip, which blew through this
    Mac's free disk space mid-build (multiple ~16GB clips do not fit in ~14GB
    free). A cut only ever uses a couple of seconds, so extracting just that
    audio window (-vn, no video at all) is both disk-safe and simpler: output
    is a few hundred KB regardless of source file size.
    """
    import subprocess

    cache_dir.mkdir(parents=True, exist_ok=True)
    dur = out_s - in_s
    if dur <= 0:
        return None
    tag = f"duck{duck_db:g}".replace(".", "p").replace("-", "m")
    out_path = cache_dir / f"{src.stem}_{in_s:.2f}_{out_s:.2f}_{tag}.m4a"
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{in_s:.3f}", "-i", str(src), "-t", f"{dur:.3f}",
        "-vn", "-af", f"volume={duck_db}dB",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Duck extraction timed out for {src.name} [{in_s:.2f}-{out_s:.2f}s]")
        return None
    if result.returncode != 0 or not out_path.exists():
        print(f"   ⚠️  Duck extraction failed for {src.name} [{in_s:.2f}-{out_s:.2f}s]: {(result.stderr or '')[-200:]}")
        return None
    return out_path


def place_music(project, music_cfg: dict, total_duration_s: float, fps: float, tmp_root: Path) -> None:
    """Import the music bed and place it on its own audio track, trimmed to the
    reel's total duration and starting at the timeline's first frame.

    Uses a fresh audio track (AddTrack) rather than reusing A1 (which carries
    the onboard ride audio linked to the V1 cuts) so the two stay on
    independent faders — matches the README's documented AppendToTimeline
    clipInfo dict (mediaType=2 for audio-only placement, README line ~221).
    """
    music_path = Path(music_cfg["path"]).expanduser()
    if not music_path.exists():
        print(f"   ⚠️  Music file not found: {music_path} — skipping music track")
        return

    mp = project.GetMediaPool()
    timeline = project.GetCurrentTimeline()

    track_index = music_cfg.get("audio_track_index") or (timeline.GetTrackCount("audio") + 1)
    while timeline.GetTrackCount("audio") < track_index:
        if not timeline.AddTrack("audio", "stereo"):
            print("   ⚠️  Failed to add audio track for music — skipping music")
            return

    items = _import_via_tmp(mp, music_path, tmp_root)
    if not items:
        print(f"   ⚠️  Failed to import music: {music_path}")
        return

    offset = float(music_cfg.get("offset", 0.0))
    timeline_start = timeline.GetStartFrame()
    try:
        append_audio_with_in_out(
            project, items[0],
            media_in_seconds=offset,
            media_out_seconds=offset + total_duration_s,
            track_index=track_index,
            fps=fps,
            timeline_start_frame=timeline_start,
        )
    except ResolveError as e:
        print(f"   ⚠️  Could not place music: {e}")
        return

    print(f"   🎵 Music '{music_path.name}' placed on A{track_index} "
          f"({offset:.1f}s-{offset + total_duration_s:.1f}s)")


def _png_to_animated_mov(
    png_path: Path,
    mov_path: Path,
    duration_s: float,
    fps: float,
    style: str = "pop",
    fade_frames: int = 3,
) -> bool:
    """Render PNG into a ProRes 4444 MOV with alpha + entry/exit animation.

    Styles:
      - "pop":      scale 0.78 → 1.0 ease-out in first 180ms, hold, scale 1.0 → 1.06 fade exit
      - "slide_up": Y +90px → 0 in first 200ms, hold, slight Y -20px on exit
      - "punch":    scale 1.12 → 0.96 → 1.0 in first 160ms (impact), held, fade exit
      - "zoom_in":  slow 0.94 → 1.0 over full duration (Ken-Burns-ish)
      - "shake":    pop entry + 5-frame horizontal jitter on the first 200ms

    Uses overlay-on-transparent-canvas for safe scale + position animation
    while preserving alpha. Resolve respects yuva444p10le natively.
    """
    import subprocess
    # Cache invalidated by style suffix in filename — but also re-render if PNG newer
    if (
        mov_path.exists()
        and png_path.exists()
        and mov_path.stat().st_mtime >= png_path.stat().st_mtime
        and mov_path.stat().st_size > 0
    ):
        return True

    total_frames = max(1, int(round(duration_s * fps)))
    fi = max(1, min(fade_frames, total_frames // 5 or 1))
    fo_start_s = max(0.0, duration_s - fi / fps)
    enter_s = min(0.20, duration_s * 0.4)  # animation ramp duration

    # Scale + position expressions per style. All keep image within 1080x1920
    # (overlay clips, but we cap scale at 1.0 to avoid edge crop on grow).
    if style == "pop":
        scale_expr = (
            f"if(lt(t,{enter_s:.3f}),0.78+0.22*(1-pow(1-t/{enter_s:.3f},3)),"
            f"if(gt(t,{fo_start_s:.3f}),1.0+0.06*(t-{fo_start_s:.3f})/{(fi/fps):.3f},1.0))"
        )
        x_expr = "(W-w)/2"
        y_expr = "(H-h)/2"
    elif style == "slide_up":
        scale_expr = "1.0"
        x_expr = "(W-w)/2"
        y_expr = (
            f"(H-h)/2 + 90*(1-min(t/{enter_s:.3f}\\,1))"
            f" - if(gt(t,{fo_start_s:.3f})\\,20*(t-{fo_start_s:.3f})/{(fi/fps):.3f}\\,0)"
        )
    elif style == "punch":
        # Impact: starts large, scales down past target, settles
        scale_expr = (
            f"if(lt(t,0.06),1.12-0.16*(t/0.06),"
            f"if(lt(t,{enter_s:.3f}),0.96+0.04*((t-0.06)/({enter_s:.3f}-0.06)),1.0))"
        )
        x_expr = "(W-w)/2"
        y_expr = "(H-h)/2"
    elif style == "zoom_in":
        scale_expr = f"0.94+0.06*min(t/{duration_s:.3f}\\,1)"
        x_expr = "(W-w)/2"
        y_expr = "(H-h)/2"
    elif style == "shake":
        scale_expr = (
            f"if(lt(t,{enter_s:.3f}),0.82+0.18*(1-pow(1-t/{enter_s:.3f},3)),1.0)"
        )
        # Small horizontal jitter ~14px during entry
        x_expr = (
            f"(W-w)/2 + if(lt(t,0.18)\\,14*sin(t*80)\\,0)"
        )
        y_expr = "(H-h)/2"
    else:
        scale_expr = "1.0"
        x_expr = "(W-w)/2"
        y_expr = "(H-h)/2"

    # Build filter_complex:
    #   transparent canvas <- overlay(scaled foreground)
    #   then alpha fade in/out
    filter_complex = (
        f"color=size=1080x1920:c=0x00000000@0.0:d={duration_s:.3f}:r={fps}[bg];"
        f"[0:v]format=rgba,scale=w='trunc(iw*({scale_expr})/2)*2':h='trunc(ih*({scale_expr})/2)*2':eval=frame[fg];"
        f"[bg][fg]overlay=x='{x_expr}':y='{y_expr}':eval=frame:shortest=1:format=auto,"
        f"format=yuva444p10le,"
        f"fade=t=in:st=0:d={fi/fps:.3f}:alpha=1,"
        f"fade=t=out:st={fo_start_s:.3f}:d={fi/fps:.3f}:alpha=1"
    )

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", f"{fps}",
        "-t", f"{duration_s:.3f}",
        "-i", str(png_path),
        "-filter_complex", filter_complex,
        "-c:v", "prores_ks", "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le",
        str(mov_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if result.returncode != 0:
            # Surface ffmpeg error on first failure for debugging
            err = (result.stderr or "")[-400:]
            print(f"   ⚠️  ffmpeg failed for {mov_path.name} ({style}): {err}")
            return False
        return mov_path.exists() and mov_path.stat().st_size > 0
    except Exception as e:
        print(f"   ⚠️  ffmpeg exception for {mov_path.name}: {e}")
        return False


# Caption animation rotation — cycles through styles for variety
_CAPTION_STYLES = ["pop", "slide_up", "pop", "punch", "zoom_in", "pop", "shake", "slide_up"]
# V1 zoom-pulse rotation — varies static framing per cut for visual rhythm
_V1_ZOOMS = [1.00, 1.06, 1.10, 1.02, 1.08, 1.00, 1.12, 1.04]
# Subtle horizontal pan offset (in pixels at timeline scale) per cut
_V1_PAN_X = [0, -40, 30, 0, -20, 50, -30, 20]


def _render_caption_png(text: str, png_path: Path, font_paths: dict) -> None:
    """Render a kinetic-typography caption PNG (1080x1920 transparent).

    Words are classified into keyword/emphasis/normal and rendered with
    different sizes/colors. Bottom-third position. White stroke, black shadow.
    """
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    KEYWORD_COLOR = (184, 115, 51, 255)   # cobre #B87333
    EMPHASIS_COLOR = (245, 200, 60, 255)  # amarelo cobre claro
    NORMAL_COLOR = (255, 255, 255, 255)
    STROKE_COLOR = (10, 26, 15, 255)

    SIZES = {"keyword": 220, "emphasis": 170, "normal": 130}
    STROKES = {"keyword": 14, "emphasis": 12, "normal": 10}

    words = text.split()
    if not words:
        return

    # Classify and load fonts
    tokens = []
    for w in words:
        cls = _classify_word(w)
        size = SIZES[cls]
        try:
            font = ImageFont.truetype(font_paths[cls], size)
        except Exception:
            font = ImageFont.load_default()
        color = {"keyword": KEYWORD_COLOR, "emphasis": EMPHASIS_COLOR, "normal": NORMAL_COLOR}[cls]
        stroke = STROKES[cls]
        tokens.append({"word": w, "font": font, "color": color, "stroke": stroke, "cls": cls})

    # Layout: stack words vertically if more than 1, else single line
    # Use a bottom-third baseline (~y=1300)
    SPACE = 28
    LINE_H_PAD = 30
    line_heights = []
    line_widths = []
    for tok in tokens:
        bbox = draw.textbbox((0, 0), tok["word"], font=tok["font"], stroke_width=tok["stroke"])
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    total_h = sum(line_heights) + LINE_H_PAD * (len(tokens) - 1)
    y = 1300 - total_h // 2

    for i, tok in enumerate(tokens):
        bbox = draw.textbbox((0, 0), tok["word"], font=tok["font"], stroke_width=tok["stroke"])
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        # Slight random horizontal jitter for "viral" feel — disabled here for stability
        draw.text((x, y - bbox[1]), tok["word"], font=tok["font"], fill=tok["color"],
                  stroke_width=tok["stroke"], stroke_fill=STROKE_COLOR)
        y += line_heights[i] + LINE_H_PAD

    img.save(png_path)


def _resolve_fonts() -> dict:
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    candidates_med = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Avenir Next.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    bold = next((p for p in candidates_bold if Path(p).exists()), None)
    med = next((p for p in candidates_med if Path(p).exists()), bold)
    return {"keyword": bold, "emphasis": bold, "normal": med}


def add_kinetic_captions(project, captions: list[dict], png_dir: Path, track_index: int = 2) -> int:
    """Generate one styled PNG per caption and place sequentially on V<track_index>.

    Each caption: {text, start, end} timeline seconds. Renders kinetic typography
    (keywords big copper, emphasis yellow, normal white) — Submagic/viral style.
    """
    if not captions:
        return 0
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    except ImportError:
        print("   ⚠️  PIL not available — skipping kinetic captions")
        return 0

    timeline = project.GetCurrentTimeline()
    fps = float(timeline.GetSetting("timelineFrameRate") or 24)
    timeline_start = timeline.GetStartFrame()  # Resolve timelines start at 1h offset by default
    mp = project.GetMediaPool()

    while timeline.GetTrackCount("video") < track_index:
        timeline.AddTrack("video")

    png_dir.mkdir(parents=True, exist_ok=True)
    tmp_root = Path("/tmp") / "video_editor_davinci_imports"
    fonts = _resolve_fonts()

    placed = 0
    for i, cap in enumerate(captions):
        text = cap["text"]
        start = float(cap["start"])
        end = float(cap["end"])
        duration_frames = max(1, int(round((end - start) * fps)))
        if duration_frames < 1:
            continue

        slug = re.sub(r'[^A-Z0-9]', '_', text.upper())[:20]
        png_name = f"cap_{i+1:03d}_{slug}.png"
        png_path = png_dir / png_name
        _render_caption_png(text, png_path, fonts)

        # Cycle animation styles for variety; cap shorter durations to safer styles
        cap_dur = end - start
        if cap_dur < 0.35:
            style = "pop"  # short captions need fast entry
        else:
            style = _CAPTION_STYLES[i % len(_CAPTION_STYLES)]

        mov_path = png_dir / f"cap_{i+1:03d}_{slug}__{style}.mov"
        if not _png_to_animated_mov(png_path, mov_path, cap_dur, fps, style=style, fade_frames=3):
            # Fallback: import the static PNG
            mov_path = png_path

        items = _import_via_tmp(mp, mov_path, tmp_root)
        if not items:
            continue

        start_frame = timeline_start + int(round(start * fps))
        payload = {
            "mediaPoolItem": items[0],
            "trackIndex": track_index,
            "recordFrame": start_frame,
            "startFrame": 0,
            "endFrame": duration_frames,
        }
        if mp.AppendToTimeline([payload]):
            placed += 1

    print(f"   ✅ {placed}/{len(captions)} kinetic captions placed on V{track_index} (animated MOV: pop/slide/punch/zoom/shake)")
    return placed


def add_stat_overlays(project, overlays: list[dict], png_dir: Path, track_index: int = 3) -> int:
    """Big stat overlays (37%, 20%, SELIC, +60%) on V<track_index>. Centered, longer-held.

    Each overlay dict: {text, subtext, start, end} timeline seconds.
    """
    if not overlays:
        return 0
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("   ⚠️  PIL not available — skipping stat overlays")
        return 0

    timeline = project.GetCurrentTimeline()
    fps = float(timeline.GetSetting("timelineFrameRate") or 24)
    timeline_start = timeline.GetStartFrame()  # Resolve timelines start at 1h offset by default
    mp = project.GetMediaPool()

    while timeline.GetTrackCount("video") < track_index:
        timeline.AddTrack("video")

    png_dir.mkdir(parents=True, exist_ok=True)
    tmp_root = Path("/tmp") / "video_editor_davinci_imports"
    fonts = _resolve_fonts()
    placed = 0

    for i, ov in enumerate(overlays):
        text = ov["text"]
        subtext = ov.get("subtext", "")
        start = float(ov["start"])
        end = float(ov["end"])
        duration_frames = max(1, int(round((end - start) * fps)))
        if duration_frames < 1:
            continue

        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        big_size = 360 if len(text) <= 4 else 280
        sub_size = 70
        try:
            big_font = ImageFont.truetype(fonts["keyword"], big_size)
            sub_font = ImageFont.truetype(fonts["normal"], sub_size)
        except Exception:
            big_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=big_font, stroke_width=18)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (1080 - tw) // 2 - bbox[0]
        y = 540
        draw.text((x, y - bbox[1]), text, font=big_font, fill=(184, 115, 51, 255),
                  stroke_width=18, stroke_fill=(10, 26, 15, 255))
        if subtext:
            sub_upper = subtext.upper()
            sb = draw.textbbox((0, 0), sub_upper, font=sub_font, stroke_width=6)
            sw = sb[2] - sb[0]
            sx = (1080 - sw) // 2 - sb[0]
            sy = y + th + 80
            draw.text((sx, sy - sb[1]), sub_upper, font=sub_font, fill=(245, 241, 232, 255),
                      stroke_width=6, stroke_fill=(10, 26, 15, 255))

        slug = text.replace('%','pct').replace('+','plus')
        png_path = png_dir / f"stat_{i+1:02d}_{slug}.png"
        img.save(png_path)

        # Stats hit hard with "punch" entry, then settle and hold
        mov_path = png_dir / f"stat_{i+1:02d}_{slug}__punch.mov"
        if not _png_to_animated_mov(png_path, mov_path, end - start, fps, style="punch", fade_frames=6):
            mov_path = png_path

        items = _import_via_tmp(mp, mov_path, tmp_root)
        if not items:
            continue

        start_frame = timeline_start + int(round(start * fps))
        payload = {
            "mediaPoolItem": items[0],
            "trackIndex": track_index,
            "recordFrame": start_frame,
            "startFrame": 0,
            "endFrame": duration_frames,
        }
        if mp.AppendToTimeline([payload]):
            placed += 1
            print(f"   🪧 Stat '{text}' on V{track_index} @ {start:.1f}-{end:.1f}s")
    return placed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--clips-dir", required=True, type=Path)
    ap.add_argument("--brand-config", type=Path,
                    help="Path to .video-editor.json (for resolve_project_folder)")
    ap.add_argument("--project-name", help="Override the project name from the plan")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    clips_dir = args.clips_dir.expanduser().resolve()
    if not clips_dir.is_dir():
        sys.exit(f"❌ Clips dir not found: {clips_dir}")

    brand_config = json.loads(args.brand_config.read_text()) if args.brand_config else {}
    project_folder = brand_config.get("resolve_project_folder")
    project_name = args.project_name or plan["name"]

    # Montage pre-render pass (mutates plan["v1_main"] in place, before we
    # resolve/import anything) — see prerender_speed_clips docstring for why
    # this can't just be a scripting API call. Audio ducking happens later,
    # per-cut, inside the V1 loop (see duck_audio_segment) — it needs each
    # cut's actual placed timeline position, and must NOT touch whole source
    # files (some of these clips are 16GB+; ducking used to stream-copy the
    # whole file per unique clip, which can exceed free disk space).
    prerender_cache = args.plan.parent / "prerender_cache"
    if any(float(c.get("speed", 1.0)) != 1.0 for c in plan["v1_main"]):
        prerender_speed_clips(plan, clips_dir, prerender_cache / "speed")
    music_cfg = plan.get("music")

    # Resolve all clip paths up front (fail fast if missing)
    referenced_clips: list[str] = sorted({entry["clip"] for entry in plan["v1_main"]})
    clip_paths: list[Path] = []
    for name in referenced_clips:
        p = clips_dir / name
        if not p.exists():
            sys.exit(f"❌ Clip not found: {p}")
        clip_paths.append(p.resolve())

    print(f"🎬 Building '{project_name}' from {len(plan['v1_main'])} cuts + {len(plan['subtitle_track'])} captions")

    try:
        resolve = connect()
    except ResolveError as e:
        sys.exit(f"❌ {e}")

    print(f"   Resolve {resolve.GetVersionString()} OK")

    project = get_or_create_project(resolve, project_name, folder=project_folder)
    fps = int(round(float(plan.get("fps", 30))))
    width, height = plan.get("resolution", [1080, 1920])
    configure_project(project, fps=fps, width=width, height=height)
    print(f"   Project '{project_name}' ready ({width}x{height} @ {fps}fps)")

    # Import clips
    items = import_clips(project, clip_paths)
    items_by_name = {item.GetName(): item for item in items}
    # MediaPool sometimes returns names without extension — try both
    for clip_path in clip_paths:
        items_by_name.setdefault(clip_path.name, None)
        items_by_name.setdefault(clip_path.stem, None)
    # Normalize: dropped Nones
    items_by_name = {k: v for k, v in items_by_name.items() if v is not None}
    print(f"   Imported {len(items)} clip(s) to MediaPool")

    # Create timeline
    timeline_name = f"{project_name}_timeline"
    timeline = create_empty_timeline(project, timeline_name)
    print(f"   Timeline '{timeline_name}' created")

    # Color correction defaults (override per-clip via plan["color_correction"]["global_cdl"])
    cdl_cfg = (plan.get("color_correction") or {}).get("global_cdl") or {}
    cdl_kwargs = {
        "saturation": float(cdl_cfg.get("saturation", 1.0)),
        "slope": tuple(cdl_cfg.get("slope", [1.0, 1.0, 1.0])),
        "offset": tuple(cdl_cfg.get("offset", [0.0, 0.0, 0.0])),
        "power": tuple(cdl_cfg.get("power", [1.0, 1.0, 1.0])),
    }
    apply_color = cdl_kwargs["saturation"] != 1.0 or cdl_kwargs["offset"] != (0.0, 0.0, 0.0)

    # Append V1 cuts
    for i, entry in enumerate(plan["v1_main"], start=1):
        clip_name = entry["clip"]
        # clip_name may be an absolute path (montage pre-render output) rather
        # than a plain filename — look up by basename first, since that's what
        # items_by_name / GetName() key on.
        item = (
            items_by_name.get(Path(clip_name).name)
            or items_by_name.get(clip_name)
            or items_by_name.get(Path(clip_name).stem)
        )
        if item is None:
            sys.exit(f"❌ Could not find imported clip for '{clip_name}'. Available: {list(items_by_name)}")

        # A cut still at speed==1.0 references the plain original source and
        # still carries its full-volume onboard audio; if a music bed is
        # configured, place that cut VIDEO-ONLY and duck+place its audio
        # separately below (a cut already re-pointed to a pre-rendered speed
        # file has no audio at all — nothing to duck).
        needs_duck = bool(music_cfg) and float(entry.get("speed", 1.0)) == 1.0
        try:
            tl_item = append_clip_with_in_out(
                project, item,
                media_in_seconds=entry["source_in"],
                media_out_seconds=entry["source_out"],
                track_index=1,
                media_type=1 if needs_duck else None,
            )
        except ResolveError as e:
            sys.exit(f"❌ Failed cut #{i} ({clip_name} {entry['source_in']:.2f}-{entry['source_out']:.2f}): {e}")

        if needs_duck:
            duck_db = float(music_cfg.get("onboard_audio_duck_db", -20.0))
            src = clips_dir / clip_name
            ducked = duck_audio_segment(src, entry["source_in"], entry["source_out"],
                                         prerender_cache / "duck", duck_db)
            if ducked:
                a_items = _import_via_tmp(project.GetMediaPool(), ducked, Path("/tmp") / "video_editor_davinci_imports")
                if a_items:
                    video_start_frame = int(tl_item.GetStart())
                    video_dur_frames = int(tl_item.GetDuration())
                    try:
                        append_audio_with_in_out(
                            project, a_items[0],
                            media_in_seconds=0.0,
                            media_out_seconds=video_dur_frames / fps,
                            track_index=1,
                            fps=fps,
                            timeline_start_frame=video_start_frame,
                        )
                    except ResolveError as e:
                        print(f"   ⚠️  Could not place ducked audio for cut #{i}: {e}")

        # Reframe horizontal source → vertical timeline (fill mode crops sides)
        scaling_ok = set_clip_scaling(tl_item, SCALE_FILL)
        # Apply color CDL if configured
        cdl_ok = apply_cdl(tl_item, **cdl_kwargs) if apply_color else True

        # Framing: montage plans can specify explicit per-cut framing (the crop
        # offset within the 4:3→9:16 fill); fall back to the cyclic zoom/pan
        # rotation for plans that don't (speech-driven Reel pipeline default).
        framing = entry.get("framing") or {}
        zoom = float(framing.get("zoom", _V1_ZOOMS[(i - 1) % len(_V1_ZOOMS)]))
        pan_x = float(framing.get("pan_x", _V1_PAN_X[(i - 1) % len(_V1_PAN_X)]))
        zoom_ok = bool(tl_item.SetProperty("ZoomX", zoom)) and bool(tl_item.SetProperty("ZoomY", zoom))
        pan_ok = bool(tl_item.SetProperty("Pan", float(pan_x))) if pan_x else True

        flags = []
        if scaling_ok: flags.append("fill")
        if apply_color and cdl_ok: flags.append(f"cdl(sat={cdl_kwargs['saturation']:.2f})")
        if zoom_ok: flags.append(f"zoom={zoom:.2f}")
        if pan_x and pan_ok: flags.append(f"pan={pan_x:+.0f}")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"   ▶ V1 cut {i}/{len(plan['v1_main'])}: {clip_name} "
              f"[{entry['source_in']:.2f}-{entry['source_out']:.2f}s]{flag_str}")

    # Music bed on its own audio track (montage plans only — see plan["music"])
    if music_cfg:
        total_duration_s = sum(e["source_out"] - e["source_in"] for e in plan["v1_main"])
        tmp_root = Path("/tmp") / "video_editor_davinci_imports"
        place_music(project, music_cfg, total_duration_s, fps, tmp_root)

    # Beat markers on the timeline ruler (montage plans only) — makes it a
    # 2-click job to nudge cuts or add more speed ramps by hand in Resolve.
    beats = plan.get("beats") or []
    if beats:
        timeline = project.GetCurrentTimeline()
        timeline_start = timeline.GetStartFrame()
        placed_markers = 0
        for b in beats:
            frame_id = timeline_start + int(round(float(b) * fps))
            if timeline.AddMarker(frame_id, "Blue", "beat", "", 1):
                placed_markers += 1
        print(f"   📍 {placed_markers}/{len(beats)} beat marker(s) added to timeline ruler")

    # Kinetic captions on V2 (one styled PNG per caption — Submagic/viral style)
    subs = plan.get("subtitle_track") or []
    if subs:
        cap_dir = args.plan.parent / "captions_png"
        # Also write SRT for backup
        srt_path = args.plan.parent / f"{project_name}_captions.srt"
        write_srt(subs, srt_path)
        add_kinetic_captions(project, subs, cap_dir, track_index=2)

    # Stat overlays on V3 (big standalone keyword cards)
    overlays = plan.get("overlays_v2") or []
    if overlays:
        ov_dir = args.plan.parent / "stat_overlays"
        add_stat_overlays(project, overlays, ov_dir, track_index=3)

    # Save
    pm = resolve.GetProjectManager()
    if pm.SaveProject():
        print(f"\n✅ Project saved. Open DaVinci Resolve → '{project_name}' in Project Manager.")
    else:
        print("\n⚠️  SaveProject returned False — try Cmd+S manually in Resolve.")


if __name__ == "__main__":
    main()

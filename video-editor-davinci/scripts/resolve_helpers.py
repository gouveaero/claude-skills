"""
resolve_helpers.py — thin, ergonomic wrappers around the raw DaVinciResolveScript module.

Why not pydavinci? Not on PyPI, incomplete coverage, breaks across Resolve versions.
We use the official `DaVinciResolveScript` module that ships with Resolve Studio.

This module is import-safe (no Resolve connection happens until you call connect()).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any


def _values(maybe_dict_or_list) -> list:
    """Resolve API often returns dicts {1: name, 2: name} or lists [name, name].
    Normalize to a list of names."""
    if maybe_dict_or_list is None:
        return []
    if isinstance(maybe_dict_or_list, dict):
        return list(maybe_dict_or_list.values())
    return list(maybe_dict_or_list)


class ResolveError(RuntimeError):
    """Raised when something goes wrong driving Resolve."""


def connect(retries: int = 3, delay: float = 1.0):
    """Returns the live Resolve object, retrying briefly to handle app startup races."""
    try:
        import DaVinciResolveScript as bmd  # type: ignore
    except ImportError as e:
        raise ResolveError(
            "Cannot import DaVinciResolveScript. Did you `source ~/.zshrc` "
            "after env vars were added? See references/setup.md."
        ) from e

    last_err = None
    for _ in range(retries):
        resolve = bmd.scriptapp("Resolve")
        if resolve is not None:
            return resolve
        time.sleep(delay)
        last_err = "scriptapp returned None"
    raise ResolveError(
        f"Could not connect to Resolve ({last_err}). Is the app running and "
        "External Scripting set to 'Local' in Preferences → System → General?"
    )


def get_or_create_project(resolve, name: str, folder: str | None = None):
    """Open project `name` (creating it if needed). Optionally inside subfolder.

    Note: Resolve's PM API returns dicts ({1: 'A', 2: 'B'}) for folder/project lists,
    not plain lists — `_values()` normalizes that.
    """
    pm = resolve.GetProjectManager()
    if pm is None:
        raise ResolveError("ProjectManager unavailable")

    # Check the CURRENT project by name before anything else. A project a
    # prior run created but crashed before SaveProject() stays open as the
    # "current project" without ever appearing in GetProjectListInCurrentFolder()
    # — and Resolve then refuses CreateProject/LoadProject for ANYTHING while
    # that unsaved project is current (both return None, indistinguishable from
    # a real failure unless you check this first).
    current = pm.GetCurrentProject()
    if current and current.GetName() == name:
        return current

    # Always anchor to root first — Project Manager navigation is stateful in
    # the live app (e.g. the user browsing folders between script runs), so
    # without this, GetProjectListInCurrentFolder()/CreateProject() below would
    # silently operate on whatever folder the UI happens to be sitting in.
    pm.GotoRootFolder()
    if folder:
        existing_folders = _values(pm.GetFoldersInCurrentFolder())
        if folder not in existing_folders:
            if not pm.CreateFolder(folder):
                raise ResolveError(f"Failed to create folder '{folder}'")
        if not pm.OpenFolder(folder):
            raise ResolveError(f"Failed to open folder '{folder}'")

    existing = _values(pm.GetProjectListInCurrentFolder())
    if name in existing:
        project = pm.LoadProject(name)
        if project is None:
            raise ResolveError(f"Found project '{name}' but failed to load")
        return project

    project = pm.CreateProject(name)
    if project is None:
        raise ResolveError(
            f"Failed to create project '{name}' — if another unsaved project is "
            "currently open in Resolve, save or close it first"
        )
    # Brief pause: MediaPool needs a moment after a new project is created
    time.sleep(0.5)
    return project


def configure_project(project, *, fps: int = 30, width: int = 1080, height: int = 1920):
    """Set timeline format settings on a project."""
    settings = {
        "timelineFrameRate": str(fps),
        "timelineResolutionWidth": str(width),
        "timelineResolutionHeight": str(height),
    }
    for k, v in settings.items():
        if not project.SetSetting(k, v):
            # Not all settings are settable post-creation; ignore silently
            pass


def import_clips(project, clip_paths: list[str | Path], retries: int = 3) -> list:
    """Import clips into the root MediaPool bin.

    Tries batch import first (fastest), then falls back to one-at-a-time on
    failure. Each individual import retries briefly to absorb the brief
    not-ready window right after CreateProject.
    """
    mp = project.GetMediaPool()
    if mp is None:
        raise ResolveError("MediaPool unavailable")

    paths = [str(p) for p in clip_paths]

    # Try batch first
    items = mp.ImportMedia(paths)
    if items and len(items) == len(paths):
        return list(items)

    # Fall back: import one at a time with retry
    accumulated: list = []
    failed: list[str] = []
    for p in paths:
        item = None
        for attempt in range(retries):
            r = mp.ImportMedia([p])
            if r and len(r) >= 1:
                item = r[0]
                break
            time.sleep(0.5 * (attempt + 1))
        if item is None:
            failed.append(p)
        else:
            accumulated.append(item)

    if failed:
        raise ResolveError(
            f"Failed to import {len(failed)} clip(s) after {retries} retries each: {failed}"
        )
    return accumulated


def create_empty_timeline(project, name: str):
    """Create a timeline with the given name, return the Timeline object."""
    mp = project.GetMediaPool()
    timeline = mp.CreateEmptyTimeline(name)
    if timeline is None:
        raise ResolveError(f"Failed to create timeline '{name}'")
    return timeline


def append_clips_to_timeline(project, items: list, *, frame_rate: float = 30.0):
    """Append MediaPoolItems sequentially to V1 of the current timeline."""
    mp = project.GetMediaPool()
    if not mp.AppendToTimeline(items):
        raise ResolveError("AppendToTimeline failed")


def append_clip_with_in_out(
    project,
    media_pool_item,
    *,
    media_in_seconds: float,
    media_out_seconds: float,
    track_index: int = 1,
    timeline_start_frame: int | None = None,
    media_type: int | None = None,
):
    """Append a single clip with explicit in/out (in source seconds) to a track.

    Resolve's AppendToTimeline accepts a list of dicts with frame-based in/out:
      {"mediaPoolItem": item, "startFrame": N, "endFrame": M, "trackIndex": k, ...}

    `media_type`: optional 1 (video only) / 2 (audio only), per the README's
    documented clipInfo dict. Pass 1 when you intend to place a SEPARATE,
    independently-processed audio clip for this same source/range (e.g. a
    ducked segment) instead of Resolve's default auto-linked embedded audio.

    Returns the appended TimelineItem (last item on the target track).
    """
    fps = float(media_pool_item.GetClipProperty("FPS") or 30.0)
    start_frame = int(round(media_in_seconds * fps))
    end_frame = int(round(media_out_seconds * fps))

    payload: dict[str, Any] = {
        "mediaPoolItem": media_pool_item,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "trackIndex": track_index,
    }
    if timeline_start_frame is not None:
        payload["recordFrame"] = timeline_start_frame
    if media_type is not None:
        payload["mediaType"] = media_type

    mp = project.GetMediaPool()
    if not mp.AppendToTimeline([payload]):
        raise ResolveError(
            f"AppendToTimeline failed for {media_pool_item.GetName()} "
            f"({media_in_seconds:.2f}s → {media_out_seconds:.2f}s)"
        )

    timeline = project.GetCurrentTimeline()
    items = timeline.GetItemListInTrack("video", track_index) or []
    return items[-1] if items else None


def append_audio_with_in_out(
    project,
    media_pool_item,
    *,
    media_in_seconds: float,
    media_out_seconds: float,
    track_index: int,
    fps: float,
    timeline_start_frame: int | None = None,
):
    """Sibling of append_clip_with_in_out for an AUDIO-ONLY clip (e.g. a music
    bed): sets mediaType=2 so AppendToTimeline places only the audio stream.

    Unlike append_clip_with_in_out, `fps` is taken explicitly (the TIMELINE's
    frame rate) rather than read from MediaPoolItem.GetClipProperty("FPS") —
    audio-only files (mp3/wav) don't reliably carry a meaningful FPS clip
    property, and getting this wrong would silently mis-time the whole music bed.
    """
    start_frame = int(round(media_in_seconds * fps))
    end_frame = int(round(media_out_seconds * fps))

    payload: dict[str, Any] = {
        "mediaPoolItem": media_pool_item,
        "startFrame": start_frame,
        "endFrame": end_frame,
        "trackIndex": track_index,
        "mediaType": 2,
    }
    if timeline_start_frame is not None:
        payload["recordFrame"] = timeline_start_frame

    mp = project.GetMediaPool()
    if not mp.AppendToTimeline([payload]):
        raise ResolveError(
            f"AppendToTimeline (audio) failed for {media_pool_item.GetName()} "
            f"({media_in_seconds:.2f}s → {media_out_seconds:.2f}s)"
        )

    timeline = project.GetCurrentTimeline()
    items = timeline.GetItemListInTrack("audio", track_index) or []
    return items[-1] if items else None


# Scaling constants (per Resolve scripting README)
SCALE_USE_PROJECT = 0
SCALE_CROP = 1
SCALE_FIT = 2
SCALE_FILL = 3
SCALE_STRETCH = 4


def set_clip_scaling(timeline_item, mode: int = SCALE_FILL) -> bool:
    """Set the per-clip mismatched-resolution scaling mode."""
    if timeline_item is None:
        return False
    return bool(timeline_item.SetProperty("Scaling", mode))


def apply_cdl(
    timeline_item,
    *,
    saturation: float = 1.0,
    slope: tuple[float, float, float] = (1.0, 1.0, 1.0),
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    power: tuple[float, float, float] = (1.0, 1.0, 1.0),
    node_index: int = 1,
) -> bool:
    """Apply ASC CDL primary color correction to node 1 of the clip."""
    if timeline_item is None:
        return False
    cdl = {
        "NodeIndex": str(node_index),
        "Slope": " ".join(f"{v:.4f}" for v in slope),
        "Offset": " ".join(f"{v:.4f}" for v in offset),
        "Power": " ".join(f"{v:.4f}" for v in power),
        "Saturation": f"{saturation:.4f}",
    }
    return bool(timeline_item.SetCDL(cdl))


def save_project(project) -> bool:
    """Save the current project."""
    return bool(project.GetProjectManager() and project.SaveProject())  # noqa


def delete_project(resolve, name: str, folder: str | None = None) -> bool:
    """Delete a project by name (use carefully — for tests/cleanup)."""
    pm = resolve.GetProjectManager()
    if folder:
        pm.GotoRootFolder()
        if not pm.OpenFolder(folder):
            return False
    return bool(pm.DeleteProject(name))


def smoke_test():
    """End-to-end sanity: connect, create test project, save, delete. CLI: --smoke"""
    resolve = connect()
    print(f"  Connected to Resolve v{resolve.GetVersionString()}")
    project = get_or_create_project(resolve, "_video_editor_smoke", folder="_skill_tests")
    configure_project(project, fps=30, width=1080, height=1920)
    timeline = create_empty_timeline(project, "smoke_timeline")
    print(f"  Created project + timeline '{timeline.GetName()}'")
    pm = resolve.GetProjectManager()
    pm.SaveProject()
    pm.CloseProject(project)
    deleted = delete_project(resolve, "_video_editor_smoke", folder="_skill_tests")
    print(f"  Cleanup: deleted={deleted}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        try:
            smoke_test()
            print("✅ Smoke test passed")
        except ResolveError as e:
            print(f"❌ {e}")
            sys.exit(1)
    else:
        print("usage: python3 resolve_helpers.py --smoke")

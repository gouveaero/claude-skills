#!/usr/bin/env python3
"""
transcribe.py — word-level transcription of video/audio clips via mlx-whisper.

Usage:
    python3 transcribe.py --input <clips_dir> [--output <transcripts.json>]
                          [--model mlx-community/whisper-large-v3-mlx]
                          [--language pt]

Output JSON shape:
{
  "model": "...",
  "language": "...",
  "clips": {
    "01_intro.mp4": {
      "duration": 12.34,
      "text": "full transcription",
      "segments": [
        {"start": 0.0, "end": 3.21, "text": "..."},
        ...
      ],
      "words": [
        {"word": "isenção", "start": 1.2, "end": 1.7, "probability": 0.98},
        ...
      ]
    }
  }
}

Cache: results are stored in <input_dir>/.video-editor/cache/transcripts/<clip>.json
       and reused unless --force is passed.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
SUPPORTED = VIDEO_EXTS | AUDIO_EXTS


def discover_clips(input_dir: Path) -> list[Path]:
    clips = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith(".")
    )
    return clips


def probe_duration(path: Path) -> float:
    """Use ffprobe to get duration in seconds."""
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True
    )
    return float(out.strip())


def extract_audio(video_path: Path, work_dir: Path) -> Path:
    """Extract audio to mono 16kHz WAV (whisper's preferred format)."""
    audio_path = work_dir / f"{video_path.stem}.wav"
    if audio_path.exists():
        return audio_path
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vn",
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
         str(audio_path)],
        check=True, capture_output=True,
    )
    return audio_path


def transcribe_one(audio_path: Path, model: str, language: str) -> dict:
    """Call mlx_whisper.transcribe with word_timestamps=True."""
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=model,
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    segments = []
    words = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "text": seg["text"].strip(),
        })
        for w in seg.get("words", []) or []:
            words.append({
                "word": w["word"].strip(),
                "start": round(w["start"], 3),
                "end": round(w["end"], 3),
                "probability": round(w.get("probability", 0.0), 4),
            })

    return {
        "text": result.get("text", "").strip(),
        "language": result.get("language", language),
        "segments": segments,
        "words": words,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path, help="Directory with clips")
    ap.add_argument("--output", type=Path, help="Output JSON path (default: <input>/transcripts.json)")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-mlx",
                    help="MLX whisper model HF repo")
    ap.add_argument("--language", default="pt", help="Language code (pt, en, es, ...)")
    ap.add_argument("--force", action="store_true", help="Ignore cache and re-transcribe everything")
    args = ap.parse_args()

    input_dir: Path = args.input.expanduser().resolve()
    if not input_dir.is_dir():
        sys.exit(f"❌ Input not a directory: {input_dir}")

    output_path: Path = args.output or (input_dir / "transcripts.json")
    cache_dir = input_dir / ".video-editor" / "cache" / "transcripts"
    cache_dir.mkdir(parents=True, exist_ok=True)
    work_dir = input_dir / ".video-editor" / "cache" / "audio"
    work_dir.mkdir(parents=True, exist_ok=True)

    clips = discover_clips(input_dir)
    if not clips:
        sys.exit(f"❌ No supported media files found in {input_dir}")

    print(f"📂 {len(clips)} clip(s) to process in {input_dir}")
    print(f"🤖 Model: {args.model}  |  Language: {args.language}")

    out_clips: dict[str, dict] = {}
    for clip in clips:
        cache_file = cache_dir / f"{clip.name}.json"
        if cache_file.exists() and not args.force:
            print(f"  ✓ {clip.name} (cached)")
            out_clips[clip.name] = json.loads(cache_file.read_text())
            continue

        print(f"  ⏳ {clip.name} ...", end=" ", flush=True)
        duration = probe_duration(clip)
        if clip.suffix.lower() in VIDEO_EXTS:
            audio_path = extract_audio(clip, work_dir)
        else:
            audio_path = clip

        try:
            result = transcribe_one(audio_path, args.model, args.language)
        except Exception as e:
            print(f"FAILED: {e}")
            continue

        result["duration"] = duration
        cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        out_clips[clip.name] = result
        print(f"OK ({duration:.1f}s, {len(result['words'])} words)")

    output = {
        "model": args.model,
        "language": args.language,
        "clips": out_clips,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n✅ Wrote {output_path}")


if __name__ == "__main__":
    main()

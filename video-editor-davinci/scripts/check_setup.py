#!/usr/bin/env python3
"""
check_setup.py — validates the local environment for video-editor-davinci skill.

Run this BEFORE attempting any other operation. If any check fails, follow the
guidance in references/setup.md and re-run.

Exit code 0 on full success, non-zero on any failure.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

OK = "\033[92m✅"
FAIL = "\033[91m❌"
WARN = "\033[93m⚠️"
RESET = "\033[0m"

results: list[tuple[bool, str]] = []


def check(label: str, fn) -> bool:
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"exception: {e}"
    icon = OK if ok else FAIL
    print(f"{icon} {label}: {detail}{RESET}")
    results.append((ok, label))
    return ok


def check_env_vars():
    api = os.environ.get("RESOLVE_SCRIPT_API")
    lib = os.environ.get("RESOLVE_SCRIPT_LIB")
    pp = os.environ.get("PYTHONPATH", "")
    if not api:
        return False, "RESOLVE_SCRIPT_API not set (see references/setup.md §3)"
    if not lib:
        return False, "RESOLVE_SCRIPT_LIB not set"
    modules_path = f"{api}/Modules"
    if modules_path not in pp:
        return False, f"PYTHONPATH missing {modules_path}"
    if not Path(api).exists():
        return False, f"RESOLVE_SCRIPT_API path does not exist: {api}"
    if not Path(lib).exists():
        return False, f"RESOLVE_SCRIPT_LIB path does not exist: {lib}"
    return True, "all set"


def check_resolve_script_module():
    try:
        # noqa: F401 — just probing import
        import DaVinciResolveScript  # type: ignore
        return True, "DaVinciResolveScript importable"
    except ImportError as e:
        return False, f"cannot import DaVinciResolveScript: {e}"


def check_resolve_connection():
    try:
        import DaVinciResolveScript as bmd  # type: ignore
    except ImportError:
        return False, "DaVinciResolveScript not importable (check env vars)"
    resolve = bmd.scriptapp("Resolve")
    if resolve is None:
        return False, "Resolve not running OR external scripting not 'Local' (Preferences → System → General)"
    version = resolve.GetVersionString() if hasattr(resolve, "GetVersionString") else "?"
    pm = resolve.GetProjectManager()
    if pm is None:
        return False, f"connected to v{version} but ProjectManager unavailable"
    project_count = len(pm.GetProjectListInCurrentFolder() or [])
    return True, f"v{version} connected, {project_count} projects in current folder"


def check_studio_vs_free():
    """Studio exposes more API surface — heuristic: check if Fusion scripting is available."""
    try:
        import DaVinciResolveScript as bmd  # type: ignore
        resolve = bmd.scriptapp("Resolve")
        if resolve is None:
            return False, "cannot detect (Resolve not running)"
        fusion = resolve.Fusion()
        if fusion is None:
            return False, "Fusion scripting not exposed — likely free version"
        return True, "Fusion scripting exposed (Studio)"
    except Exception as e:
        return False, f"check failed: {e}"


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        return False, "ffmpeg not in PATH (run: brew install ffmpeg)"
    out = subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0]
    return True, out.split(" version ")[1].split(" ")[0] if " version " in out else "installed"


def check_mlx_whisper():
    try:
        import mlx_whisper  # noqa: F401
        version = getattr(mlx_whisper, "__version__", "unknown")
        return True, f"v{version}"
    except ImportError:
        return False, "not installed (run: pip3 install --user mlx-whisper)"


def check_anthropic():
    try:
        import anthropic  # noqa: F401
        version = getattr(anthropic, "__version__", "unknown")
        return True, f"v{version}"
    except ImportError:
        return False, "not installed (run: pip3 install --user anthropic)"


def check_jinja2():
    try:
        import jinja2  # noqa: F401
        return True, f"v{jinja2.__version__}"
    except ImportError:
        return False, "not installed (run: pip3 install --user jinja2)"


def check_skill_layout():
    skill_root = Path.home() / ".claude" / "skills" / "video-editor-davinci"
    required = ["SKILL.md", "scripts", "templates", "templates/macros", "brand-configs", "references"]
    missing = [p for p in required if not (skill_root / p).exists()]
    if missing:
        return False, f"missing: {', '.join(missing)}"
    return True, str(skill_root)


def main():
    print("=== video-editor-davinci :: setup check ===\n")

    print("— Environment variables —")
    check("RESOLVE_SCRIPT_API/_LIB/PYTHONPATH", check_env_vars)

    print("\n— DaVinci Resolve scripting —")
    check("DaVinciResolveScript module", check_resolve_script_module)
    check("Resolve connection", check_resolve_connection)
    check("Studio vs Free", check_studio_vs_free)

    print("\n— External binaries —")
    check("ffmpeg", check_ffmpeg)

    print("\n— Python packages —")
    check("mlx-whisper", check_mlx_whisper)
    check("anthropic", check_anthropic)
    check("jinja2", check_jinja2)

    print("\n— Skill layout —")
    check("Skill directory", check_skill_layout)

    print()
    failed = [label for ok, label in results if not ok]
    if failed:
        print(f"{FAIL} {len(failed)} check(s) failed: {', '.join(failed)}")
        print(f"   See references/setup.md for guidance.{RESET}")
        sys.exit(1)
    print(f"{OK} All checks passed. Skill is ready to use.{RESET}")


if __name__ == "__main__":
    main()

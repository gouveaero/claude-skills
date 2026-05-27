#!/usr/bin/env python3
"""
run_freepik.py — runtime Playwright humanizado para o Pikaso (Freepik).

Lê um markdown com header YAML + blocos JSON e submete os prompts ao
Pikaso através de um Chrome real com sessão persistente, digitando
caractere a caractere e respeitando caps de sessão (30/sessão, 60/h).

Output: logs em stderr; JSON estruturado na ÚLTIMA linha do stdout.

Spec completa: ../references/playwright-freepik.md
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from playwright.sync_api import (
    Locator,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


# ---------- Constantes ----------

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = SKILL_DIR / ".playwright-profile"
STATE_FILE = SKILL_DIR / ".session_state.json"
CREDS_FILE = SKILL_DIR / "credentials.local.json"
BLOCK_SHOTS_DIR = SKILL_DIR / ".block_screenshots"

CAP_PER_SESSION = 30
CAP_PER_HOUR = 60
SESSION_IDLE_MIN = 30
BLOCK_COOLDOWN_MIN = 60
HOURLY_WINDOW_HOURS = 1

PROJECT_SLUG_TO_UI = {
    "pessoal": "Pessoal",
    "ufmg": "UFMG",
    "spoiler": "Spoiler",
    "tribotax": "Tribotax",
    "exos": "Exos",
    "vhoe": "Vhoe.co",
    "saif": "SAIF",
}

BLOCK_PATTERNS = [
    r"captcha", r"verifica.*humano", r"verify.*human", r"bot.*detect",
    r"temporariamente.*bloquead", r"temporarily.*block",
    r"limite.*atingid", r"too many requests",
    r"cloudflare", r"challenge",
]

JSON_FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
SLIDE_HEADING_RE = re.compile(
    r"^(?:#{2,4})\s*(?:slide\s+)?(s\d+|S\d+|\d+)\b",
    re.IGNORECASE | re.MULTILINE,
)


# ---------- Logging ----------

def log(msg: str) -> None:
    """Emit human-readable progress to stderr. Stdout stays JSON-only."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


# ---------- Time helpers ----------

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


# ---------- Humanização ----------

def pause(lo: float, hi: float) -> None:
    time.sleep(random.uniform(lo, hi))


def human_type(page: Page, locator: Locator, text: str, log_label: str = "") -> dict:
    """Digita caractere a caractere com delays + typos ocasionais."""
    locator.scroll_into_view_if_needed()
    locator.click()
    pause(0.10, 0.30)
    start = time.time()
    n_typos = 0
    n_thinking = 0
    for ch in text:
        if random.random() < 0.015 and ch.isalpha():
            wrong = random.choice("abcdefghijklmnop")
            page.keyboard.type(wrong)
            pause(0.05, 0.12)
            page.keyboard.press("Backspace")
            pause(0.03, 0.08)
            n_typos += 1
        page.keyboard.type(ch)
        delay = max(0.012, random.gauss(0.035, 0.015))
        if random.random() < 0.02:
            delay += random.uniform(0.3, 1.0)
            n_thinking += 1
        time.sleep(delay)
    elapsed = time.time() - start
    cps = len(text) / elapsed if elapsed > 0 else 0
    if log_label:
        log(f"typed {len(text)} chars in {elapsed:.1f}s "
            f"({cps:.1f}cps, typos={n_typos}, thinking={n_thinking}) [{log_label}]")
    return {"chars": len(text), "elapsed_s": elapsed, "cps": cps}


def human_mouse_to(page: Page, locator: Locator) -> bool:
    """Move mouse em passos até ponto aleatório do bbox do elemento."""
    try:
        locator.scroll_into_view_if_needed(timeout=3_000)
    except PlaywrightTimeoutError:
        return False
    box = locator.bounding_box()
    if not box:
        return False
    x = box["x"] + random.uniform(0.25, 0.75) * box["width"]
    y = box["y"] + random.uniform(0.25, 0.75) * box["height"]
    page.mouse.move(x, y, steps=random.randint(15, 35))
    return True


def human_click(page: Page, locator: Locator) -> None:
    moved = human_mouse_to(page, locator)
    pause(0.10, 0.40)
    if moved:
        page.mouse.down()
        pause(0.04, 0.12)
        page.mouse.up()
    else:
        locator.click()


def inter_submission_pause(idx: int) -> float:
    base = random.uniform(12, 25)
    if idx > 0 and idx % random.randint(5, 10) == 0:
        extra = random.uniform(30, 90)
        log(f"long break ({extra:.0f}s) after submission #{idx}")
        base += extra
    return base


# ---------- Markdown parsing ----------

@dataclass
class Slide:
    label: str
    prompt: dict


@dataclass
class MdData:
    path: Path
    project_slug: str
    aspect: str
    variations: int
    resolution: str
    model: str
    mode: str
    on_complete: dict
    label: str
    slides: list[Slide]


def infer_project_from_path(path: Path) -> str | None:
    s = str(path).lower()
    rules = [
        (r"vhoe|vhoe\.co", "vhoe"),
        (r"saif|zahnspangehome", "saif"),
        (r"alex_agrotax|tribotax", "tribotax"),
        (r"/exos[/_]|exos_", "exos"),
        (r"/ufmg/|/faculdade/", "ufmg"),
        (r"projeto_eu|/pessoal/", "pessoal"),
    ]
    for pat, slug in rules:
        if re.search(pat, s):
            return slug
    return None


def parse_markdown(path: Path) -> MdData:
    raw = path.read_text(encoding="utf-8")
    # frontmatter
    fm = {}
    body = raw
    if raw.startswith("---"):
        try:
            _, fm_text, body = raw.split("---", 2)
            fm = yaml.safe_load(fm_text) or {}
        except ValueError:
            pass

    slug = fm.get("project") or infer_project_from_path(path)

    # Build label index by scanning headings before each JSON block.
    blocks = []
    for m in JSON_FENCE_RE.finditer(body):
        json_text = m.group(1).strip()
        try:
            prompt = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise SystemExit(f"invalid JSON block @ char {m.start()}: {e}")
        # Find nearest preceding heading
        prefix = body[: m.start()]
        head = None
        for hm in SLIDE_HEADING_RE.finditer(prefix):
            head = hm.group(1)
        label = head if head else None
        blocks.append((label, prompt))

    # Fall back to positional sN labels for missing
    slides: list[Slide] = []
    for idx, (label, prompt) in enumerate(blocks, start=1):
        if not label:
            label = f"s{idx}"
        # Normalize "1" -> "s1", "S2" -> "s2"
        m = re.match(r"^[sS]?(\d+)$", label)
        if m:
            label = f"s{int(m.group(1))}"
        slides.append(Slide(label=label, prompt=prompt))

    return MdData(
        path=path,
        project_slug=slug,
        aspect=fm.get("aspect", "9:16"),
        variations=int(fm.get("variations", 3)),
        resolution=fm.get("resolution", "2K"),
        model=fm.get("model", "nano-banana-2"),
        mode=fm.get("mode", "normal"),
        on_complete=fm.get("on_complete") or {},
        label=fm.get("label", path.stem),
        slides=slides,
    )


# ---------- Rate limiter ----------

@dataclass
class RateState:
    session_id: str
    started_at: str
    last_activity_at: str
    submissions_this_session: int = 0
    submissions_log: list[dict] = field(default_factory=list)
    last_block_detected: str | None = None
    cap_per_session: int = CAP_PER_SESSION
    cap_per_hour: int = CAP_PER_HOUR

    @classmethod
    def load_or_new(cls) -> "RateState":
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                inst = cls(**data)
                last = parse_iso(inst.last_activity_at)
                if datetime.now(last.tzinfo) - last > timedelta(minutes=SESSION_IDLE_MIN):
                    log(f"previous session idle >{SESSION_IDLE_MIN}min — starting fresh session")
                    return cls._fresh()
                return inst
            except Exception as e:
                log(f"state file corrupt ({e}); starting fresh")
        return cls._fresh()

    @classmethod
    def _fresh(cls) -> "RateState":
        t = now_iso()
        return cls(session_id=t, started_at=t, last_activity_at=t)

    def save(self) -> None:
        STATE_FILE.write_text(json.dumps(asdict(self), indent=2))

    def in_block_cooldown(self) -> tuple[bool, str | None]:
        if not self.last_block_detected:
            return False, None
        last = parse_iso(self.last_block_detected)
        elapsed = datetime.now(last.tzinfo) - last
        if elapsed < timedelta(minutes=BLOCK_COOLDOWN_MIN):
            mins_left = BLOCK_COOLDOWN_MIN - int(elapsed.total_seconds() / 60)
            return True, f"block cooldown active for ~{mins_left}min more"
        return False, None

    def hourly_count(self) -> int:
        now = datetime.now(timezone.utc).astimezone()
        cutoff = now - timedelta(hours=HOURLY_WINDOW_HOURS)
        return sum(1 for e in self.submissions_log if parse_iso(e["t"]) >= cutoff)

    def can_submit(self) -> tuple[bool, str | None]:
        cooldown, msg = self.in_block_cooldown()
        if cooldown:
            return False, msg
        if self.submissions_this_session >= self.cap_per_session:
            return False, f"session cap reached ({self.cap_per_session})"
        if self.hourly_count() >= self.cap_per_hour:
            return False, f"hourly cap reached ({self.cap_per_hour})"
        return True, None

    def record(self, label: str, v: int, path: str) -> None:
        t = now_iso()
        self.submissions_log.append({"t": t, "label": label, "v": v, "path": path})
        self.submissions_this_session += 1
        self.last_activity_at = t
        # Truncate log to last 2h
        cutoff = datetime.now(timezone.utc).astimezone() - timedelta(hours=2)
        self.submissions_log = [
            e for e in self.submissions_log if parse_iso(e["t"]) >= cutoff
        ]
        self.save()

    def mark_block(self) -> None:
        self.last_block_detected = now_iso()
        self.save()


# ---------- Browser setup ----------

def launch_context(pw: Playwright, headed: bool):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    log(f"launching Chrome (profile={PROFILE_DIR}, headed={headed})")
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="chrome",
        headless=not headed,
        viewport={"width": 1440, "height": 900},
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    ctx.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    return ctx


def load_creds() -> dict:
    if not CREDS_FILE.exists():
        raise SystemExit(f"credentials file missing: {CREDS_FILE}")
    return json.loads(CREDS_FILE.read_text())["freepik"]


def ensure_logged_in(page: Page, creds: dict) -> None:
    """Magnific (sucessor do Pikaso) — login em id.magnific.com via 'Continue with email'."""
    log("navigating to Magnific")
    page.goto(creds["pikasoUrl"], wait_until="domcontentloaded", timeout=45_000)
    pause(3.0, 4.5)  # give UI time to settle before checking login state
    needs_login = page.locator("text=Fazer login").count() > 0 or "log-in" in page.url
    if needs_login:
        log("not logged in — running Magnific login flow")
        if "log-in" not in page.url:
            page.locator("text=Fazer login").first.click()
        page.wait_for_url(re.compile(r"id\.magnific\.com.*log-in"), timeout=15_000)
        pause(1.5, 2.5)
        cont_email = page.locator("button:has-text('Continue with email')").first
        human_click(page, cont_email)
        page.wait_for_selector('input[type="email"]', timeout=10_000)
        pause(0.6, 1.2)
        human_type(page, page.locator('input[type="email"]').first, creds["email"], "email")
        pause(0.5, 1.0)
        cont_btn = page.locator("button:has-text('Continue')").first
        human_click(page, cont_btn)
        page.wait_for_selector('input[type="password"]', timeout=10_000)
        pause(0.6, 1.4)
        human_type(page, page.locator('input[type="password"]').first, creds["password"], "password")
        pause(0.4, 0.9)
        for label in ("Log in", "Sign in", "Entrar"):
            btn = page.locator(f"button:has-text('{label}')").first
            if btn.count() > 0 and btn.is_visible():
                human_click(page, btn)
                break
        page.wait_for_url(re.compile(r"magnific\.com.*ai-image-generator"), timeout=30_000)
        log("login submitted, redirected to app")
    page.wait_for_selector('[data-cy="image-prompt-input"]', timeout=30_000)
    log("Magnific generator loaded")


# ---------- Pikaso project + config ----------

def current_project_ui(page: Page) -> str | None:
    """Magnific: the active project name is the innerText of header-current-project-link."""
    link = page.locator('[data-cy="header-current-project-link"]').first
    if link.count() == 0:
        return None
    try:
        txt = link.inner_text(timeout=2000)
    except PlaywrightTimeoutError:
        return None
    return txt.strip() if txt else None


def slug_from_ui(name: str) -> str:
    n = name.strip().lower().replace(".co", "").replace(" ", "")
    if n == "projetopessoal":
        return "pessoal"
    return n


def ensure_project_active(page: Page, target_slug: str) -> tuple[bool, str | None]:
    """Magnific: switch project by navigating through /br/app/projects/work hub."""
    current_ui = current_project_ui(page)
    if not current_ui:
        return False, "header-current-project-link not found"
    target_ui = PROJECT_SLUG_TO_UI.get(target_slug)
    if not target_ui:
        return False, f"unknown slug '{target_slug}'"
    current_slug = slug_from_ui(current_ui)
    if current_slug == target_slug:
        log(f"project already active: {current_ui}")
        return True, None
    # Magnific projects hub renders cards as React-routed divs, not <a href>.
    # Programmatic switch via hub is brittle; warn and continue in current project.
    log(
        f"WARN: target project '{target_ui}' differs from current '{current_ui}'. "
        f"Skipping switch (Magnific hub unreliable for automation). "
        f"User can move outputs later via UI."
    )
    return True, f"warning: stayed in '{current_ui}' (target was '{target_ui}')"
    # --- legacy hub-switch code below, currently unreachable ---
    page.goto(
        "https://www.magnific.com/br/app/projects/work",
        wait_until="domcontentloaded",
        timeout=30_000,
    )
    pause(2.0, 3.0)
    # Find an anchor whose visible text matches target_ui (case-insensitive).
    target_link = (
        page.locator("a")
        .filter(has_text=re.compile(rf"^\s*{re.escape(target_ui)}\s*$", re.I))
        .first
    )
    if target_link.count() == 0:
        target_link = (
            page.locator("a").filter(has_text=re.compile(re.escape(target_ui), re.I)).first
        )
    if target_link.count() == 0:
        # Fallback: try any clickable element (button, div with role=button) carrying the name
        target_link = (
            page.locator("button, [role='button'], [role='link']")
            .filter(has_text=re.compile(rf"^\s*{re.escape(target_ui)}\s*$", re.I))
            .first
        )
    if target_link.count() == 0:
        # Non-blocking: stay on current project, surface a warning via return
        log(
            f"WARN: '{target_ui}' link not found in hub — continuing in current "
            f"project '{current_ui}'. User can move outputs later."
        )
        # Return to generator anyway so submission can proceed.
        page.goto(
            "https://www.magnific.com/br/app/ai-image-generator",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        page.wait_for_selector('[data-cy="image-prompt-input"]', timeout=30_000)
        return True, f"warning: project switch skipped, still in '{current_ui}'"
    human_click(page, target_link)
    pause(2.0, 3.0)
    # Return to the generator inside the new project context
    page.goto(
        "https://www.magnific.com/br/app/ai-image-generator",
        wait_until="domcontentloaded",
        timeout=30_000,
    )
    page.wait_for_selector('[data-cy="image-prompt-input"]', timeout=30_000)
    pause(1.5, 2.5)
    new_ui = current_project_ui(page)
    if new_ui and slug_from_ui(new_ui) == target_slug:
        log(f"project switched to: {new_ui}")
        return True, None
    return False, f"after switch expected '{target_ui}', got '{new_ui}'"


def ensure_session_config(page: Page, md: MdData) -> None:
    """Best-effort setup: model, aspect, resolution. Tolerant to existing state."""
    # Aspect
    try:
        aspect_input = page.locator('[data-cy="image-aspect-ratio-input"]').first
        if aspect_input.count() > 0:
            current = (aspect_input.inner_text() or "").strip()
            if md.aspect not in current:
                log(f"setting aspect {current!r} → {md.aspect}")
                human_click(page, aspect_input)
                page.wait_for_selector('[data-cy="popover-option"]', timeout=4_000)
                opts = page.locator('[data-cy="popover-option"]')
                desired_re = re.compile(re.escape(md.aspect).replace(":", r"\s*[:x]\s*"), re.I)
                target = opts.filter(has_text=desired_re).first
                if target.count() > 0:
                    human_click(page, target)
                else:
                    page.keyboard.press("Escape")
                pause(0.6, 1.2)
    except Exception as e:
        log(f"aspect setup warning: {e}")

    # Resolution
    try:
        res_input = page.locator('[data-cy="image-resolution-input"]').first
        if res_input.count() > 0:
            current = (res_input.inner_text() or "").strip()
            if md.resolution.lower() not in current.lower():
                log(f"setting resolution {current!r} → {md.resolution}")
                human_click(page, res_input)
                page.wait_for_selector('[data-cy="popover-option"]', timeout=4_000)
                opts = page.locator('[data-cy="popover-option"]')
                target = opts.filter(has_text=re.compile(md.resolution, re.I)).first
                if target.count() > 0:
                    human_click(page, target)
                else:
                    page.keyboard.press("Escape")
                pause(0.6, 1.2)
    except Exception as e:
        log(f"resolution setup warning: {e}")


# ---------- Block detection ----------

def detect_block(page: Page) -> tuple[bool, str | None]:
    url = page.url.lower()
    if "/challenge" in url or "cf_chl_" in url:
        return True, f"url:{url}"
    try:
        body = page.evaluate(
            "() => (document.body && document.body.innerText || '').toLowerCase().slice(0, 5000)"
        )
    except Exception:
        return False, None
    for pat in BLOCK_PATTERNS:
        if re.search(pat, body):
            return True, f"text:/{pat}/"
    return False, None


def save_block_screenshot(page: Page) -> str:
    BLOCK_SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = BLOCK_SHOTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        return ""


# ---------- Submission loop ----------

def submit_one(page: Page, prompt_obj: dict, dry_run: bool) -> dict:
    editable = page.locator('[data-cy="image-prompt-input"] [contenteditable="true"]').first
    editable.wait_for(state="visible", timeout=15_000)
    human_click(page, editable)
    pause(0.2, 0.5)
    # Clear existing
    page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
    pause(0.05, 0.15)
    page.keyboard.press("Delete")
    pause(0.10, 0.30)
    prompt_text = json.dumps(prompt_obj, ensure_ascii=False)
    typing = human_type(page, editable, prompt_text, log_label="prompt")
    # "Read what I just typed"
    pause(2.0, 8.0)
    btn = page.locator('[data-cy="generate-button"]').first
    btn.wait_for(state="visible", timeout=15_000)
    # Wait for button to become enabled
    try:
        page.wait_for_function(
            """() => {
                const b = document.querySelector('[data-cy="generate-button"]');
                return b && !b.disabled;
            }""",
            timeout=25_000,
        )
    except PlaywrightTimeoutError:
        return {"clicked": False, "reason": "generate-button-stuck-disabled", "typing": typing}
    if dry_run:
        return {"clicked": False, "reason": "dry-run", "typing": typing}
    human_click(page, btn)
    return {"clicked": True, "typing": typing}


def regenerate_same(page: Page, dry_run: bool) -> dict:
    """Re-click Gerar without retyping the prompt — variations share the same text."""
    empty_typing = {"chars": 0, "elapsed_s": 0.0, "cps": 0.0}
    btn = page.locator('[data-cy="generate-button"]').first
    btn.wait_for(state="visible", timeout=15_000)
    try:
        page.wait_for_function(
            """() => {
                const b = document.querySelector('[data-cy="generate-button"]');
                return b && !b.disabled;
            }""",
            timeout=25_000,
        )
    except PlaywrightTimeoutError:
        return {"clicked": False, "reason": "generate-button-stuck-disabled", "typing": empty_typing}
    if dry_run:
        return {"clicked": False, "reason": "dry-run", "typing": empty_typing}
    human_click(page, btn)
    return {"clicked": True, "typing": empty_typing}


def submission_loop(
    page: Page,
    md: MdData,
    rate: RateState,
    args: argparse.Namespace,
) -> dict:
    fired = []
    pauses = []
    by_label: dict[str, dict] = {s.label: {"fired": 0, "done": 0} for s in md.slides}
    block_evidence: str | None = None
    status = "loop_done"
    total_attempts = 0

    for slide in md.slides:
        for v in range(1, md.variations + 1):
            can, why = rate.can_submit()
            if not can:
                log(f"cap reached: {why}")
                status = "cap_reached" if "cap" in (why or "") else "blocked"
                if status == "blocked":
                    block_evidence = why
                return _wrap_loop_result(
                    status, fired, by_label, pauses, block_evidence, total_attempts
                )

            total_attempts += 1
            log(f"[{total_attempts}/{len(md.slides)*md.variations}] "
                f"submitting {slide.label} v{v}")
            try:
                if args.simulate_block_at and total_attempts >= args.simulate_block_at:
                    log("SIMULATE_BLOCK: forcing blocked status")
                    block_evidence = "simulated"
                    rate.mark_block()
                    return _wrap_loop_result(
                        "blocked", fired, by_label, pauses, block_evidence, total_attempts
                    )
                if v == 1:
                    res = submit_one(page, slide.prompt, args.dry_run)
                else:
                    # Same prompt already in the input — just re-click Gerar.
                    res = regenerate_same(page, args.dry_run)
            except PlaywrightTimeoutError as e:
                log(f"timeout submitting {slide.label} v{v}: {e}")
                fired.append({
                    "label": slide.label, "v": v, "ts": now_iso(),
                    "clicked": False, "error": "playwright-timeout",
                })
                continue

            if res["clicked"]:
                rate.record(slide.label, v, str(md.path))
                by_label[slide.label]["fired"] += 1
            fired.append({
                "label": slide.label, "v": v, "ts": now_iso(),
                "clicked": res["clicked"], "reason": res.get("reason"),
                "typing_cps": res["typing"]["cps"],
            })

            # Block detection after each click
            is_block, reason = detect_block(page)
            if is_block:
                log(f"BLOCK DETECTED: {reason}")
                block_evidence = reason
                shot = save_block_screenshot(page)
                if shot:
                    block_evidence = f"{reason} [screenshot: {shot}]"
                rate.mark_block()
                return _wrap_loop_result(
                    "blocked", fired, by_label, pauses, block_evidence, total_attempts
                )

            wait = inter_submission_pause(len(fired))
            pauses.append(wait)
            log(f"waiting {wait:.1f}s before next submission")
            time.sleep(wait)

    return _wrap_loop_result(status, fired, by_label, pauses, block_evidence, total_attempts)


def _wrap_loop_result(status, fired, by_label, pauses, block_evidence, total_attempts):
    return {
        "loop_status": status,
        "fired": fired,
        "by_label": by_label,
        "pauses": pauses,
        "block_evidence": block_evidence,
        "total_attempts": total_attempts,
    }


# ---------- Polling ----------

POLL_JS = """
() => {
  const items = [...document.querySelectorAll('[data-cy="feed-virtual-item"]')];
  let inflight = 0, queued = 0, done = 0;
  for (const el of items) {
    const t = el.textContent || '';
    if (/Gerando|Preparando/i.test(t)) inflight++;
    else if (/Na fila/i.test(t)) queued++;
    else {
      const imgs = [...el.querySelectorAll('img')].filter(im => im.naturalWidth > 0 || im.src).length;
      if (imgs > 0) done += imgs;
    }
  }
  return { inflight, queued, done };
}
"""


def poll_until_converged(page: Page, expected_fired: int, max_minutes: int = 15) -> dict:
    if expected_fired == 0:
        return {"converged": True, "inflight": 0, "queued": 0, "done": 0, "rounds": 0}
    deadline = time.time() + max_minutes * 60
    streak_zero = 0
    last = {"inflight": -1, "queued": -1, "done": 0}
    rounds = 0
    while time.time() < deadline:
        rounds += 1
        try:
            state = page.evaluate(POLL_JS)
        except Exception as e:
            log(f"poll error: {e}")
            time.sleep(5)
            continue
        log(f"poll #{rounds}: inflight={state['inflight']} "
            f"queued={state['queued']} done={state['done']}")
        last = state
        if state["inflight"] == 0 and state["queued"] == 0:
            streak_zero += 1
            if streak_zero >= 2:
                return {"converged": True, **state, "rounds": rounds}
        else:
            streak_zero = 0
        time.sleep(random.uniform(15, 20))
    return {"converged": False, **last, "rounds": rounds, "timeout": True}


# ---------- Output ----------

def emit_json(payload: dict) -> None:
    """Print final result as JSON on stdout (last line)."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_payload(
    md: MdData,
    project_result: tuple[bool, str | None],
    loop_result: dict,
    poll_result: dict | None,
    rate: RateState,
    duration: float,
    args: argparse.Namespace,
) -> dict:
    expected = len(md.slides) * md.variations
    fired_clicks = sum(1 for f in loop_result["fired"] if f.get("clicked"))
    skipped = sum(1 for f in loop_result["fired"] if not f.get("clicked") and f.get("reason"))
    errors = sum(1 for f in loop_result["fired"] if f.get("error"))

    by_label = dict(loop_result["by_label"])
    if poll_result and poll_result.get("converged"):
        # Distribute done counts evenly across labels we fired (best-effort).
        total_done = poll_result["done"]
        for label, st in by_label.items():
            st["done"] = min(st["fired"], math.ceil(total_done / max(1, len(by_label))))

    loop_status = loop_result["loop_status"]
    block_evidence = loop_result["block_evidence"]

    if loop_status == "blocked":
        status = "blocked"
        next_action = "alert_user_blocked"
    elif loop_status == "cap_reached":
        status = "cap_reached"
        next_action = "wait_then_resume"
    elif poll_result is None:
        status = "partial" if fired_clicks < expected else "converged"
        next_action = "partial_retry" if status == "partial" else "run_on_complete"
    elif poll_result.get("converged") and fired_clicks == expected and skipped == 0 and errors == 0:
        status = "converged"
        next_action = "run_on_complete"
    elif fired_clicks == 0:
        status = "error"
        next_action = "ask_user"
    else:
        status = "partial"
        next_action = "partial_retry"

    # remaining labels (those with fired < variations)
    remaining = sorted({
        s.label for s in md.slides
        if by_label.get(s.label, {}).get("fired", 0) < md.variations
    })

    resume_iso = None
    if status == "cap_reached":
        resume_iso = (datetime.now(timezone.utc).astimezone() + timedelta(minutes=10)).isoformat(timespec="seconds")

    avg_cps = 0.0
    cps_vals = [f.get("typing_cps") for f in loop_result["fired"] if f.get("typing_cps")]
    if cps_vals:
        avg_cps = sum(cps_vals) / len(cps_vals)
    pauses = loop_result["pauses"]
    avg_pause = sum(pauses) / len(pauses) if pauses else 0.0
    longest_pause = max(pauses) if pauses else 0.0

    payload = {
        "status": status,
        "path": str(md.path),
        "project": {
            "requested_slug": md.project_slug,
            "active_ok": project_result[0],
            "active_error": project_result[1],
            "active_ui_name": PROJECT_SLUG_TO_UI.get(md.project_slug, "?"),
        },
        "totals": {
            "expected": expected,
            "fired": fired_clicks,
            "skipped": skipped,
            "errors": errors,
            "done": poll_result["done"] if poll_result else 0,
        },
        "by_label": by_label,
        "duration_seconds": round(duration, 1),
        "humanization": {
            "avg_typing_cps": round(avg_cps, 2),
            "avg_pause_between_subs_s": round(avg_pause, 2),
            "longest_pause_s": round(longest_pause, 2),
            "session_submissions_total": rate.submissions_this_session,
            "hourly_window_total": rate.hourly_count(),
        },
        "next_action": next_action,
        "remaining_labels": remaining,
        "resume_suggested_at_iso": resume_iso,
        "prompt_for_user": None,
        "block_evidence": block_evidence,
        "dry_run": bool(args.dry_run),
    }

    # Project not found → ask user
    if not project_result[0] and project_result[1] and "not found" in project_result[1]:
        payload["status"] = "needs_user_input"
        payload["next_action"] = "ask_user"
        payload["prompt_for_user"] = (
            f"Projeto Pikaso '{md.project_slug}' "
            f"({PROJECT_SLUG_TO_UI.get(md.project_slug, '?')}) "
            f"não foi encontrado na conta. Opções: (a) criar agora, (b) usar outro projeto da lista, (c) cancelar."
        )

    return payload


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="run_freepik.py",
        description="Submete prompts ao Pikaso (Freepik) via Playwright humanizado.",
    )
    ap.add_argument("path", help="Caminho do markdown com header YAML + blocos JSON")
    ap.add_argument("--only", help="Lista de labels (csv) a regerar (ex: s1,s3)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Faz tudo menos o click final em Gerar")
    ap.add_argument("--variations", type=int,
                    help="Override de variations do YAML")
    ap.add_argument("--headed", dest="headed", action="store_true", default=True,
                    help="Browser visível (default, recomendado por anti-detect)")
    ap.add_argument("--headless", dest="headed", action="store_false",
                    help="Browser sem UI (NÃO recomendado — facilita detecção)")
    ap.add_argument("--simulate-block-at", type=int, default=0,
                    help="(test) Força status=blocked na N-ésima submissão")
    return ap.parse_args()


def apply_filters(md: MdData, args: argparse.Namespace) -> None:
    if args.variations is not None:
        md.variations = args.variations
    if args.only:
        only_set = {x.strip() for x in args.only.split(",")}
        md.slides = [s for s in md.slides if s.label in only_set]


# ---------- main ----------

def main() -> int:
    args = parse_args()
    md_path = Path(args.path).expanduser().resolve()
    if not md_path.exists():
        emit_json({"status": "error", "error": f"file not found: {md_path}", "next_action": "ask_user"})
        return 0

    md = parse_markdown(md_path)
    apply_filters(md, args)
    if not md.slides:
        emit_json({"status": "error", "error": "0 JSON blocks (after --only filter)", "next_action": "ask_user"})
        return 0
    if not md.project_slug:
        emit_json({
            "status": "needs_user_input",
            "prompt_for_user": "project ausente do YAML e não infereível pelo caminho — qual slug usar?",
            "next_action": "ask_user",
        })
        return 0

    rate = RateState.load_or_new()
    can, why = rate.can_submit()
    if not can:
        # short-circuit before opening browser
        payload = {
            "status": "cap_reached" if "cap" in (why or "") else "blocked",
            "path": str(md_path),
            "totals": {"expected": len(md.slides) * md.variations, "fired": 0, "skipped": 0, "errors": 0, "done": 0},
            "next_action": "wait_then_resume" if "cap" in (why or "") else "alert_user_blocked",
            "block_evidence": why,
            "remaining_labels": [s.label for s in md.slides],
            "resume_suggested_at_iso": (
                datetime.now(timezone.utc).astimezone() + timedelta(minutes=10)
            ).isoformat(timespec="seconds"),
            "dry_run": bool(args.dry_run),
        }
        emit_json(payload)
        return 0

    creds = load_creds()
    started = time.time()
    project_result = (False, "not attempted")
    loop_result = {"loop_status": "not_started", "fired": [], "by_label": {},
                   "pauses": [], "block_evidence": None, "total_attempts": 0}
    poll_result: dict | None = None

    try:
        with sync_playwright() as pw:
            ctx = launch_context(pw, headed=args.headed)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                ensure_logged_in(page, creds)
                is_block, reason = detect_block(page)
                if is_block:
                    rate.mark_block()
                    loop_result["block_evidence"] = reason
                    loop_result["loop_status"] = "blocked"
                else:
                    project_result = ensure_project_active(page, md.project_slug)
                    if project_result[0]:
                        ensure_session_config(page, md)
                        loop_result = submission_loop(page, md, rate, args)
                        if loop_result["loop_status"] not in ("blocked", "cap_reached"):
                            # poll only when something was actually fired
                            n_fired = sum(1 for f in loop_result["fired"] if f.get("clicked"))
                            if n_fired > 0:
                                poll_result = poll_until_converged(page, n_fired)
                            else:
                                poll_result = {"converged": True, "inflight": 0, "queued": 0, "done": 0, "rounds": 0}
            finally:
                ctx.close()
    except Exception as e:
        log(f"FATAL: {e}")
        emit_json({
            "status": "error",
            "error": str(e),
            "path": str(md_path),
            "next_action": "ask_user",
            "dry_run": bool(args.dry_run),
        })
        return 0

    duration = time.time() - started
    payload = build_payload(md, project_result, loop_result, poll_result, rate, duration, args)
    emit_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())

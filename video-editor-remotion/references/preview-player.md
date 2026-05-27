# Embeddable Preview Player

Share a frame-accurate preview URL with the client BEFORE the final render. Saves an iteration round-trip vs. exporting MP4 → email → client opens.

Built on `@remotion/player` (the same React component that powers the Remotion landing-page demos).

## When to use

- **Client approval gate** — TriboTax, Telesapiens, Vhoe stakeholders watch the reel and approve motion graphics + cuts before committing to final render.
- **Internal review on mobile** — your phone in fullscreen via the URL.
- **Side-by-side comparison** — open two preview URLs in adjacent browser tabs to compare v1 vs v2.

## Quick start

```bash
python3 ~/.claude/skills/video-editor/scripts/preview_player.py \
  --remotion-dir <output>/remotion \
  --port 8123
```

Opens `http://localhost:8123/` with the reel auto-loaded. Share via ngrok / tailscale-funnel / vps tunnel if the client is remote.

## What it does

1. Calls `npx remotion bundle src/index.ts --out-dir <out>/bundle/` to produce a static asset bundle.
2. Writes an `index.html` wrapper that mounts an `<iframe>` over the bundle.
3. Serves the directory via `npx serve`.

The bundle is fully static — no server-side dependency. You can also upload `<out>/preview/` to S3/Cloudflare R2 and share a CDN URL.

## Studio mode (dev only)

```bash
python3 preview_player.py --remotion-dir <output>/remotion --studio --port 8123
```

Opens `npx remotion studio` instead. Full dev experience with prop sliders / Zod-driven inputs, but NOT for sharing externally — exposes the source code and supports editing.

## Tunneling to a public URL

```bash
# tailscale funnel (recommended — no auth tokens needed)
tailscale funnel 8123

# or ngrok
ngrok http 8123
```

## Notes on sharing

- The bundle includes ALL assets referenced via `staticFile()`, including raw `.mov`/`.mp3` files. For long reels with HD video, the bundle can be hundreds of MB. Consider transcoding video assets to lower bitrate before bundling for preview.
- The `<Player>` does NOT cache audio — each play re-streams from the bundle. Test on the actual deployment target.
- For long-term hosting (e.g. embed the player on a client portal), build the bundle once + serve via CDN.

## Anti-patterns

- **Sharing the Studio URL externally** — Studio is dev tooling; exposes templates, lets users edit props. Use bundled `--port`-served preview instead.
- **Re-bundling on every change** — bundling takes 30-90s. Bundle once after Visual Review passes; only re-bundle on actual code changes.
- **Serving from `~/.claude/skills/video-editor/`** — the skill directory is read-only by convention. Always use `<output>/remotion/preview/`.

## See also

- [remotion-feature-catalog.md](./remotion-feature-catalog.md) — `@remotion/player` reference
- [visual-review.md](./visual-review.md) — automated review loop that runs BEFORE you share with client

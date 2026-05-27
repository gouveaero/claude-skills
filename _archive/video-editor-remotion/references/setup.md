# Setup — video-editor-remotion

## One-time prerequisites

### 1. Node.js 18+

```bash
node --version  # should be >= v18
```

If missing or older:
```bash
brew install node          # macOS
# or download from https://nodejs.org
```

### 2. ffmpeg + ffprobe

```bash
brew install ffmpeg        # macOS
# or apt install ffmpeg     # Linux
```

Used for HEVC → H.264 transcoding before Remotion ingests clips.

### 3. mlx-whisper (Apple Silicon)

```bash
pip install mlx-whisper
```

Cross-platform fallback: `npx remotion install whisper-cpp` (will be downloaded into the per-reel project on first run).

### 4. Anthropic API key

```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
source ~/.zshrc
```

### 5. Anthropic Python SDK

```bash
pip install anthropic
```

### Verify everything

```bash
python3 ~/.claude/skills/video-editor-remotion/scripts/check_setup.py
```

Should output `✅ All checks passed`.

## Per-reel setup

Each reel scaffolds its own Remotion project at `<ClientFolder>/output/<reel-name>/remotion/`. The first scaffold takes ~1 min (`npm install` for ~200MB node_modules). Subsequent runs reuse the project.

To verify a scaffolded project:
```bash
cd <ClientFolder>/output/<reel>/remotion
npx remotion studio       # opens at localhost:3000
```

## Cleanup

To free disk space from old reels' node_modules:
```bash
find ~/.../output/*/remotion/node_modules -maxdepth 0 -type d -exec rm -rf {} +
```

(They re-install on next scaffold.)

## Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `Cannot find module 'remotion'` | Scaffold incomplete | `cd remotion && npm install` |
| `Studio port 3000 in use` | Other process | `preview.py` retries 3001, 3002, ... automatically |
| Black frames in preview | HEVC clip not transcoded | Run `setup_project.py` again — it'll detect missing proxies |
| `whisper not found` | mlx-whisper not installed | `pip install mlx-whisper` (or use whisper-cpp fallback) |
| `ANTHROPIC_API_KEY not set` | Env var missing | Add to `~/.zshrc` and `source` |
| Render is very slow | Concurrency too low | Add `--concurrency 4` (or higher on M-series) |

## Reference URLs

- Remotion docs: https://www.remotion.dev/docs/
- `@remotion/captions`: https://www.remotion.dev/docs/captions/
- `@remotion/install-whisper-cpp`: https://www.remotion.dev/docs/install-whisper-cpp/
- `@remotion/transitions`: https://www.remotion.dev/docs/transitions/
- Audiogram template (closest fit): https://github.com/remotion-dev/template-audiogram

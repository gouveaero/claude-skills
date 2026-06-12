# Coolify Env-Var Setup (per VPS)

The skill puts all platform secrets in env vars — never in code, never in `.tracking.json`. This file explains how to wire them up on each Coolify instance.

## Two VPSes — keep them separate

Gabriel runs two Coolify instances:

| VPS | Address | Coolify URL | What lives here |
|-----|---------|-------------|-----------------|
| **Exos** | `187.127.30.29` | `coolify.exosmkt.com` | Exos client sites (Letícia, Elen, Dr. Kleber, etc.), Exos infra (n8n, Typebot) |
| **Gabriel pessoal / Gouvêa Growth** | `187.127.2.180` | `coolify.gabrielgouvea.com.br` | Personal projects, Gouvêa Growth, TriboTax |

**Never** put an Exos client's tokens on the personal VPS or vice versa. The skill always asks which VPS before generating Coolify-specific commands. If the user hasn't said, default to the VPS matching the client's folder (Exos clients → Exos VPS).

## Env var naming convention

Per app:
- `META_PIXEL_ID` — public, used client-side, prefix `NEXT_PUBLIC_` for Next.js exposure
- `META_CAPI_TOKEN` — secret, server-only
- `META_GRAPH_VERSION` — public-ish, default `v25.0`
- `META_TEST_EVENT_CODE` — leave empty in production
- `GA4_MEASUREMENT_ID` — public, prefix `NEXT_PUBLIC_`
- `GA4_API_SECRET` — secret, server-only
- `TIKTOK_PIXEL_ID` — public, prefix `NEXT_PUBLIC_`
- `TIKTOK_ACCESS_TOKEN` — secret, server-only
- `TIKTOK_TEST_EVENT_CODE` — leave empty in production
- `GOOGLE_ADS_CONVERSION_ID` — public, prefix `NEXT_PUBLIC_`

For Next.js, `NEXT_PUBLIC_*` vars are inlined into the client bundle at build time. For Vite, the equivalent is `VITE_*`. The skill's templates use the right prefix per stack.

## Setting env vars in Coolify — UI

1. SSH into Coolify (`ssh vps-exos` or `ssh vps-pessoal`).
2. Open `https://coolify.exosmkt.com` (or personal equivalent) in browser.
3. Navigate to project → application.
4. Tab "Environment Variables" → "Add" for each var.
5. For client-bundle vars (`NEXT_PUBLIC_*`, `VITE_*`), check "Is Build Time?" so they're available during `bun run build` / `npm run build`.
6. For server-only secrets (`META_CAPI_TOKEN`, `GA4_API_SECRET`, `TIKTOK_ACCESS_TOKEN`), leave "Is Build Time?" unchecked.
7. Click "Save" → trigger redeploy ("Force Rebuild" if env changed).

## Setting env vars in Coolify — API (faster for many vars)

The Coolify API is documented at `https://coolify.exosmkt.com/api/v1/`. You need a Coolify API token (Settings → API Tokens). Lives in your local `~/.config/coolify/exos.env` (gitignored).

```bash
# Bulk-add env vars to an app
curl -X POST "https://coolify.exosmkt.com/api/v1/applications/{APP_UUID}/envs" \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "META_CAPI_TOKEN",
    "value": "EAAR...",
    "is_build_time": false,
    "is_preview": false
  }'
```

After bulk-adding, trigger redeploy:

```bash
curl -X POST "https://coolify.exosmkt.com/api/v1/applications/{APP_UUID}/restart" \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN"
```

For Letícia Lang's app, `{APP_UUID}` is documented in `Exos/Leticia_Lang/.coolify-app.json` (if present) or readable via Coolify UI.

## Where the user gets each secret

| Secret | Where to generate |
|--------|------------------|
| `META_CAPI_TOKEN` | Events Manager → Settings → Conversions API → Generate Access Token |
| `GA4_API_SECRET` | GA4 Admin → Data Streams → Web → your stream → Measurement Protocol API secrets → Create |
| `TIKTOK_ACCESS_TOKEN` | TikTok Events Manager → Settings → Generate Access Token |
| `META_TEST_EVENT_CODE` | Events Manager → Test Events → top of the page (use only during testing) |

The post-install checklist walks the user through each. **Always remind them to NOT paste tokens into chat** — the skill should not see them at all. The user goes from "Generate Token" page directly to Coolify's env-var input.

## Sidecar service for Vite SPAs

The Vite template ships a `tracking-sidecar/` folder that runs as a **separate Coolify app**. Configuration:

- Repo: same as the main site (multi-app from one repo).
- Coolify project: same as the main site.
- Application name: `<client_code>-tracking` (e.g. `leticialang-tracking`).
- Build pack: Dockerfile (the sidecar has its own `Dockerfile`).
- Domain: `track.<primary_domain>` (e.g. `track.leticialang.exosmkt.com`).
- Env vars: same as the main site's server-only vars (`META_CAPI_TOKEN`, etc.) — duplicated, not shared. Coolify doesn't share env vars across apps in the same project.

The main Vite SPA's `lib/track.ts` POSTs to `https://track.leticialang.exosmkt.com/api/track` instead of `/api/track`.

CORS: the sidecar must accept POSTs from the primary domain. The shipped `server.ts` sets `Access-Control-Allow-Origin` to whatever's in `.env` as `CORS_ORIGIN` (e.g. `https://leticialang.exosmkt.com`).

## Adding a new Coolify app via API (sidecar)

There's a documented pattern in Gabriel's memory: `POST /api/v1/applications/private-github-app` with `instant_deploy:true` creates + deploys in one call. Faster than clicking through UI.

```bash
curl -X POST "https://coolify.exosmkt.com/api/v1/applications/private-github-app" \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_uuid": "<exos-project-uuid>",
    "server_uuid": "<server-uuid>",
    "environment_name": "production",
    "github_app_uuid": "<github-app-uuid>",
    "git_repository": "https://github.com/exosmkt/leticia-lang",
    "git_branch": "main",
    "ports_exposes": "3000",
    "name": "leticialang-tracking",
    "fqdn": "https://track.leticialang.exosmkt.com",
    "build_pack": "dockerfile",
    "dockerfile_location": "/tracking-sidecar/Dockerfile",
    "base_directory": "/tracking-sidecar",
    "instant_deploy": true
  }'
```

UUIDs are visible in Coolify URLs after clicking into the project/server/github-app.

## Verifying env vars are live

After deploy, smoke-test the endpoint:

```bash
curl -X POST "https://leticialang.exosmkt.com/api/track" \
  -H "Content-Type: application/json" \
  -d '{"name":"PageView","event_id":"test","event_time":1717000000,"event_source_url":"https://leticialang.exosmkt.com/"}'
# Expect: 204 No Content, with debug header X-Track-Status listing each platform's status
```

If 500 → env vars missing or wrong. SSH into the VPS and check the container logs:

```bash
ssh vps-exos
docker ps | grep leticialang
docker logs <container_id> --tail 50
```

## Rotating tokens

When a token leaks (or as periodic hygiene):

1. Generate new token in the platform UI.
2. Update env var in Coolify (replace value, save, redeploy).
3. Revoke old token in the platform UI.

The skill doesn't automate this — token rotation is a security operation that should be a deliberate human action.

## DNS wildcards (already configured)

Both VPSes have wildcard DNS configured:
- `*.exosmkt.com` → `187.127.30.29`
- `*.gabrielgouvea.com.br` → `187.127.2.180`

So creating a new subdomain (e.g. `track.leticialang.exosmkt.com`) doesn't require DNS changes — Coolify + Traefik handle SSL automatically on first deploy.

For client-owned domains (`leticialang.com.br` etc.), DNS is configured at the registrar to point at the VPS. Adding a new subdomain there is a manual step the user does at the registrar (Registro.br, GoDaddy, etc.).

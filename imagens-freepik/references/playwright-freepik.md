# Runtime Playwright para o Pikaso (Freepik)

Referência operacional do script `automation/run_freepik.py`. Vive aqui (não no SKILL.md) porque é detalhe de implementação — só carregar quando for debugar/estender o runtime.

## Pré-requisitos

```bash
pip install playwright pyyaml
playwright install chromium       # caso queira fallback p/ chromium puro
# Chrome real (channel="chrome") já existe em /Applications/Google Chrome.app no macOS
```

Credenciais em [credentials.local.json](../credentials.local.json) (gitignored):

```json
{ "freepik": { "email": "...", "password": "...", "loginUrl": "https://www.freepik.com/log-in", "pikasoUrl": "https://br.freepik.com/pikaso/ai-image-generator" } }
```

Profile persistente em `.playwright-profile/` (gitignored, criado no 1º run).

## Por que esses defaults (não mexer sem razão concreta)

| Default | Valor | Por quê |
|---|---|---|
| Cap por sessão | **30 submissões** | Bloqueio Freepik de 2026-05 aconteceu em sessão com ~36 cliques em ~5min. 30 deixa margem. |
| Cap por hora rolante | **60** | Bots típicos fazem 100+/h. Humano usando intensamente fica em 40-60/h. |
| Pausa entre submissões | **12-25s uniforme** | Humano lê o que digitou, revisa, clica gerar. Sub-10s = bot. |
| Break a cada 5-10 subs | **+30-90s extra** | Humano pausa pra checar resultado, conferir crédito, beber café. |
| Typing delay | **Gauss(μ=80ms, σ=30ms)** | 12 cps em média — datilografia rápida humana fica 8-15 cps. |
| Typing pause de "pensamento" | **5% chance, +0.5-2s** | Humano para no meio da frase às vezes. |
| Typo + correção | **3% chance** | Pequeno mas presente. |
| Mouse-move antes do click | **15-35 steps** | `page.mouse.move(x,y,steps=N)` interpola — sem N, teletransporta. |
| Click point | **20-80% do bbox** | Humano não clica exatamente no centro. |
| Pausa "lendo o prompt" antes do Gerar | **2-8s** | Tempo de olhar o que vai mandar. |
| Headless | **Sempre False** | Headless tem fingerprint detectável. Chrome real headed é o disfarce. |
| Channel | **`chrome`** | Chrome de verdade do macOS, não chromium for testing. |

Se o usuário pedir pra "ir mais rápido": **não negociar sem aprovação explícita**. A tabela de rationalizations no SKILL.md cobre isso.

## Setup do contexto stealth

```python
ctx = pw.chromium.launch_persistent_context(
    user_data_dir=str(PROFILE_DIR),
    channel="chrome",
    headless=False,
    viewport={"width": 1440, "height": 900},
    locale="pt-BR",
    timezone_id="America/Sao_Paulo",
    args=["--disable-blink-features=AutomationControlled"],
    ignore_default_args=["--enable-automation"],
)
ctx.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
""")
```

**Não usar `playwright-stealth` como dep externa** — adiciona pin instável; o tweak acima cobre ~95% dos checks comuns. Se Freepik subir defesa, considerar `playwright-stealth` numa segunda iteração.

## Login flow

Mesmas etapas do legacy (email-only → continuar → password → submit), agora:

```python
def login(page, creds):
    page.goto(creds["loginUrl"], wait_until="domcontentloaded")
    page.wait_for_selector('input[name="email"]', timeout=15_000)
    human_type(page, page.locator('input[name="email"]'), creds["email"])
    pause(0.3, 0.7)
    human_click(page, page.get_by_role("button", name=re.compile(r"continuar.*e.?mail", re.I)))
    page.wait_for_selector('input[name="password"]', timeout=15_000)
    pause(0.5, 1.2)
    human_type(page, page.locator('input[name="password"]'), creds["password"])
    pause(0.3, 0.7)
    human_click(page, page.locator("button#submit"))
    page.wait_for_url(re.compile(r"freepik\.com(?!.*log-in)"), timeout=30_000)
```

Profile persistente fará isso uma vez — sessões subsequentes pulam direto pro Pikaso.

## Seletores Pikaso (reutilizados do legacy)

```
[data-cy="image-prompt-input"] [contenteditable="true"]   # campo prompt (contenteditable)
[data-cy="tti-mode-selector-v3-trigger"]                  # trigger seletor modelo
[data-cy="ai-model-selector-show-all-button"]             # expandir lista modelos
[data-cy="ai-model-item-imagen-nano-banana-2"]            # Nano Banana Pro
[data-cy="image-aspect-ratio-input"]                      # trigger aspect (Radix popover)
[data-cy="image-resolution-input"]                        # trigger resolução
[data-cy="popover-option"]                                # opções de dropdown
[data-cy="generate-button"]                               # botão Gerar
[data-cy="sidebar-project-selector"]                      # projeto ativo (aria-label = nome UI)
[data-cy="projects-selector-menu"]                        # popover lista de projetos
[data-cy="header-current-project-link"]                   # link header (UUID do projeto)
[data-cy="feed-virtual-item"]                             # item do feed virtualizado
[data-cy="main-feed-gallery"]                             # container do feed
```

### Popover Radix — quirk

`.click()` JS NÃO abre popovers Radix-Vue. Em Playwright funciona com `locator.click()` real (passa por mouse-down/up), MAS é preciso humanizar antes:

```python
human_click(page, page.locator('[data-cy="image-aspect-ratio-input"]'))
page.wait_for_selector('[data-cy="popover-option"]', timeout=5_000)
opts = page.locator('[data-cy="popover-option"]')
target = opts.filter(has_text=re.compile(r"9.*16"))
human_click(page, target.first)
```

## Helpers de humanização (resumo)

| Helper | Função |
|---|---|
| `human_type(page, locator, text)` | Digita caractere a caractere com Gauss(80,30) + 5% pausa de pensamento + 3% typo-correção |
| `human_click(page, locator)` | Move mouse em 15-35 steps até ponto aleatório do bbox, pausa 0.1-0.4s, click |
| `human_mouse_to(page, locator)` | Só movimento (sem click) — usar entre ações pra mascarar gaps |
| `pause(min, max)` | `time.sleep(random.uniform(min,max))` |
| `inter_submission_pause(idx)` | 12-25s base + (a cada 5-10 subs) +30-90s break |

## Polling sem IA

Mesmo script JS contador do legacy, agora chamado via `page.evaluate()`:

```python
def poll_state(page):
    return page.evaluate("""
        () => {
          const items = [...document.querySelectorAll('[data-cy="feed-virtual-item"]')];
          let inflight = 0, queued = 0, done = 0;
          for (const el of items) {
            const t = el.textContent;
            if (/Gerando|Preparando/i.test(t)) inflight++;
            else if (/Na fila/i.test(t)) queued++;
            else {
              const imgs = [...el.querySelectorAll('img')].filter(im => im.naturalWidth > 0 || im.src).length;
              if (imgs > 0) done += imgs;
            }
          }
          return { inflight, queued, done };
        }
    """)
```

Intervalo: **15s + random 0-5s** (jitter pra evitar timing perfeitamente periódico). Convergência: `inflight==0 && queued==0` por 2 pools seguidos. Timeout: 15 min.

Para a contagem final (feed virtualizado), rolar o container até o fim e agregar por `data-index` — mesmo script `seen.set(idx, ...)` do legacy.

## Detecção de bloqueio

```python
BLOCK_PATTERNS = [
    r"captcha", r"verifica.*humano", r"verify.*human", r"bot.*detect",
    r"temporariamente.*bloquead", r"temporarily.*block",
    r"limite.*atingid", r"too many requests",
    r"cloudflare", r"challenge"
]

def detect_block(page):
    url = page.url.lower()
    if "/challenge" in url or "cf_chl_" in url or "/log-in" in url:
        return True, f"url:{url}"
    body = page.evaluate("() => document.body.innerText.toLowerCase().slice(0, 5000)")
    for pat in BLOCK_PATTERNS:
        if re.search(pat, body):
            return True, f"text:{pat}"
    return False, None
```

Chamar após **cada** submissão. Se True → screenshot em `.block_screenshots/<ts>.png`, statu `blocked`, **não retentar automaticamente**.

## State file `.session_state.json`

```json
{
  "session_id": "2026-05-20T14:35:00-03:00",
  "started_at": "2026-05-20T14:35:00-03:00",
  "last_activity_at": "2026-05-20T14:48:12-03:00",
  "submissions_this_session": 12,
  "submissions_log": [
    {"t": "2026-05-20T14:35:18-03:00", "label": "s1", "v": 1, "path": "..."},
    {"t": "2026-05-20T14:35:45-03:00", "label": "s1", "v": 2, "path": "..."}
  ],
  "last_block_detected": null,
  "cap_per_session": 30,
  "cap_per_hour": 60
}
```

Regras:
- Sessão "expira" após **30min de inatividade** (`last_activity_at` > 30min) → próximo run reseta `submissions_this_session` e começa nova `session_id`.
- `submissions_log` é truncado pra entradas das últimas 2h (suficiente pra checar cap por hora rolante).
- `last_block_detected` quando setado bloqueia novos runs por 60min como circuit-breaker.

## Schema do JSON de retorno (stdout, sempre na última linha)

```json
{
  "status": "converged | partial | cap_reached | blocked | needs_user_input | error",
  "path": "...",
  "project": { "requested_slug": "vhoe", "active_slug": "vhoe", "active_ui_name": "Vhoe.co" },
  "totals": { "expected": 18, "fired": 18, "skipped": 0, "errors": 0, "done": 18 },
  "by_label": { "s1": { "fired": 3, "done": 3 }, "s2": { "fired": 3, "done": 3 } },
  "duration_seconds": 487,
  "humanization": {
    "avg_typing_cps": 11.4,
    "avg_pause_between_subs_s": 17.2,
    "longest_pause_s": 73,
    "session_submissions_total": 18,
    "hourly_window_total": 22
  },
  "next_action": "run_on_complete | partial_retry | wait_then_resume | alert_user_blocked | ask_user",
  "remaining_labels": ["s7", "s8"],
  "resume_suggested_at_iso": "2026-05-20T15:05:00-03:00",
  "prompt_for_user": null,
  "block_evidence": null,
  "dry_run": false
}
```

`next_action` é o ponteiro pro Claude:
- `run_on_complete` → status `converged`, Claude executa hooks YAML (`move_to`, `update_indices`).
- `partial_retry` → status `partial` (alguns labels falharam mas não bloqueou); sugere `--only` em nova invocação.
- `wait_then_resume` → status `cap_reached`; Claude reporta a `resume_suggested_at_iso` ao usuário.
- `alert_user_blocked` → status `blocked`; **não** retentar; Claude alerta e para.
- `ask_user` → status `needs_user_input`; Claude mostra `prompt_for_user` e aguarda.

## Troubleshooting

| Sintoma | Diagnóstico | Ação |
|---|---|---|
| `playwright._impl._errors.Error: Executable doesn't exist` | Chrome canal não instalado | `playwright install chrome` ou ajustar `channel="chromium"` |
| `playwright` import errors | Não instalado no Python ativo | `pip3 install playwright` no Python certo |
| Chrome abre mas Pikaso pede login mesmo com profile | Cookies expiraram | Deletar `.playwright-profile/` e fazer login na primeira execução |
| `bounding_box()` retorna `None` no `human_mouse_to` | Elemento fora da viewport | `locator.scroll_into_view_if_needed()` antes |
| Botão Gerar fica disabled > 25s | Sessão pausada / loading | Tirar screenshot, reportar `error`, não retentar automaticamente |
| `detect_block` retorna True imediatamente após login | Cloudflare desafiando login | Pausa de 1h via `last_block_detected`; usuário precisa logar manual |
| Pikaso projeto target não existe no popover | Renomeação / nova conta | Status `needs_user_input` com prompt: criar / outro / cancelar |
| Polling não converge em 15min | Geração travada no servidor | Reportar status `partial`, atualizar `by_label` com `done` parcial |
| Estado parece corrompido | `.session_state.json` mal formado | Script trata como sessão nova; usuário pode deletar manualmente |

## Como o Claude orquestra

Claude **não** chama a UI nem o browser. Só:

1. Roda `python automation/run_freepik.py <md> [flags]` via `Bash`.
2. Lê o JSON final do stdout.
3. Decide próxima ação baseado em `next_action`:
   - `run_on_complete` → executa `move_to` + `update_indices` do YAML (responsabilidade do Claude, não do script).
   - `wait_then_resume` → reporta ao usuário, sugere nova invocação com `--only <remaining_labels>` após `resume_suggested_at_iso`.
   - `alert_user_blocked` → mostra `block_evidence`, para tudo.
   - `ask_user` → mostra `prompt_for_user`.

Nenhum print ANSI/log do script vai pro Claude — só o JSON final. Logs intermediários vão pro stderr e não atrapalham o parse.

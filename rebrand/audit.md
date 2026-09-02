# Rebrand audit — upstream hermes-agent @ main (2026-09-01)

Raw data in `rebrand/audit/`:
`files-with-hits.txt`, `tokens.txt`, `env-vars.txt`, `urls.txt`,
`model-and-repo-ids.txt`, `paths-with-hermes.txt`, `images-sha256.txt`.

## Headline numbers

| Metric | Count |
|---|---|
| Files containing `hermes` or `nous` (text, excl. node_modules/.git) | 6,566 |
| Lines containing `hermes` or `nous` | 93,459 |
| Distinct `HERMES_*` env vars | 637 |
| Files/dirs with `hermes` in the **name** | 123 |
| Image/media assets in tree | 70 |
| Python test files | 3,626 |
| Upstream commits (history kept) | 26,982 |

Word-bounded `nous` hits: 7,790 of 10,838 raw hits. The rest are false
positives (`synchronous`, `asynchronous`, `monotonous`, `luminous`,
`PYTHONNOUSERSITE`). **The codemod must use word boundaries for `nous`.**

## Hits by area (files)

desktop 1,162 · hermes_cli 807 · docs 433 · gateway 393 · tools 345 ·
i18n 315 · agent 268 · src 244 · creative 125 · run_agent 109 · cli 104 ·
platforms 87 · plugins 80 · cron 77 · tui_gateway 71 · model-providers 57.

## Classification of tokens

### A. Rename (product identity)
- Package/command: `hermes-agent`, `hermes`, `hermes-cli`, `hermes-gateway`, `hermes-acp`, `hermes.exe`
- Python modules: `hermes_cli/`, `hermes_state*.py` (7 files), `hermes_constants.py`, `hermes_logging.py`, `hermes_time.py`, `hermes_bootstrap.py`, `hermes_startup_watchdog.py`, `agent/transports/hermes_tools_mcp_server.py`, `./hermes` launcher, `setup-hermes.sh`
- Config root: `~/.hermes`, `%LOCALAPPDATA%\hermes`, `HERMES_HOME`, `hermes_home` / `get_hermes_home` / `_hermes_home` helpers (~8k occurrences)
- Env vars: all 637 `HERMES_*` → `REIGN_*`
- TS/JS: `@hermes/ink`, `@hermes/shared` npm scopes, `hermes-tui`, `hermesDesktop` / `window.hermesDesktop` (349), `hermesApi`, `HermesCLI`, `HermesGateway`, `ai.hermes.gateway` (bundle id), `com.nousresearch.hermes` (appId)
- Docker: image `hermes-agent`, container `hermes`, user `hermes`, `/opt/hermes`, s6 service `main-hermes`
- Nix: `nix/hermes-agent.nix`
- Prose: "Hermes Agent", "Hermes", "Nous Research" (as builder), tagline
- `SOUL.md` first line: "You are Hermes Agent, built by Nous Research." — **this is a persona/system-prompt string**; decision 11 says persona untouched, but the *name* must change. Rename only the identity phrase.
- Locales: 17 of `locales/*.yaml` carry "Hermes" strings (en: 13 lines)
- `website/i18n/zh-Hans/` mirrors docs in Chinese (315 files) — rename or drop (see decisions needed)

### B. Keep — model identifiers (allowlist)
`Hermes-4`, `hermes-4-405b`, `Hermes-4-70B`, `Hermes-4.5`, `Hermes-4.3-36B-Q5_K_M`,
`hermes-4-mini`, `hermes-3`, `hermes-3-llama-3.1-70b/8b/405b`,
`NousResearch/Hermes-3-Llama-3.1-70B`, `nousresearch/hermes-4-405b`, `hermes2`, `hermes3`.
Also **Nous Portal** provider integration (`NousPortalAdapter`, `NousCloud`,
`NousProfile`, `portal.nousresearch.com`, `inference-api.nousresearch.com`) —
this is an inference *provider* like OpenRouter, keep functional.

### C. Keep — URLs (decision 8, separate allowlist)
`hermes-agent.nousresearch.com` (335), `github.com/NousResearch/hermes-agent` (~750),
`portal.nousresearch.com`, `inference-api.nousresearch.com`, `discord.gg/NousResearch`,
`hub.docker.com/r/nousresearch/hermes-agent`, `NousResearch/hermes-example-plugins`,
`NousResearch/hermes-plugin-index`.

### D. Keep — legal / provenance
`LICENSE`, `contributors/emails/*` (git identity data, not branding), git history.

### E. Manual (not codemod-able)
- `hermes_cli/banner.py`: `HERMES_AGENT_LOGO` (gold ASCII), `HERMES_CADUCEUS` hero art
- `ui-tui/src/banner.ts` `LOGO_ART`; `ui-tui/src/components/branding.tsx` taglines (lines 57–59, 358, 390)
- `hermes_cli/skin_engine.py`: `default` skin "Classic Hermes — gold and kawaii", `(^_^)?` help headers in all four skins, `⚕` caduceus glyphs in goodbye/response_label
- Wake word: `tools/wakewords/hey_hermes.{onnx,tflite}` — trained models for the phrase "hey hermes". **Cannot be renamed by string replace.** Options: keep the model but label it, ship without a bundled wake word, or train a "hey reign" model later.
- Images (section below)

## Image assets to replace (anime mascot / Hermes identity)

| Path | What it is |
|---|---|
| `assets/banner.png`, `website/static/img/hermes-agent-banner.png` | README/docs banner (12 KB, identical) |
| `website/static/img/logo.png` (1.3 MB), `website/static/img/nous-logo.png` | Anime girl with "N" collar; Nous logo |
| `website/static/img/favicon.{ico,svg}`, `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png` | Docs favicons |
| `web/public/favicon.ico` | Dashboard favicon |
| `apps/desktop/assets/icon.{icns,ico,png}`, `apps/desktop/public/apple-touch-icon.png` | Desktop app icons |
| `apps/desktop/public/hermes.png`, `hermes-sprite.png`, `hermes-frames/hermes-frame-{0..7}.png`, `nous-girl.jpg` | Animated pixel-art Hermes mascot (winged helmet + caduceus) and anime girl avatar |
| `apps/desktop/src/components/pet/pet-egg-sheet.png` | Desktop "pet" feature sprite sheet |
| `apps/desktop/public/ds-assets/filler-bg0.jpg` (3.9 MB) | Background art — inspect |
| `apps/bootstrap-installer/public/nous-girl.jpg`, `src-tauri/icons/*` | Tauri installer avatar + icons |
| `plugins/hermes-achievements/docs/assets/*.png` | Plugin screenshots (Hermes UI) |
| `website/static/img/dashboard/*`, `docs/dashboard-models/*`, `kanban-tutorial/*` | ~25 doc screenshots of the Hermes UI — re-shoot after rebrand or leave |
| `apps/desktop/src/assets/tiers/feature-*.webp` | Feature tier illustrations — inspect |

Neutral (keep): `gateway/assets/telegram-botfather-threads-settings.jpg`,
`optional-skills/security/unbroker/assets/unbroker.png`, `website/static/img/docs/*.svg`.

Inline base64 images in source are test fixtures / vision-tool samples, not branding.

## Surfaces not in the original plan (discovered)
1. `apps/bootstrap-installer/` — Tauri desktop installer with its own icons and avatar.
2. Desktop mascot/pet system — animated sprite frames + `pet/` component. Needs new art or feature removal.
3. `plugins/hermes-achievements/` — plugin dir named after Hermes.
4. Wake-word models (`hey_hermes`).
5. `locales/*.yaml` (17 languages) and `website/i18n/zh-Hans/` (315 files).
6. `SOUL.md` identity line.
7. `nix/`, `flake.nix` packaging.
8. `contributors/` — leave.
9. Stray tracked junk: `apps/desktop/'/var/folders/.../hermes-update-mutex-*` (upstream accident) — delete.

## Baseline
- `uv sync --extra dev` → Python 3.11.15, pytest 9.1.1. OK.
- `ui-tui`: `npm ci` + `npm run build` → `dist/entry.js` (3.6 MB). OK.
- Full test suite: 42,244 passed / 59 host-specific failures after installing CI extras. See `rebrand/audit/baseline-tests-run{1,2}.txt` and `baseline-known-failures.txt`.

# Reign — Rebranding Plan (Hermes Agent → Reign by Rook)

Status: DECISIONS LOCKED — ready to start Phase 1. No code changes yet.
Upstream: https://github.com/NousResearch/hermes-agent (MIT)
Target: `reign` — Rook's branded AI agent. Tagline: "In Your Corner".

---

## 1. Decisions (locked 2026-09-01)

| # | Question | Decision |
|---|---|---|
| 1 | Strategy | **Hard fork + scripted codemod.** |
| 2 | Upstream pin | **Latest `main`** at clone time; record the commit SHA in `rebrand/UPSTREAM.md`. |
| 2b | Git history | **Keep upstream history, as a standalone repo (not a GitHub "fork").** See rationale below. |
| 3 | Names | CLI `reign`, config dir `~/.reign`, env `REIGN_HOME` / `REIGN_*`, package `reign`, Docker `reign`. |
| 4 | Brand assets | In `brand/`: `Imagemark for embroidery.svg` (circle mark, single path), `Rook Imagemark.ai`, `Rook Logo With Strap.ai`, `Imagemark for embroidery.ai`. `.ai` files are PDF-compatible; convert to SVG/PNG in Phase 0. Palette assumed monochrome: `#000000` / `#FFFFFF`. Wordmark is used as an image, so no typeface needed in code. |
| 5 | Tagline | **"In Your Corner"** |
| 6 | Skins | Keep `ares` / `mono` / `slate` **if** they only change colors/spinner text. Any skin that carries Hermes imagery, kawaii faces, or Hermes naming gets neutralized or dropped. Audit decides. New `rook` skin is the default. |
| 7 | Local install | **Do not touch the local `~/.hermes` install.** All dev/testing runs isolated (Docker or `REIGN_HOME` pointed at a scratch dir). Deliverable for v0.1 is a GitHub repo; user will provide the repo link when ready. |
| 8 | Upstream links | **Leave Nous/Hermes URLs in place** (docs site, GitHub, Docker Hub) rather than substituting Rook ones. See caveat below. |
| 9 | License | Keep the Nous MIT notice in `LICENSE`; add Rook copyright line above it and a short `NOTICE` crediting Hermes Agent. No attempt to hide provenance. |
| 10 | Trims | **Drop non-English `CONTRIBUTING.*.md`.** Everything else stays. |
| 11 | Persona | **Visual and naming only.** System prompt / personality untouched in v0.1. |

### Rationale: keep history, standalone repo
- Keeping history preserves attribution, keeps `git blame` useful on a ~23k-LOC core, and lets us `git merge upstream/main` later with rename detection doing some of the work.
- Pushing to a fresh repo (not using GitHub's fork button) avoids the "forked from NousResearch/hermes-agent" badge on the repo page and keeps Issues/Actions settings independent.
- We add `upstream` as a remote so future syncs are possible. Realistically, after the module renames, syncs will be "re-run the codemod on a new upstream checkout and diff", not clean merges. The codemod design accounts for that.

### Caveat on decision 8 (leaving Nous links)
Leaving URLs like `hermes-agent.nousresearch.com` means the literal string
"hermes" survives in help text, README, and docs, and any client who clicks a
docs link in the product lands on Nous's site. That is acceptable per your
call. To keep this controllable, the codemod treats URLs as a **separate
allowlisted category**, so flipping to Rook-hosted links later is a one-line
mapping change. Recommendation for v0.1: leave links in `README`/`NOTICE`/docs
as-is, but audit any link that appears **inside the running product** (CLI
help, TUI, dashboard, gateway welcome messages) and flag those for a decision
— those are the ones a client will actually click.

## 2. What we are forking

| Surface | Location | Stack | Branding present |
|---|---|---|---|
| Agent core / CLI | `run_agent.py`, `cli.py`, `hermes_cli/`, `hermes_state.py`, `hermes_constants.py`, `hermes_logging.py` | Python | Module names, `~/.hermes`, `HERMES_HOME`, `hermes` command, help text |
| Skin engine | `hermes_cli/skin_engine.py` | Python + YAML | Built-in skins `default` (gold/kawaii), `ares`, `mono`, `slate`; spinner faces, banner colors, `agent_name`, welcome/goodbye, tagline |
| TUI | `ui-tui/` (Ink/React, TypeScript) + `tui_gateway/` (Python) | TS + Python | Hardcoded `LOGO_ART` in `ui-tui/src/banner.ts`; tagline + fallback "NOUS HERMES" in `ui-tui/src/components/branding.tsx` (upstream issue #25704 confirms these ignore config) |
| Web dashboard | `web/` | React | Logo, favicon, page titles, embedded TUI via `hermes_cli/pty_bridge.py` |
| Desktop app | `apps/desktop/` | Electron + React | App name, bundle id, icons (`.icns`, `.ico`, `.png`), window titles |
| Docs site | `website/` | Docusaurus | Site title, logo, favicon, social card, every doc page |
| Messaging gateway | `gateway/` | Python | Bot display names, welcome messages, help text on Telegram/Discord/Slack/WhatsApp/Signal/Email |
| Packaging | `pyproject.toml`, `package.json`, `docker/`, compose files, `scripts/` | — | PyPI name, Docker image `nousresearch/hermes-agent`, install scripts, `uv` entry point |
| Repo docs | `README.md`, `AGENTS.md`, `CONTRIBUTING*.md`, `assets/banner.png` | Markdown | Banner image, anime mascot artwork, Nous links |
| Tests | ~900 files / ~17k tests via `scripts/run_tests.sh` | pytest | Hardcoded `hermes` paths, names, and fixtures |

## 3. Rename mapping

| Upstream | Reign | Notes |
|---|---|---|
| `hermes` (CLI command) | `reign` | |
| `hermes-agent` (package / repo / Docker) | `reign` | |
| `~/.hermes`, `%LOCALAPPDATA%\hermes` | `~/.reign`, `%LOCALAPPDATA%\reign` | No migration helper in v0.1 (decision 7) |
| `HERMES_HOME` and any `HERMES_*` env vars | `REIGN_HOME`, `REIGN_*` | Full list comes from the audit |
| `hermes_cli/`, `hermes_state.py`, `hermes_constants.py`, `hermes_logging.py` | `reign_cli/`, `reign_state.py`, `reign_constants.py`, `reign_logging.py` | Module renames + all imports + tests |
| `tui_gateway/` | keep | No brand in name |
| "Hermes Agent" / "Hermes" (prose) | "Reign" | Excluding model names and URLs |
| "Nous Research" (prose, product copy) | "Rook" | Excluding LICENSE, NOTICE, URLs |
| "Messenger of the Digital Gods" | "In Your Corner" | |
| `LOGO_ART` ASCII "HERMES-AGENT" | ASCII "REIGN" (+ optional ♜ glyph) | Generate with pyfiglet; pick a font with the weight of the Rook wordmark |
| Skin `default` (gold/kawaii) | Skin `rook` (black/white), set as default | Kawaii faces → neutral spinner |
| `assets/banner.png` + mascot art | Rook circle mark + wordmark-with-strap | Generated from `brand/` |
| `CONTRIBUTING.<lang>.md` | deleted | Decision 10 |

### Exclusions (must NOT be renamed)
- **Model identifiers.** "Hermes" is also Nous's model family (`Hermes-3-*`, `Hermes-4-*`, etc.). Provider/model config strings are preserved. Codemod carries an allowlist built during audit.
- **URLs** to Nous / Hermes properties (decision 8). Separate allowlist category so it can be flipped later.
- **`LICENSE`** (MIT notice stays) and **`NOTICE`** (credits Hermes Agent by name).
- **Third-party package names** in `pyproject.toml` / lockfiles that happen to contain "hermes".
- **Git history.**

## 4. Brand assets and derivatives

Source of truth: `brand/` (already in repo root).

Phase 0 generates into `brand/generated/` (script: `rebrand/gen_assets.py`, using
`pdftocairo`/`inkscape` for `.ai` → SVG/PNG and Pillow or `iconutil`/`png2icns`
for icon packs):

| Derivative | From | Used by |
|---|---|---|
| `rook-mark.svg`, `rook-mark-{16..2048}.png` | `Rook Imagemark.ai` (black disc, white rook) | Primary mark: app icons, dashboard logo, banner |
| `rook-mark-white-*.png` (luminance-inverted: white disc, black rook) | same | Dark backgrounds, social card |
| `rook-mark-outline.svg`, `rook-mark-outline-{16..1024}.png`, `-white-` variants | `Imagemark for embroidery.ai/.svg` (thin ring, solid rook) | Small sizes: favicon 16/32, TUI glyph, status bar. Reads better than the disc under ~64px |
| `rook-logo-strap-black.svg/.png`, `rook-logo-strap-white.svg/.png` | `Rook Logo With Strap.ai` | README hero, docs navbar, desktop About |
| `favicon.ico` (multi-size), `favicon.svg` | mark PNGs | `web/public/`, `website/static/img/` |
| `icon.icns`, `icon.ico`, `icons/*.png` | mark PNGs | `apps/desktop/` |
| `banner.png` (README hero: mark + wordmark + "In Your Corner") | composed | `assets/banner.png` |
| `social-card.png` (1200×630) | composed | Docusaurus |

Expected upstream image touchpoints to replace (confirmed by audit):
`assets/`, `web/public/`, `website/static/img/`, `apps/desktop/` resources,
inline SVG/base64 in React components, and text-art spinner faces in
`skin_engine.py`.

## 5. Phases

### Phase 0 — Setup (DONE 2026-09-01)
- [x] Plan agreed.
- [x] Brand sources in `brand/`.
- [x] Convert `.ai` → SVG; generate derivative set (section 4) via `rebrand/gen_assets.py` → `brand/generated/`.
- [x] Tooling: `uv` 0.12.8 and `poppler` 26.08 installed with the **native ARM Homebrew** (`/opt/homebrew/bin/brew`). Note: this Mac also has an Intel Homebrew at `/usr/local` that shadows `brew` on PATH and compiles from source under Rosetta — always call `/opt/homebrew/bin/brew` explicitly. `pyfiglet` + Pillow live in a scratch venv, not system Python.
- [x] Target repo confirmed: `asxi9832/reign` (private, only a stub README on `main`; will be replaced at Phase 5).

### Phase 1 — Clone and audit (DONE 2026-09-01)
Results in `rebrand/audit.md` (summary) and `rebrand/audit/` (raw data). Provenance in `rebrand/UPSTREAM.md`.
Upstream history kept (26,982 commits); remotes: `upstream` = Nous, `origin` = asxi9832/reign.

Baseline environment: Python 3.11.15 venv via `uv sync --locked --python 3.11 --extra all --extra dev --extra anthropic --extra mistral --extra fal --extra modal --extra daytona --extra hindsight --extra parallel-web` (same set as upstream CI). `ui-tui` `npm ci && npm run build` OK.

Baseline tests (`scripts/run_tests.sh -j 6`, ~35 min for the full suite on this Mac):

| Run | Files | Passed | Failed | Skipped |
|---|---|---|---|---|
| 1: dev extra only | 3,589 | 42,244 | 245 | 440 |
| 2: rerun of the 130 failed files with CI extras | 130 | 3,791 | 59 | 66 |

Net baseline: **59 pre-existing failures in 24 files**, all host-specific (systemd/launchd service tests, git self-update tests, a few that observe the live Hermes desktop app running on this Mac). Recorded in `rebrand/audit/baseline-known-failures.txt`. **Phase 4 passes when the failure set is a subset of this list**, not when it is zero. Upstream CI runs Linux and Windows lanes we do not replicate locally.

Original Phase 1 checklist:

Original Phase 1 checklist:
- Clone `NousResearch/hermes-agent` `main` into `rook-reign/` (this directory; move `brand/` and this plan into it, or clone alongside then merge). Add `upstream` remote. Record SHA in `rebrand/UPSTREAM.md`.
- Full audit: `grep -rniE 'hermes|nous' --exclude-dir=node_modules --exclude-dir=.git` plus an image inventory (path, size, sha256). Output → `rebrand/audit.md` with per-directory counts and classification: **rename / model-name / url / license / manual**.
- Build model-name and URL allowlists from the audit.
- Inspect each built-in skin for imagery/naming (decision 6).
- Baseline: `npm run build` in `ui-tui/`, `scripts/run_tests.sh` in Docker or with `HERMES_HOME` pointed at a scratch dir. Must be green before any change.

### Phase 2 — Codemod
- `rebrand/rebrand.py` driven by `rebrand/mapping.yaml`: ordered, case-aware replacements (`hermes-agent`→`reign` first, then `Hermes Agent`→`Reign`, `hermes`→`reign`, `Hermes`→`Reign`, `HERMES`→`REIGN`, `Nous Research`→`Rook`, tagline), with allowlists for model names, URLs, LICENSE/NOTICE, lockfiles, and binaries.
- Python module/dir renames via `git mv`; import rewrite; test path fixes.
- `pyproject.toml`, `package.json`, Docker files, compose, install scripts, entry points → `reign`.
- Delete `CONTRIBUTING.<lang>.md`.
- Add `NOTICE`; prepend Rook line to `LICENSE`.
- Script must be idempotent and re-runnable on a fresh upstream checkout.

### Phase 3 — Manual branding surfaces
- TUI: replace `LOGO_ART`, tagline, small-terminal fallback; route everything through `agent_name` so nothing stays hardcoded.
- Skin engine: add `rook` skin (black/white), make it default, remove kawaii faces; neutralize or drop other skins per audit.
- Web dashboard: logo, favicon, `<title>`, empty states.
- Desktop app: product name, bundle id, icons, About dialog.
- Docs site: title, logo, favicon, social card, landing copy, sidebar labels. Nous URLs stay.
- Gateway: bot names, welcome/help text per platform. Flag any in-product Nous links for decision (section 1 caveat).
- README / AGENTS.md: rewrite hero and install instructions to `reign`.

### Phase 4 — Verification
- Zero-hit check: `grep -rniE 'hermes|nous'` returns only allowlisted lines (model names, URLs, LICENSE, NOTICE). Report the residual list explicitly.
- Image check: no upstream image hashes from the audit inventory remain.
- Rebuild TUI, web, desktop, docs. Screenshot every surface: CLI banner, TUI, dashboard, desktop, docs home, one gateway welcome message.
- Full test suite green.
- Fresh-install smoke test in Docker: `reign setup`, `reign model`, `reign gateway`. Never against the local `~/.hermes`.

### Phase 5 — Handoff
- Push to the Rook GitHub repo (link to be provided). Tag `v0.1.0`.
- `rebrand/UPSTREAM.md` documents the upstream SHA and the exact command to re-run the codemod for a future sync.

## 5b. Audit findings that change the plan (2026-09-01)

Scale: 6,566 files / 93k lines mention hermes or nous; 637 distinct `HERMES_*` env vars; 123 paths carry `hermes` in the name; 70 image assets. Full detail in `rebrand/audit.md`.

**Codemod rules added**
- `nous` must be matched with word boundaries: 3k hits are `synchronous`/`asynchronous`/`monotonous`/`luminous`/`PYTHONNOUSERSITE`.
- Nous Portal is an inference *provider* integration (`hermes_cli/nous_account.py`, `portal_cli.py`, `NousPortalAdapter`, `NousCloud`, `NousProfile`). Keep functional and out of the prose rename; only its user-facing label is reviewed in Phase 3.
- npm scopes `@hermes/ink` and `@hermes/shared` and the `hermesDesktop` window API rename with the codemod (affects `package-lock.json` files, regenerate rather than edit).
- Delete tracked junk `apps/desktop/'/var/folders/.../hermes-update-mutex-*` (upstream accident).
- `SOUL.md` opens with "You are Hermes Agent, built by Nous Research." Decision 11 keeps the persona, but the identity phrase becomes "You are Reign, built by Rook." Nothing else in SOUL.md changes.

**Surfaces added to Phase 3**
- `apps/bootstrap-installer/` (Tauri): `src/components/brand-mark.tsx`, `public/nous-girl.jpg`, `src-tauri/icons/*`, `hermes-setup.manifest`.
- Desktop mascot: `apps/desktop/src/components/brand-mark.tsx`, animated pixel-art Hermes sprite (`public/hermes-frames/*`, `hermes-sprite.png`, `hermes.png`), anime avatar `nous-girl.jpg`.
- `plugins/hermes-achievements/` directory rename plus its screenshot assets.
- `locales/*.yaml` (17 languages carry "Hermes" strings) — codemod handles.
- Skins: 9 built-ins, not 4 (`default`, `ares`, `mono`, `slate`, two light themes, ocean, sisyphus, volcanic). None carry imagery; they carry colors, `(^_^)?` help headers, and `⚕` caduceus glyphs. Per decision 6: keep all, strip Hermes naming/glyphs/kawaii faces, add `rook` as default.
- `hermes_cli/banner.py` holds two hand-drawn art blocks: `HERMES_AGENT_LOGO` (gold block letters) and `HERMES_CADUCEUS` (braille-art caduceus). Both replaced.

**Decisions needed from Joel** (defaults in brackets; proceeding with defaults unless told otherwise)
- D1. Desktop **pet / mascot feature**: **DECIDED (Joel, 2026-09-02): leave it.** Feature and its pixel-art sprite stay as-is; audience is professional office workers, low priority. Note: the sprite is a winged-helmet Hermes character with a caduceus, so the pet remains Hermes-themed. File references still rename (`hermes-frames/` → `reign-frames/` etc.) so the tree stays consistent; only the artwork is untouched. Candidate for a pixel-art rook later.
- D2. **Wake word.** `hey_hermes.{onnx,tflite}` are openWakeWord models trained by upstream from synthetic TTS speech (no human recordings). Two ways to get "hey Reign":
  - **(a) Zero training, ship in v0.1:** `tools/wake_word.py` already has a `sherpa` engine (sherpa-onnx open-vocabulary keyword spotting) that detects *any typed phrase* against a 13 MB model downloaded once. Make `provider: sherpa` and `phrase: "hey reign"` the defaults, drop the `hey_hermes` model files. Trade-off: slightly higher false-trigger rate than a purpose-trained model, and a one-time download on first use instead of working offline out of the box.
  - **(b) Train `hey_reign` with openWakeWord (~half a day):** the openWakeWord training notebook generates synthetic clips for the phrase with Piper TTS, augments them, and trains a small classifier; roughly 1–2 hours on a free Colab GPU plus tuning against false positives, output is a drop-in `.onnx` + `.tflite` pair (~200 KB each). No recordings needed; Apache-2.0 so redistribution is fine.
  - **DECIDED (Joel, 2026-09-02): (a), zero-training sherpa default with phrase "hey reign"; drop the `hey_hermes` model files.** A trained model via a partner is a future option if the feature gets real use.
- D3. **Chinese docs mirror** `website/i18n/zh-Hans/` (315 files): **DECIDED: remove.** Also remove `README.es.md`, `README.zh-CN.md`, `README.ur-pk.md`, `SECURITY.es.md`, `CONTRIBUTING.es.md`, and the `i18n` locale entry in `website/docusaurus.config.ts`. The runtime `locales/*.yaml` (UI strings in 17 languages) are a product feature, not docs, and stay.
- D4. **~25 documentation screenshots** of the Hermes dashboard/kanban UI under `website/static/img/`: **DECIDED: leave them.** Not re-shot in v0.1.
- D5. `apps/desktop/public/ds-assets/filler-bg0.jpg` (3.9 MB) is a blue-tinted classical Greek engraving (statue and swordsman on steps). No Hermes mark, but it carries the Greek-mythology theme. **DECIDED: replace with a subdued white Rook imagemark** (large, low-opacity white mark on the dark background, generated from `brand/generated/rook-mark-white-2048.png` at ~6-8% opacity, same 1440×1440 dimensions so the CSS needs no change). The four `src/assets/tiers/feature-*.webp` tiles (128 px) are the same blue-engraving style, no Hermes marks [default: keep in v0.1, restyle later]. `components/pet/pet-egg-sheet.png` is a generic egg-hatch sprite with no branding [keep].

## 6. Remaining open items
- GitHub repo URL for push: https://github.com/asxi9832/reign (provided 2026-09-01).
- In-product Nous links: decide keep vs. replace once the audit lists them (section 1 caveat).
- Brand hex colors / typeface: none supplied; proceeding monochrome. Supply if Rook has an official accent color for the `rook` skin.

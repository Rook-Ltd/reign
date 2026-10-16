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
- [x] Target repo confirmed: `rook-ltd/reign` (private, only a stub README on `main`; will be replaced at Phase 5).

### Phase 1 — Clone and audit (DONE 2026-09-01)
Results in `rebrand/audit.md` (summary) and `rebrand/audit/` (raw data). Provenance in `rebrand/UPSTREAM.md`.
Upstream history kept (26,982 commits); remotes: `upstream` = Nous, `origin` = rook-ltd/reign.

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

### Phase 2 — Codemod (DONE 2026-09-02)
Implemented as `rebrand/rebrand.py` + `rebrand/mapping.yaml` (`--dry-run`, apply, `--check`). Idempotent; a second run is a no-op.

| Result | Count |
|---|---|
| Paths deleted (non-English docs, zh-Hans mirror, junk mutex paths, wake-word models) | 8 (325 files) |
| Files rewritten | 5,973 |
| Files renamed via `git mv` | 1,545 |
| Residual hermes/nous lines after allowlist | ~75 in 19 files, all reviewed: test-fixture URLs, third-party links, Nous Portal OAuth codes, docs community-stories data |

Lockfiles regenerated: `uv.lock` (project now `reign`), root / website / photon sidecar / whatsapp-bridge `package-lock.json`. `uv sync` installs `reign`, `reign-agent`, `reign-acp` entry points. TUI rebuilt with `@reign/ink`, zero hermes strings in `dist/entry.js`.

Notes for Phase 3 that came out of the codemod:
- `pyproject` scripts: upstream had `hermes` and `hermes-agent`; both mapped to `reign`, so the second is now `reign-agent = run_agent:main`.
- `apps/desktop/package.json` maintainer still reads `Rook <support@nousresearch.com>` (email was protected). Fix by hand.
- `website/docusaurus.config.ts` still declares the `zh-Hans` locale whose files were deleted. Remove the i18n entry.
- `tools/wake_word.py` defaults still point at the deleted `hey_reign` openWakeWord model. Switch default provider to `sherpa`, phrase `hey reign`, and fix `tests/tools/test_wake_word.py` expectations.
- `README.md` line ~165 and docs still link to `hermes-agent.nousresearch.com/docs` (decision 8). Review in-product links.
- `website/src/data/userStories.json` is Nous community marketing content linking to the Nous Discord archive. Decide keep/remove with the docs landing page.
- Telegram managed-bot test fixtures embed `?name=Hermes+Agent` deep links; if the code builds that from the agent name, Phase 4 will show it.
- Three binary assets still carry Nous names and content: `apps/bootstrap-installer/public/nous-girl.jpg`, `apps/desktop/public/nous-girl.jpg`, `website/static/img/nous-logo.png`. Replaced in Phase 3 with the image pass.

Original Phase 2 checklist:
- `rebrand/rebrand.py` driven by `rebrand/mapping.yaml`: ordered, case-aware replacements (`hermes-agent`→`reign` first, then `Hermes Agent`→`Reign`, `hermes`→`reign`, `Hermes`→`Reign`, `HERMES`→`REIGN`, `Nous Research`→`Rook`, tagline), with allowlists for model names, URLs, LICENSE/NOTICE, lockfiles, and binaries.
- Python module/dir renames via `git mv`; import rewrite; test path fixes.
- `pyproject.toml`, `package.json`, Docker files, compose, install scripts, entry points → `reign`.
- Delete `CONTRIBUTING.<lang>.md`.
- Add `NOTICE`; prepend Rook line to `LICENSE`.
- Script must be idempotent and re-runnable on a fresh upstream checkout.

### Phase 3 — Manual branding surfaces (DONE 2026-09-17)
- CLI: `REIGN_AGENT_LOGO` is a 38-col ANSI Shadow "REIGN"; the caduceus hero is now `REIGN_HERO`, the Rook mark in braille (art sources in `rebrand/art/`). Logo shows from 40 columns instead of 95. Kawaii text faces `(^_^)`, `(x_x)`, `(o_o)` etc. across `cli.py`, `reign_cli/cli_commands_mixin.py`, `gateway/run.py` replaced with neutral glyphs; hand-padded box titles re-balanced.
- Skins: `default` is now the Rook monochrome palette (white/silver/grey on dark, black/charcoal/grey on light) with `rook` registered as an alias; neutral spinner glyphs replace the kawaii faces in both the skin and the `agent/display.py` fallbacks; `(^_^)?` help headers → `[?]`; `⚕` → `♜`. Other built-in skins kept (they carry no imagery).
- TUI (`ui-tui/src`): same logo/hero art, monochrome default seeds, help header `♜ Commands`. 1,737 vitest tests pass; bundle has zero Hermes/caduceus strings.
- Images (`rebrand/place_images.py`, re-runnable): README/docs banner, docs logo + favicons + social image, dashboard favicon, Electron `.icns/.ico/.png`, apple-touch icons, Tauri installer icon set, both `brand-mark.tsx` components now load `rook-mark.png`. Deleted: `nous-girl.jpg` (x2), `nous-logo.png`, unused mascot sprite/frames. Desktop backdrop `filler-bg0.jpg` is the outline mark on white (rendered at 2.5% opacity by the app).
- Docs/repo: README hero rewritten (no caduceus, no dead language badges, plain "Built by Rook" badge, Credits section); `NOTICE` added; `LICENSE` gains a Rook line above the Nous notice; Docusaurus tagline "In Your Corner", `zh-Hans` locale removed, footer "Reign by Rook · Built on Hermes Agent (MIT)". Docs site builds clean.
- Wake word: default provider `sherpa`, phrase "hey reign", no bundled model; openwakeword without a model path fails with a clear message. 29 tests pass.
- Corrections to codemod over-reach found here: nested third-party `LICENSE` copyright lines restored to Nous Research (and now excluded in `mapping.yaml`); dashboard OAuth provider label restored to "Nous Portal" (code + docs anchors); web dashboard `brandShort` "HA" → "RG"; achievement share text `☤` → `♜`.
- Left as-is per decisions: in-product links to `hermes-agent.nousresearch.com` docs and install scripts (full list in `rebrand/audit/urls.txt`), the Nous community "user stories" docs page, docs screenshots of the old UI, the pet feature, `SECURITY.md` disclosure contact `security@nousresearch.com` (**flag: reports would go to Nous — decide whether to point this at a Rook address**).

Original Phase 3 checklist:
- TUI: replace `LOGO_ART`, tagline, small-terminal fallback; route everything through `agent_name` so nothing stays hardcoded.
- Skin engine: add `rook` skin (black/white), make it default, remove kawaii faces; neutralize or drop other skins per audit.
- Web dashboard: logo, favicon, `<title>`, empty states.
- Desktop app: product name, bundle id, icons, About dialog.
- Docs site: title, logo, favicon, social card, landing copy, sidebar labels. Nous URLs stay.
- Gateway: bot names, welcome/help text per platform. Flag any in-product Nous links for decision (section 1 caveat).
- README / AGENTS.md: rewrite hero and install instructions to `reign`.

### Phase 4 — Verification (DONE 2026-09-17)

| Check | Result |
|---|---|
| Full Python suite (`scripts/run_tests.sh -j 6`, 33 min) | 43,258 passed / 53 failed on first pass. 35 of the failures are the host-specific baseline set (names shifted by the rename). The 18 new ones were all fixed; the affected 16 files rerun green (983 tests). |
| TUI (`ui-tui`) | 1,737 vitest tests pass; `npm run build` OK; bundle free of Hermes/caduceus strings |
| Web dashboard (`web`) | `tsc -b && vite build` OK into `reign_cli/web_dist`; only residual string is the upstream docs URL (decision 8) |
| Desktop app (`apps/desktop`) | `tsc --noEmit` clean |
| Docs site (`website`) | `npm run build` OK; rendered and screenshotted at `/docs/`: Rook mark navbar, monochrome theme, "In Your Corner" tagline |
| Image bytes | No upstream image hash survives except the neutral set (doc screenshots, telegram/unbroker illustrations, feature tiles, pet egg) |
| Residual `hermes`/`nous` text | 74 lines in 17 files after allowlist, all reviewed (Nous Portal provider code, upstream URLs, test fixtures, contributor identities, Credits line) |
| CLI smoke (`REIGN_HOME` isolated) | `reign --help`, `reign --version` OK; welcome banner renders REIGN logo + Rook braille mark; nothing written to `~/.reign` |

**Real regressions the codemod introduced, found by the suite and fixed** (recorded in `rebrand/mapping.yaml` so a re-run cannot repeat them):
- Model-family detection needles: `agent/coding_context.py`, `reign_cli/auth.py`, `reign_cli/model_switch.py` regex, godmode skill — a bare `"hermes"` compared against model ids was renamed to `"reign"`, so Nous Hermes models were no longer recognized. Restored.
- `scripts/install.sh` wrote the CLI launcher and the agent launcher under the same name `reign` (upstream: `hermes` and `hermes-agent`), the second overwriting the first. Agent launcher is now `reign-agent`, matching the `pyproject` console script; `reign_cli/profiles.py`, `main.py`, `uninstall.py` name sets updated.
- Skill frontmatter key: bundled skills now use `metadata.reign:` but community hub skills publish `metadata.hermes:`. Readers in `tools/skills_hub.py`, `skills_tool.py`, `blueprints.py`, `skill_linter.py` accept both.
- Test fixtures where a protected URL/email kept `hermes` while the code side was renamed (Slack link text, Discord truncated URL, hindsight template URL, SSH user, Telegram/photon/google-meet bot names, packaging artifact globs, a `"Hermez".replace` trick). Fixed in the tests.
- Docs theme: `website/src/css/custom.css` and the intro page carried the Hermes gold palette and inline gold button; now monochrome. Two Nous marketing sentences ("the lab behind Hermes, Nomos, and Psyche") removed from the docs intro.

Not replicated locally: upstream's Linux and Windows CI lanes (skipped markers), Docker image build, Electron packaging, Tauri installer build. Docker smoke test deferred to after the first push so CI can run it.

Original Phase 4 checklist:
- Zero-hit check: `grep -rniE 'hermes|nous'` returns only allowlisted lines (model names, URLs, LICENSE, NOTICE). Report the residual list explicitly.
- Image check: no upstream image hashes from the audit inventory remain.
- Rebuild TUI, web, desktop, docs. Screenshot every surface: CLI banner, TUI, dashboard, desktop, docs home, one gateway welcome message.
- Full test suite green.
- Fresh-install smoke test in Docker: `reign setup`, `reign model`, `reign gateway`. Never against the local `~/.hermes`.

### Phase 5 — Handoff and distribution model (decided 2026-09-19)

**Distribution: Rook is the distributor.** Clients install from and `reign update` against `rook-ltd/reign`. Rook re-cuts Reign from upstream on a cadence with a test gate (weekly or biweekly), never by `git merge upstream/main`: upstream moves ~600 commits/day and touched 8,111 files in the 18 days after the fork, 1,557 of them under renamed paths and 5,801 containing Hermes/Nous text, so a merge is not viable.

**Sync mechanics (to build next):** `rebrand/sync_upstream.py` takes a fresh `upstream/main` checkout, runs `rebrand.py` (all five stages), replays the hand-edit overlay (Phase 3/4 changes as a patch set plus `place_images.py`), runs the residual and image-hash gates, then records the result as a merge commit whose parents are the previous Reign head and the upstream commit (`git commit-tree`). Client installs fast-forward on every sync; mechanical branding cannot come back because the codemod runs every time; new *kinds* of branding surface on the residual list for review.

**Code-fetch paths repointed to the Rook repo** (codemod stage 5 `post_replace` in `mapping.yaml`, so re-syncs keep them): `scripts/install.sh` / `install.ps1` clone and zip URLs, `reign update` zip fallback and official-repo detection, desktop passive update check and bootstrap script download, nix/desktop homepage, release links, user-agent strings. Documentation links stay on upstream (decision 8). Left on Nous deliberately: the skills hub "official optional skills" source (`tools/skills_hub.py`), the local-runtime catalog JSON, the model catalog JSON, the Telegram security-advisory link, and the GitHub workflow `github.repository` gates (Docker Hub / Vercel / skills-index publishing need Nous credentials; they stay dormant in the Rook repo).

**Sync tooling built and tested (2026-09-19).** `rebrand/sync_upstream.py` (worktree → codemod → per-file 3-way overlay → images → lockfiles → gates → merge commit on `sync/upstream-<date>`), `rebrand/make_overlay.py` (overlay = diff of codemod output at the fork point vs HEAD, so every hand edit promoted to a mapping rule drops out automatically), `rebrand/overlay/hand-edits.patch` (68 files). Seven dry runs against upstream `d7b836ab1c` (about 11,000 commits past the fork point) found and fixed: a mapping list that had been split by an edit, nested protected spans not being restored, `git apply` aborting the whole overlay on one missing file (upstream moved the test), lockfiles riding in the overlay, per-file `git mv` costing twelve minutes. A sync now takes about five minutes and the codemod is a verified no-op on the branded tree.

**Honest per-sync cost for an 18-day gap:** all gates clean (0 residual lines beyond baseline, 0 upstream images, 0 files that fail to apply), and **35 conflict hunks in 19 files** where upstream changed the same lines as a hand edit (`tools/wake_word.py` 5, `tools/skills_hub.py` 3, `reign_cli/skin_engine.py` 3, `banner.py` 3, `auth.py` 3, the rest 1–2 each). Those are resolved by hand in the kept worktree, then `run_tests.sh`, then the sync branch is pushed as a PR. Shorter cadence means fewer hunks. Seen in the dry run and worth a rule before the first real sync: upstream added a new reader of the `hermes:` skill-metadata key (`agent/learning_graph.py`), which the codemod renames to `reign` and so silently breaks for hub skills; the dual-key fix currently lives in the overlay for four files only. A `protect` + `post_replace` regex for `.get("hermes")` would cover every current and future reader. Next reduction: turn the remaining block-style hand edits (banner art constants, default skin dict, spinner face lists, wake-word defaults) into regex block rules so they leave the overlay too.

**Inherited automation switched off (2026-09-22).** Upstream's scheduled workflows failed on every run in the Rook repo (the Install & Update E2E job needs release tags, which do not exist here; OSV-Scanner needs code scanning enabled; the two skills-index jobs are gated to the Nous repo). Disabled via GitHub: `Install & Update E2E`, `OSV-Scanner`, `Build Skills Index`, `Skills Index Freshness Check`. `.github/dependabot.yml` removed and its open action-bump PRs closed. Re-enable the E2E workflow once Rook pushes its first `v`-tag; re-add Dependabot when there is a policy for action pins.

**Release cadence and promotion flow (decided 2026-10-06).**
- Target: the newest upstream `v*` release tag, not `main` tip (upstream tags weekly; a tag has passed upstream's own gates). First real sync: `v2026.9.24`.
- `.github/workflows/upstream-sync.yml` runs Mondays 06:17 UTC (and on demand with a ref). Clean sync → pushes `sync/upstream-<tag>`, force-updates **`dev`**, opens a PR to `main`. Blocked sync (overlay conflicts) → opens/updates an issue with the conflict report; a human runs `python rebrand/sync_upstream.py --ref <tag> --keep-worktree` locally, resolves, tests, pushes the branch.
- **Dev environment = any Reign install whose checkout tracks `origin/dev`** (`git checkout dev` in the install dir, then `reign update` pulls each sync). Production installs track `main`.
- **Approval = merging the PR.** Nothing reaches `main` without a human merge. CI runs on the PR only if the `UPSTREAM_SYNC_TOKEN` secret (fine-grained PAT, contents + pull-requests write) exists; PRs opened with the default Actions token do not trigger `pull_request` workflows.
- Skill metadata key reverted to `metadata.hermes` (hub-skill and upstream-reader compatibility beat the cosmetic rename; the key is only visible to skill authors).

**First real sync: v2026.9.24 (2026-10-06).** 22,663 upstream commits past the fork point. Done with the tooling, not by hand. What it took and what it changed:
- Three sync runs. Run 1: 30 overlay files conflicted. Those were brand surfaces upstream keeps refactoring (banner art, skin palette, spinner faces, wake-word defaults, docs CSS) plus dependabot workflow bumps that had leaked into the overlay. All of them became `post_replace` rules in `rebrand/mapping.yaml` with the files listed under `overlay_exclude`; run 3: 41 overlay files, 0 conflicts.
- Full suite on the re-cut: 49,243 passed / 115 failed. Running the same files on pristine upstream showed 21 are host-specific (they fail without any rebrand; now the baseline in `rebrand/audit/baseline-known-failures.txt`). The other 86 were Reign bugs, all in the codemod's *protections*, all fixed as rules: dict keys vs. values named `hermes` (honcho host block, ACP `_meta`, API extras rename together), "Hermes Agent" vs. lowercase "hermes agent" mapping to different strings (a server message lost its classifier), the Hermes model-id regex swallowing `hermes_2026-…` timestamps, console-script tuples in either order, the shared skin branding helper appending " Agent", split string-literal YAML in test fixtures, third-party plugin maintainers.
- New tool: `rebrand/rederive.py --ref <tag>` recomputes every codemod-only file from upstream after a mapping change, so a fix can be verified in a minute instead of a 7-minute re-sync.
- Procedure that worked, for the next operator: sync → full suite → run the failing *files* on a pristine upstream worktree (`git worktree add … <tag>`, `uv sync`, `scripts/run_tests.sh <files>`) → anything that passes upstream is a Reign bug; fix it as a mapping rule, `rederive`, rerun those files. Never hand-edit the synced tree for a class of problem; hand-edit only one-offs, and put those in the overlay.
- Local quirk: a `uv sync` that reuses an old `.venv` may copy the interpreter instead of symlinking it; one upstream test (`test_update_import_guard`) symlinks that interpreter into a fake venv and then fails with a bogus `/install` prefix. `rm -rf .venv && uv venv --python 3.11` fixes it. CI is unaffected.

**Open: repo visibility.** `rook-ltd/reign` is private. Every client install and update needs a GitHub credential until it is public or a deploy key / token scheme exists.

Original Phase 5 checklist:
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
- GitHub repo URL for push: https://github.com/rook-ltd/reign (provided 2026-09-01).
- In-product Nous links: decide keep vs. replace once the audit lists them (section 1 caveat).
- Brand hex colors / typeface: none supplied; proceeding monochrome. Supply if Rook has an official accent color for the `rook` skin.

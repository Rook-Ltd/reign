# Upstream sync report — v0.23.0 on 2026-11-08

- Upstream source: `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19` (stable `v0.23.0`).
- Previous upstream source: `67481b6f37615e58f1434ba6a1528e4c6e9b754c`.
- Replayed both sources with the Reign mapping and brand assets, then merged Reign's changes.
- Regenerated Python/npm lockfiles, i18n key indexes and prompt fixtures; applied ESLint and RUF022 fixes.
- Reconciled dashboard command registration and mobile WebSocket compatibility with upstream's socket-scoped ticket admission.
- No unresolved conflict markers or surviving upstream brand images outside the neutral allowlist.
- Sync conflict reporting now uses the built-in token's Issues permission; branch/PR publishing continues to use UPSTREAM_SYNC_TOKEN.
- Native prompt rendering preserves the host OS and normalizes environment paths.

Validation before PR:

- 842 focused authentication, gateway, CLI, prompt, skill, model-picker, catalog and sync-tooling tests passed; one platform-dependent test skipped.
- Rebranding gates: no unresolved conflict markers and no unexpected upstream brand images.
- All 14 repository checks passed on the application integration and catalog-tooling revision. An inherited silent fallback now logs its traceback.

Catalog handling:

- The application update was merged in PR #7. The follow-up preserves the catalog accepted on main and makes future syncs put catalog YAML in a data-only companion PR, preserving the admission gate.
- External plugin names, repository paths, capabilities and credential identifiers are preserved; only the host compatibility field is translated.
- The codemod uses the project's existing ruamel.yaml dependency.
- Native PM bundle builds remain manually dispatched because the upstream private macOS runner is unavailable in this fork.
- The formatting bot uses the existing UPSTREAM_SYNC_TOKEN when no GitHub App is configured, including for its Git push; its privileged job remains isolated from npm execution.
- Main's JavaScript suites passed. Its packaging download failed; the same Electron, icon and archive-tool downloads subsequently completed through the real Linux preparation path. Retry CI after the remaining Python shards finish.

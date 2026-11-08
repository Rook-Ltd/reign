# Upstream provenance

- Upstream: https://github.com/NousResearch/hermes-agent
- Branch: main
- Forked at: 00b2e03c8028cbe9e6b59b03306be300c6a6df8c
- Synced at: 2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19 (v0.23.0, 2026-11-08)
- Upstream commit date: 2026-09-01 21:46:46 -0500
- Cloned: 2026-09-02T02:52Z
- Remotes: `upstream` = Nous, `origin` = https://github.com/rook-ltd/reign
- Upstream syncs (`rebrand/sync_upstream.py`) are run from a rook-ltd/reign checkout and merge
  into its `main` through a PR; there is no separate private mirror.
- Server deployment config is not in this repo; it lives in a private repo.
- A sync carries every Reign hand edit since the previous sync by three-way merging HEAD onto the
  rebranded new upstream, with the rebranded previous upstream as the base (see the
  `sync_upstream.py` docstring). `overlay/hand-edits.patch` is no longer applied.
- [Plugin API compatibility](PLUGIN-API.md) preserves public upstream Python names for external
  plugins. Its bridge and frozen consumers are intentionally excluded from content rebranding.

## Re-syncing with upstream (future)
```
git fetch upstream
# then either merge (rename detection will do some work) or re-run the codemod on a fresh checkout and diff:
python rebrand/rebrand.py --check
```

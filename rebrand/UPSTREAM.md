# Upstream provenance

- Upstream: https://github.com/NousResearch/hermes-agent
- Branch: main
- Forked at: 00b2e03c8028cbe9e6b59b03306be300c6a6df8c
- Synced at: f97608f178d1ffeca59860195ab7da295f7c8e5f (v2026.9.24, 2026-10-06)
- Upstream commit date: 2026-09-01 21:46:46 -0500
- Cloned: 2026-09-02T02:52Z
- Remotes: `upstream` = Nous, `origin` = https://github.com/rook-ltd/reign
- Upstream syncs (`rebrand/sync_upstream.py`) are run from a rook-ltd/reign checkout and merge
  into its `main` through a PR; there is no separate private mirror.
- Server deployment config is not in this repo; it lives in a private repo.

## Re-syncing with upstream (future)
```
git fetch upstream
# then either merge (rename detection will do some work) or re-run the codemod on a fresh checkout and diff:
python rebrand/rebrand.py --check
```

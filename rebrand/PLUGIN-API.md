# Upstream plugin API compatibility

Reign accepts current public Hermes Python API spellings at plugin import boundaries.
An unchanged plugin can import `hermes_constants.get_hermes_home`,
`hermes_cli.config`, `hermes_state.SessionDB`, `hermes_time` or `hermes_yaml`.
The import bridge in `reign_cli/plugin_host_api.py` resolves these to the running
Reign modules. It does not install or execute a second copy of Hermes.

## Contract

- A legacy module and its canonical module are the same object. Classes, registries,
  context variables and configuration caches therefore keep one identity.
- Existing exported names renamed by branding resolve to their Reign equivalents.
  Public module functions accept the original branded keyword arguments too;
  supplying both spellings of one argument is an error.
- Memory-provider initialization supplies `hermes_home` and `reign_home` with the
  same owning profile's path. Home and secret resolution still use Reign's scoped
  runtime. The bridge never mirrors process environment variables or reloads a
  conversation's prompts, memories or tools.
- Installed entry points in `hermes_agent.plugins`,
  `hermes_agent.plugin_capabilities` and `hermes_agent.memory_providers` remain
  discoverable. A Reign entry point of the same name takes precedence.
- `requires_hermes` retains its admission and runtime version gates. An explicitly
  declared `requires_reign` takes precedence.
- Admission lint canonicalizes legacy imports before checking private coupling or
  core mutation. The legacy spelling cannot bypass these checks.

The bridge activates through the Reign CLI package before loading user plugins,
including plugin-host children and admission probes. A standalone interpreter that
has not imported Reign does not gain these imports automatically.

## Boundaries

This preserves branded names of APIs that exist today. Private imports still produce
admission warnings and gain no stability guarantee: an alias disappears when its
canonical implementation disappears. This does not restore removed upstream APIs,
alias third-party packages, install
missing dependencies, rewrite arbitrary environment reads, or alter distribution
metadata. For example, a plugin reading `os.environ['HERMES_HOME']` directly should
use the public home resolver to work correctly across profiles.

Catalog sources and SHA pins stay unchanged while retesting. Inaccessible pins,
missing entrypoints, undeclared dependencies, capability mismatches and committed
executable payloads still need their own resolution. Compatibility passing is not
evidence that a plugin's remote service or inference calls work.

## Validation and upstream syncs

`tests/reign_cli/fixtures/upstream_api` is a frozen consumer of upstream spellings.
Its tests execute real imports, registration, admission probes, memory-provider
initialization and hook calls through both runtimes with profile A → B → A.

The rebrand mapping excludes this bridge and the frozen fixtures from content
replacement. Rebranding them would erase the compatibility contract. Changes to
the implementation still carry through the normal upstream three-way merge.

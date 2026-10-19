# Reign CLI Reference

Live sources when anything looks stale: `reign --help`, `reign <command> --help`,
https://hermes-agent.nousresearch.com/docs/reference/cli-commands

### Global Flags

```
reign [flags] [command]        (no subcommand = interactive chat)

  --version, -V             Show version
  -z, --oneshot PROMPT      One-shot: print ONLY the final response (for scripts/pipes)
  -m MODEL  --provider P    Model/provider override for this invocation
  -t, --toolsets LIST       Comma-separated toolsets for this invocation
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --tui / --cli             Force the Ink TUI / classic REPL
  --ignore-rules            Skip AGENTS.md/SOUL.md/memory/skill injection
  --safe-mode               Disable ALL customizations (troubleshooting)
  --pass-session-id         Include session ID in system prompt
```

### Chat

```
reign chat [flags]
  -q, --query TEXT          Single query, non-interactive
  --image PATH              Attach a local image to a single query
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --max-turns N             Cap tool-calling iterations
  --source TAG              Session source tag (default: cli)
```
(plus the global flags above)

### Configuration

```
reign setup [section]      Wizard (model|tts|terminal|gateway|tools|agent)
reign model                Interactive model/provider picker
reign fallback [add|remove|list]  Fallback provider chain
reign config [show|edit|get|set|unset|path|env-path|check|migrate]
reign login / logout       OAuth sign-in / clear stored auth
reign doctor [--fix]       Check dependencies and config
reign status [--full]      Component summary (--full: every section)
```

### Tools & Skills

```
reign tools [list|enable NAME|disable NAME]   Per-platform toolsets (curses UI with no args)

reign skills list|browse|search QUERY|inspect ID
reign skills install ID    Hub identifier OR a direct https://…/SKILL.md URL
reign skills config        Enable/disable skills per platform
reign skills check|update|uninstall|publish PATH
reign skills tap add REPO  Add a GitHub repo as a skill source
reign bundles              Skill bundles (one /<name> alias loads several skills)
```

### MCP Servers

```
reign mcp add NAME (--url or --command) | remove | list | test NAME
reign mcp catalog | install NAME     Curated catalog install
reign mcp configure NAME             Toggle tool selection
reign mcp serve                      Run Reign as an MCP server
```
Details (transport, tool discovery, catalog): `references/native-mcp.md`.

### Gateway (Messaging Platforms)

```
reign gateway run|install|start|stop|restart|status|setup
```

20+ platforms: Telegram, Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon — `reign photon setup`), Signal, Email, SMS, Matrix, Mattermost, Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin, API Server, Webhooks. Open WebUI connects via the API Server adapter. Most adapters ship under `plugins/platforms/`.
Docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
reign sessions list|browse|rename ID TITLE|delete ID|export OUT|prune|stats
```

### Cron / Webhooks

```
reign cron list|create SCHED|edit ID|pause|resume|run ID|remove|status
    Schedules: '30m', 'every 2h', '0 9 * * *', ISO timestamp
reign webhook subscribe NAME|list|remove NAME|test NAME
```
Webhook payloads/routes: `references/webhooks.md`.

### Profiles

```
reign profile list|create NAME (--clone|--clone-all|--clone-from)|use|show|delete
reign profile rename A B | alias NAME | export NAME | import FILE
reign profile migrate-identity A B   Retry a completed rename's session/routing identity migration
```

### Credentials & Pools

```
reign auth                 Interactive credential manager
reign auth add [PROVIDER]  Add OAuth or API-key credential (nous, openai-codex, qwen-oauth, …)
reign auth list|remove P IDX|reset PROVIDER|status
```
Multiple credentials per provider form a pool that rotates automatically and skips exhausted keys.

### Other

```
reign desktop / gui        Native desktop app
reign dashboard            Web admin panel + embedded chat (--stop / --status)
reign proxy                OpenAI-compatible local proxy backed by an OAuth provider
reign portal               Quick setup / sign in via Nous Portal
reign kanban <verb>        Multi-agent work-queue board
reign project              Named multi-folder workspaces
reign skin list|use|set    Switch/tweak skins (see references/themes.md)
reign pets <verb>          Pet mascots (see references/petdex.md)
reign memory setup|status|off|reset   Memory provider
reign secrets bitwarden|onepassword   External secret stores
reign moa                  Mixture-of-Agents slots
reign hooks / security / backup / import / checkpoints / console
reign logs [-f] [errors]   View agent/error logs
reign send                 One-off message through a gateway platform
reign pairing / plugins / insights / journey / computer-use
reign acp                  ACP server (IDE integration)
reign completion bash|zsh|fish
reign update / uninstall / claw migrate
```

Plugin- and provider-supplied subcommands (e.g. `reign photon setup`) only appear once their plugin is installed/active.

### Where to Find Things

| Looking for... | Location |
|---|---|
| Config options | `reign config edit` · [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Tools / toolsets | `reign tools list` · [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Skills catalog | `reign skills browse` · [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `reign model` · [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Env variables | `reign config env-path` · [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| Gateway logs | `~/.reign/logs/gateway.log` (or `reign logs`) |
| Sessions | `reign sessions browse` (reads state.db) |

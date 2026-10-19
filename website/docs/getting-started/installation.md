---
sidebar_position: 2
title: "Installation"
description: "Install Reign with desktop bundles, source installers, Docker, Nix, or the Termux APT package"
---

# Installation

Get Reign up and running in under two minutes!

:::tip Platform Support
For the full platform support matrix (which OSes, distribution methods, and
platform-gated features are supported), see **[Platform Support](./platform-support.md)**.
:::

## Quick Install
### Desktop packages on macOS or Windows

Download the package for your platform from the
[Reign website](https://hermes-agent.nousresearch.com/).

- **Windows:** open the `.appinstaller` download with Windows App Installer.
  It installs the signed MSIX bundle and records its update source.
  Microsoft Store packages have separate Store ownership.
- **macOS:** open the DMG, then copy `Reign.app` to Applications. The ZIP
  artifact carries the signed app used by the automatic updater.

Bundled packages contain the agent, Python, supported dependencies, and prebuilt
interfaces. First launch does not build that base runtime. Provider access and
optional integrations can still require network access.

A `Reign-Setup` bootstrap installer is different: it downloads a source
installation and builds the desktop app. See [Reign Desktop](../user-guide/desktop.md).

There is no separate remote-only Desktop download. To use Desktop with a Reign
backend on another machine, install one of the packages above and connect it
from **Settings → Gateways**; see
[Connecting to a remote backend](../user-guide/desktop.md#connecting-to-a-remote-backend).

:::note
The macOS installer is **Apple Silicon only**. macOS on x86 (Intel) processors is [not a supported platform](./platform-support.md#unsupported).
:::

### Without Reign Desktop:
For a command-line only install without Reign Desktop, run:

#### Linux / macOS / WSL2
```bash
curl -fsSL https://raw.githubusercontent.com/rook-ltd/reign/main/scripts/install.sh | bash
```

#### Windows (native)

Run in powershell:
```powershell
iex (irm https://raw.githubusercontent.com/rook-ltd/reign/main/scripts/install.ps1) 
```

If you want to install & run Reign Desktop after a command-line only install, simply run
```bash
reign desktop
```

### Android / Termux

Use the [Termux APT package](./termux.md) on aarch64 Android devices.
Configure its signed repository before running `pkg install reign`.
The desktop/server scripts are not the Termux installation path.

### What the source installer does

The scripts clone the source, bootstrap uv, and delegate dependency preparation
to PM. PM provides pinned Python, Node.js, npm, ripgrep, and FFmpeg. The source
installation selects the `all` Python extra, not every optional extra.
PM also installs the browser and computer-use tools by default: `agent-browser`
and its pinned Chromium, and `cua-driver` (the computer-use driver, on macOS,
Windows and glibc Linux). If a download fails, the install still completes and
prints the command to retry. The default browser driver (browser-harness, the
engine of the Browser Use CLI) is a regular Python dependency, so every install,
the Desktop app included, already has it.
Other optional tools use their feature-specific installation paths.

A new install lands on the latest stable release, the channel `reign update`
follows from then on (see [Updating](./updating.md)). To install the tip of
`main` instead, pass `--channel main` on POSIX or `-Channel main` on Windows
(or set `REIGN_INSTALL_CHANNEL=main` first, for the one-liners).

To leave the browser tools out, pass `--skip-browser` on POSIX or `-SkipBrowser`
on Windows; for the computer-use driver, `--skip-computer-use` /
`-SkipComputerUse`. Reign remembers these choices: later installs and
`reign update` do not add them back. Run `reign pm install agent-browser` or
`reign pm install cua-driver` to install them and undo the choice.

The scripts create a launcher and prepare the data directory. Interactive runs
also invoke setup and gateway configuration. `--non-interactive` on POSIX, or
`-NonInteractive` on Windows, skips stages that need input. The optional
`--include-desktop` / `-IncludeDesktop` stage builds the desktop from source.

On a terminal the scripts show one status line per step and write the output
of git, uv and the builds to `logs/install.log` under the Reign data
directory; a failed step prints its last lines and the log path. CI (`CI` or
`GITHUB_ACTIONS` set), redirected output, `--verbose` / `-Verbose` or
`REIGN_INSTALL_VERBOSE=1` stream everything instead.

#### Install layout

| Method | Code | CLI entry point | Default user data |
|---|---|---|---|
| POSIX source script | `~/.reign/reign/` | `~/.local/bin/reign` wrapper | `~/.reign/` |
| Windows source script | `%LOCALAPPDATA%\reign\reign\` | `%LOCALAPPDATA%\reign\bin\` | `%LOCALAPPDATA%\reign\` |
| Desktop bundle | Inside the installed app package | Packaged launchers; Windows execution aliases | Platform default Reign data directory |
| Docker | `/opt/reign/` | Image entrypoint and `reign` shim | Mounted `/opt/data/` |
| Termux APT | `$PREFIX/lib/reign/` | Symlinks in `$PREFIX/bin/` | `~/.reign/` |

`REIGN_HOME` selects user data. The POSIX script's `--dir` selects its source
checkout independently. Windows provides `-ReignHome` and `-InstallDir`.
Running the POSIX script as root does not select an automatic FHS layout:
it uses root's home unless you provide an explicit source path.

PM's tool store and per-install Python generations have separate lifetimes.
See [Package management](../reference/package-management.md) for their locations.
Do not remove the data root to repair an application installation.

### After Installation

Reload your shell and start chatting:

```bash
source ~/.bashrc   # or: source ~/.zshrc
reign             # Start chatting!
```

To reconfigure individual settings later, use the dedicated commands:

```bash
reign model          # Choose your LLM provider and model
reign tools          # Configure which tools are enabled
reign gateway setup  # Set up messaging platforms
reign config set     # Set individual config values
reign config get     # Inspect individual config values
reign setup          # Or run the full setup wizard to configure everything at once
```

:::tip Fastest path: Nous Portal
One subscription covers 300+ models plus the [Tool Gateway](../user-guide/features/tool-gateway.md) (web search, image generation, TTS, cloud browser). Skip the per-tool key juggling:

```bash
reign setup --portal
```

That logs you in, sets Nous as your provider, and turns on the Tool Gateway in one command.
:::

:::tip Already running Reign on another machine?
You don't need to rebuild your setup from scratch. Restore a full backup with `reign import` (see [Exporting Reign to another machine](../reference/faq.md#exporting-reign-to-another-machine)), or bring over a single agent with `reign profile import` (see [Moving a single profile to another machine](../reference/faq.md#moving-a-single-profile-to-another-machine)). Note that a profile export excludes credentials by design, so an export alone is not a full backup — [`reign backup` vs `reign profile export`](../reference/faq.md#reign-backup-vs-reign-profile-export) explains which to use.
:::

---

## Prerequisites

For the POSIX source script, provide Git, curl, tar, and SHA-256 utilities.
Windows can bootstrap its pinned Git for Windows archive when Git is absent.
The script always downloads its verified uv pin; a uv already on your PATH is never used.

Current first-party installations run on **Python 3.14**. The broader
`>=3.11,<3.15` range in `pyproject.toml` lets older Python installations
run the updater before PM switches them to 3.14; it does not promise current
runtime support on 3.11–3.13. PM selects the managed tool versions from
`pm/lock.json`; it does not adopt arbitrary system Node versions as the
installed runtime.

Source builds can require a native compiler and platform development libraries.
Building Electron from source adds Node native-module requirements. These
build prerequisites do not apply to installing a complete desktop package.
Linux Chromium also requires system libraries supplied by the distribution.

On glibc Linux, the managed Node.js links `libatomic.so.1`, which minimal
Debian, Ubuntu and RHEL-family images do not ship. When the library is
missing, the installer and `reign update` install the distro package
(`libatomic1` on apt and zypper, `libatomic` on dnf/yum and apk, `gcc-libs`
on pacman). They run the package manager directly as root, or as
`sudo -n` otherwise. An interactive run asks for your sudo password once,
before installing dependencies. `--non-interactive` runs never prompt. If
the install cannot run, the error names the exact command for the package
manager it found.

:::tip Nix users
Nix is **no longer an explicitly supported install path** (best-effort only). If you already use Nix (on NixOS, macOS, or Linux), there's a dedicated setup path with a Nix flake, declarative NixOS module, and optional container mode. See the **[Nix & NixOS Setup](./nix-setup.md)** guide.
:::

---

## Manual / Developer Installation

For a source checkout, start with the
[PM developer workflow](../reference/package-management.md#developer-workflow).
It covers activation, daily commands, dependency refresh, and current bootstrap limits.
[Development Setup](../developer-guide/contributing.md#development-setup) covers the separate test environment and checks.

---

## Non-Sudo / System Service User Installs

Run the source installer as the intended service user. Its home, tool store,
configuration, and launcher must belong to that user.

1. As an administrator, install the source-build prerequisites and any Linux
   libraries needed by the selected browser backend.
2. As the service user, run the regular installer:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/rook-ltd/reign/main/scripts/install.sh | bash
   ```

3. Add the actual launcher directory to the service user's shell environment:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. Run `reign doctor` from that account. Use the installed wrapper, not a
   hardcoded `venv/bin/reign` path.
5. For a Linux user service that must survive logout, enable lingering as an administrator:

   ```bash
   sudo loginctl enable-linger SERVICE_USER
   ```

The current source installer does not run Playwright's `--with-deps` step.
Apart from Node.js's `libatomic` (see Prerequisites), it does not install
system packages. PM manages tool binaries; the administrator supplies system
libraries. A service user without sudo gets the exact `libatomic` command to
ask an administrator to run. See
[Browser automation](../user-guide/features/browser.md) and
[Messaging Gateway](../user-guide/messaging/index.md).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `reign: command not found` | Reload your shell (`source ~/.bashrc`) or check PATH |
| `API key not set` | Run `reign model` to configure your provider, or `reign config set OPENROUTER_API_KEY your_key` |
| Missing config after update | Run `reign config check` then `reign config migrate` |

For more diagnostics, run `reign doctor` — it will tell you exactly what's missing and how to fix it.

### Symlinked home directories and external storage

Reign supports a symlinked `REIGN_HOME` and symlinked home subdirectories,
including `hooks`, `skills`, `sessions`, and `logs`. During home initialization,
existing directory links are preserved, and permissions on linked directories
(and descendants such as `logs/curator`) are left to their owner.

If a link target is missing, inaccessible, or not a directory, initialization
stops with a storage error naming the path and link target. Reign does **not**
replace the link or create its missing target: doing so could write data onto
the local disk while an external or NAS volume is unmounted. Check the reported
link, restore the mount or correct its target, and verify access permissions
before retrying. For a deliberately new dotfiles target, create it yourself only
after confirming the intended storage is available.

`reign doctor` reports these failures as storage problems, not invalid YAML.
Keep your existing `config.yaml`; running `reign setup` is not the repair for an
unavailable directory. This is a directory-availability check, not a mount monitor:
an existing directory cannot establish that the intended volume is mounted.

## Install method auto-detection

The update owner depends on the running installation, not only its data home.
Source checkouts use the managed Git update path. Desktop bundles, Docker,
Nix, and Termux packages retain their package owner's update mechanism.
`reign doctor` reports installation provenance. See
[Updating & Uninstalling](./updating.md) before changing package-owned files.

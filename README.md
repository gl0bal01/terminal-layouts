# Terminal-layouts

**Eight ready-made terminal workspaces. One command opens each, in tmux, Zellij or Herdr.**

Type `tmux-pentest` and a full engagement workspace is in front of you: four tabs, fifteen panes,
live socket and process monitors already running. `zellij-pentest` and `herdr-pentest` open the same
layout (Herdr starts the monitors only when you ask, with `--run-commands`).

![Install Terminal-layouts and enable the shell commands](docs/demo/01-install.gif)

## The workflows

Open any of them with `tmux-<workflow>`, `zellij-<workflow>` or `herdr-<workflow>`.

| | Workflow | Tabs you get | Opens in |
|---|---|---|---|
| 🖥️ | **`project`** | `work` (editor or agent, live `git status`, logs) · `scratch` | current directory |
| 🤖 | **`ai-agents`** | `cockpit` · `implement` · `research` · `review`, one coding agent per tab | current directory |
| 🏠 | **`claude-projects`** | `cockpit` · one tab per project · `scratch` | `~/projects` |
| 🐳 | **`docker`** | `stack` (Compose, live `docker ps`) · `logs` · `debug` | `~/docker` |
| 🎯 | **`pentest`** | `recon` · `exploit` · `post` · `loot` | `~/ops/pentest` |
| 🔬 | **`malware-analysis`** | `static` · `dynamic` · `network` · `ioc` | `~/ops/malware` |
| 📡 | **`osint`** | `target` · `web` · `social` · `timeline` | `~/ops/osint` |
| 🏁 | **`ctf`** | `cockpit` · `web` · `pwn` · `crypto` · `forensics` · `misc` | `~/ops/ctf` |

Each tab is laid out for its job. Two examples:

```
project › work                           pentest › recon
┌───────────────────────┬─────────┐      ┌───────────────────────┬─────────┐
│                       │ git     │      │ scanner               │ netmon  │
│ editor / agent        │ status  │      │                       │ live ss │
│                       ├─────────┤      ├───────────────────────┼─────────┤
│                       │ logs    │      │ enum                  │ notes   │
└───────────────────────┴─────────┘      └───────────────────────┴─────────┘
```

Every tab and pane of every workflow: [Workflows](docs/workflows.md). They are plain YAML, so you can
change them or add your own.

## Install

```bash
pipx install terminal-layouts
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc    # bash: tl init bash, in ~/.bashrc
exec zsh
```

- **Needs** Python 3.10+ and at least one of: tmux 3.4+ with tmuxp, Zellij, Herdr 0.8.2+.
- **Runs on** Linux and macOS. On Windows, use WSL2.
- **Upgrade** with `pipx upgrade terminal-layouts`.

### Install with an AI agent

Paste this into Claude Code, Codex or any agent that has a shell:

```text
Install Terminal-layouts from https://github.com/gl0bal01/terminal-layouts.
1. Check which of tmux (3.4+), zellij and herdr are installed. If none, ask me which one to install.
2. For tmux, make sure tmuxp is installed (pipx install tmuxp).
3. Run: pipx install terminal-layouts (already installed: pipx upgrade terminal-layouts)
4. Add eval "$(command tl init zsh)" to ~/.zshrc (bash: tl init bash, in ~/.bashrc),
   unless the line is already there. Show me the line before you write it.
5. Verify in a new shell: tl --version, tl validate, layouts.
Do not start any session, and do not use sudo without asking me.
```

## Use

Every command is `<backend>-<workflow>`. Tab completes names, directories and options.

```bash
layouts                      # every command, with its directory
tmux-project                 # tmux:   this directory, session <directory>
zellij-docker                # Zellij: ~/docker, session docker
herdr-ai-agents              # Herdr:  this directory, workspace ai-<directory>
tmux-pentest --new acme      # create ~/ops/pentest/acme, session pt-acme
tl help                      # the manual
```

## One manifest, three backends

tmux reads `tmuxp` YAML, Zellij reads KDL, and Herdr has no layout file at all. Keeping the same
workspace by hand in each of them means the copies drift apart. Here each workflow is one YAML file,
the only thing you edit. The `tl` command generates every backend from it, and the tests fail when two
backends stop describing the same workspace. You can switch between tmux, Zellij and Herdr and find
the same tabs and panes.

## Documentation

| Read | To |
|---|---|
| [Commands and options](docs/usage.md) | learn every command, where a workspace opens and how it is named |
| [Tmux](docs/tmux.md) · [Zellij](docs/zellij.md) · [Herdr](docs/herdr.md) | start from zero with one backend: install, first session, the few keys you need, troubleshooting |
| [Workflows](docs/workflows.md) | see the tabs and panes of each workflow, change them or write your own |
| [Development](docs/development.md) | work on the code: Make targets, tests, CI, how the generators work |

In the terminal, `tl help` prints the manual for the manifest you use and `tl COMMAND -h` covers one
command.

## Development

```bash
git clone https://github.com/gl0bal01/terminal-layouts && cd terminal-layouts
pip install pyyaml jsonschema
make            # list every target
make test       # schema, parity, idempotence, unit and shell tests
make e2e        # launch every workflow on real, throwaway tmux, Zellij and Herdr servers
make ci         # every CI job, locally
```

Details in [Development](docs/development.md).

## License

MIT

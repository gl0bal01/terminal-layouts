# Herdr for beginners, with terminal-layouts

[Herdr](https://herdr.dev/) is a terminal workspace manager built for AI coding agents. A background
**server** keeps everything running; the `herdr` app you open is a client you can close and reopen.
The server holds **workspaces** (listed in the sidebar), each with **tabs**, each split into **panes**.
terminal-layouts builds every workflow as a workspace in the running server: one command and the whole
workspace is there. There is no layout file to install.

![Every workflow as a Herdr workspace](demo/04-herdr.gif)

**Contents:** [1 Install](#1-install) · [2 First workspace](#2-your-first-workspace) ·
[3 Keys](#3-the-keys-you-need) · [4 Every command](#4-every-command) · [5 Options](#5-options) ·
[6 Workspaces](#6-managing-workspaces) · [7 Recipes](#7-recipes) · [8 Troubleshooting](#8-troubleshooting) ·
[9 Learn more](#9-learn-more)

---

## 1. Install

You need **Herdr 0.8.2 or newer** (tested on 0.8.2 and 0.9.5; install it from
[herdr.dev](https://herdr.dev/)) and **tl**, installed from the repository (Herdr support is newer than
the PyPI release):

```bash
sudo apt install pipx && pipx ensurepath   # macOS: brew install pipx. Then open a new terminal
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"
herdr --version && tl --version
```

Then add the shell commands to `~/.zshrc` (bash: `~/.bashrc` and `tl init bash`), and open a new
terminal:

```bash
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc
layouts                          # lists every command it defined
```

Only want Herdr? Use `eval "$(command tl init zsh --backends herdr)"` instead of the line above.

## 2. Your first workspace

```bash
herdr                            # start Herdr (or reattach to it)
```

In a Herdr pane:

```bash
cd ~/projects/my-app
herdr-ai-agents                  # = tl launch herdr ai-agents
```

A new workspace `ai-my-app` appears in the sidebar and gets the focus, with its tabs (`cockpit`,
`implement`, `research`, `review`). The panes start as plain shells: **no agent is started for you**.
Type `opencode`, `pi`, `claude` or `codex` in the pane you want.

Close the app whenever you like: press `Ctrl+b` then `q` (**detach**), or close the terminal window.
The server and every pane keep running (not across a reboot); `herdr` brings you back.
`herdr server stop` ends everything. To run Herdr without the app, start `herdr server` in a terminal
of its own: it stays in the foreground.

## 3. The keys you need

Herdr is mouse-first: click workspaces, tabs and panes, drag split borders, right-click for menus,
drag-select text to copy it. On the keyboard, every key starts with the **prefix**: press `Ctrl+b`,
release it, then the key. Default Herdr 0.9.5 keys:

| To do this | Press |
|---|---|
| **Detach** (everything keeps running) | `Ctrl+b` `q` |
| Pick a workspace | `Ctrl+b` `w` |
| Go anywhere (session navigator) | `Ctrl+b` `g` |
| Next / previous tab | `Ctrl+b` `n` / `Ctrl+b` `p` |
| Go to tab 1…9 | `Ctrl+b` `1` … `9` |
| Move to the pane left / down / up / right | `Ctrl+b` `h` / `j` / `k` / `l` |
| Next / previous pane | `Ctrl+b` `Tab` / `Ctrl+b` `Shift+Tab` |
| **Zoom** the pane, and back | `Ctrl+b` `z` |
| Split right / split down | `Ctrl+b` `v` / `Ctrl+b` `-` |
| Resize mode | `Ctrl+b` `r` |
| Close the pane | `Ctrl+b` `x` |
| New tab / close tab | `Ctrl+b` `c` / `Ctrl+b` `Shift+x` |
| Rename tab / pane / workspace | `Ctrl+b` `Shift+t` / `Shift+p` / `Shift+w` |
| New workspace / close workspace | `Ctrl+b` `Shift+n` / `Ctrl+b` `Shift+d` |
| **Scroll** and copy | `Ctrl+b` `[`, then `h` `j` `k` `l` `PageUp` `PageDown`, `/` search, `v` select, `y` copy, `q` leave |
| Show / hide the sidebar | `Ctrl+b` `b` |
| Settings | `Ctrl+b` `s` |
| Every key binding | `Ctrl+b` `?` |

Keys live in `~/.config/herdr/config.toml` (`[keys]`); `herdr --default-config` prints the defaults.
Reload after a change with `Ctrl+b` `Shift+r` (or `herdr server reload-config`).

**tmux inside Herdr?** Both use `Ctrl+b`. Give Herdr another prefix, for example
`prefix = "ctrl+a"` under `[keys]`, then reload (`Ctrl+b` `Shift+r`).

## 4. Every command

Each command is a shortcut for a `tl launch` line. Both take the same arguments. Every run creates a
**new** workspace.

| Shortcut | Same as | Opens in | Workspace name |
|---|---|---|---|
| `herdr-ai-agents` | `tl launch herdr ai-agents` | current directory | `ai-<directory>` |
| `herdr-claude-projects` | `tl launch herdr claude-projects` | `~/projects` | `Claude Projects` |
| `herdr-ctf` | `tl launch herdr ctf` | `~/ops/ctf` | `CTF` |
| `herdr-docker` | `tl launch herdr docker` | `~/docker` | `Docker` |
| `herdr-malware-analysis` | `tl launch herdr malware-analysis` | `~/ops/malware` | `Malware Analysis` |
| `herdr-osint` | `tl launch herdr osint` | `~/ops/osint` | `OSINT` |
| `herdr-pentest` | `tl launch herdr pentest` | `~/ops/pentest` | `Pentest` |
| `herdr-project` | `tl launch herdr project` | current directory | `<directory>` |

What each workflow contains (tabs and panes): [The 8 workflows](../README.md#the-8-workflows).
Directories come from the manifest; `tl help workflows` shows yours. `tl gen herdr pentest` prints the
plan that would be built, without touching Herdr.

Type `herdr-` and press `Tab` to complete the name, then `Tab` again for directories and options.

`claude-projects` is a sample multi-project cockpit: its project tabs point at the author's own
directories. Edit them in your manifest before using it ([Customize](../README.md#customize)).

## 5. Options

| Shortcut | Same as | Effect |
|---|---|---|
| `herdr-pentest .` | `tl launch herdr pentest .` | open in the current directory, workspace `pt-<directory>` |
| `herdr-pentest ~/case` | `tl launch herdr pentest ~/case` | open in `~/case`, workspace `pt-case` (`--cwd DIR` is the same) |
| `herdr-pentest --new acme` | `tl launch herdr pentest --new acme` | create `~/ops/pentest/acme`, open it, workspace `pt-acme` |
| `herdr-pentest --label red-team` | `tl launch herdr pentest --label red-team` | choose the workspace name |
| `herdr-pentest --run-commands` | `tl launch herdr pentest --run-commands` | also **run** the pane commands of the workflow |

- Give **one** place: `DIR`, `.` or `--new NAME`, not two.
- Pane commands are **off** by default in Herdr (tmux and Zellij always run them). `--run-commands`
  runs every non-empty command of the Herdr plan, and security workflows can contain network tools:
  read the plan first with `tl gen herdr pentest`.
- The prefix (`pt-`, `ma-`, `os-`, …) keeps names apart: `herdr-pentest .` and `herdr-osint .` from the
  same directory give `pt-<dir>` and `os-<dir>`.

## 6. Managing workspaces

| Shortcut | Same as | Does |
|---|---|---|
| `herdr-ls` | `herdr workspace list` (made readable) | list workspaces: `*` = focused, then id, name, tabs and panes |
| `herdr-close <id>...` | `herdr workspace close <id>` | close one or more workspaces (ids from `herdr-ls`; `Tab` completes them) |
| `h` | `herdr` | Herdr itself, e.g. `h status` |

```text
$ herdr-ls
* w1     pt-acme  (4 tabs, 15 panes)
  w2     ai-my-app  (4 tabs, 9 panes)
$ herdr-close w2
closed w2
```

The Herdr CLI goes further: `herdr workspace focus <id>`, `herdr workspace rename <id> <name>`,
`herdr tab list`, `herdr pane list`. `herdr server stop` ends the server and every pane in it.

If a name was already taken in your shell (an alias `h`, say), terminal-layouts keeps yours and says
so once at startup. To replace it, change the line in `~/.zshrc` to `eval "$(command tl init zsh --force)"` (it replaces every taken name) and open a new terminal.

## 7. Recipes

**One workspace per engagement**

```bash
herdr-pentest --new acme         # creates ~/ops/pentest/acme, workspace pt-acme
# Ctrl+b q to detach ... next morning: herdr, then Ctrl+b w to pick pt-acme
```

The server keeps it while the machine runs, **not across a reboot**: save your work before shutting
down.

**Agents side by side on one project**

```bash
cd ~/projects/my-app
herdr-ai-agents                  # cockpit, implement, research, review tabs
# start claude in one pane and codex in another; Ctrl+b n / p between tabs
```

Give each agent that writes code its own Git worktree, and review before you merge:
[AI-agent workspaces](ai-agents.md).

**From another terminal:** `herdr-<workflow>` also works outside Herdr. It targets your default Herdr
session (or `HERDR_SOCKET_PATH`); open `herdr` to see the result. Inside a Herdr pane it targets that
session.

**Opened one twice by mistake?** Every run is a new workspace: `herdr-ls`, then `herdr-close <id>`.

## 8. Troubleshooting

| You see | Do this |
|---|---|
| `error: Herdr executable not found; install Herdr first` | install Herdr (section 1) |
| `error: Herdr server unavailable; start 'herdr server' or open Herdr first` | run `herdr` (or `herdr server` in another terminal), then try again |
| `error: Herdr client/server protocol mismatch; restart the Herdr server` | you upgraded Herdr: `herdr server stop` (this **stops every pane and agent**: let them finish first), then `herdr` |
| `command not found: herdr-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing h ...` | the name was taken: use `herdr` / `tl launch herdr …`, or put `--force` in your `tl init` line (section 6) |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; Herdr will open those panes in $HOME` | create that directory, or pass `DIR` / `.` / `--new NAME` (`claude-projects`: edit it, section 4) |
| `error: --detach is tmux-only` | drop `-d`: the workspace is created in the server anyway |
| A launch failed halfway | nothing to clean up: tl closes the workspace it was building |
| An agent did not start | on purpose: type it in the pane (`--run-commands` only runs manifest commands) |

## 9. Learn more

- `tl help herdr` and `tl help launch`: every option, in the terminal; `tl launch -h`: examples.
- `Ctrl+b` `?` inside Herdr; [herdr.dev/tui/docs](https://herdr.dev/tui/docs/), `herdr --help`.
- [AI-agent workspaces](ai-agents.md): how the Herdr backend works and its limits.
- [tmux tutorial](tmux.md) · [Zellij tutorial](zellij.md) · [all GIFs](../README.md#learn-it-in-6-gifs)

![The tl commands](demo/06-cli.gif)

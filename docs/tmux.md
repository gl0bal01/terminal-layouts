# tmux for beginners, with terminal-layouts

tmux keeps your terminals alive in **sessions** that survive closing the window or losing an SSH
connection. A session holds **windows** (tabs, listed in the status bar at the bottom), and each window
is split into **panes**. terminal-layouts turns every workflow into a ready-made session: one command
and the whole workspace is there.

![Every workflow in tmux](demo/02-tmux.gif)

**Contents:** [1 Install](#1-install) · [2 First session](#2-your-first-session) ·
[3 Keys](#3-the-keys-you-need) · [4 Every command](#4-every-command) · [5 Options](#5-options) ·
[6 Sessions](#6-managing-sessions) · [7 Recipes](#7-recipes) · [8 Troubleshooting](#8-troubleshooting) ·
[9 Learn more](#9-learn-more)

---

## 1. Install

You need **tmux 3.4+**, **tmuxp** (it loads the layouts) and **tl**, installed with
[pipx](https://pipx.pypa.io/).

```bash
sudo apt install tmux pipx       # Ubuntu 24.04+ / Debian 13+   (macOS: brew install tmux pipx)
pipx ensurepath                  # then open a new terminal, so ~/.local/bin is on your PATH
pipx install tmuxp
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"
tmux -V && tmuxp --version && tl --version     # check all three
```

`--force` replaces an older `tl` (the PyPI release predates the shell commands). `tmux -V` older than
3.4 (Ubuntu 22.04 ships 3.2a, Debian 12 3.3a)? Install a newer tmux, for example with Homebrew.

Then add the shell commands to `~/.zshrc` (bash: `~/.bashrc` and `tl init bash`), and open a new
terminal:

```bash
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc
layouts                          # lists every command it defined
```

Only want tmux? Use `eval "$(command tl init zsh --backends tmux)"` instead of the line above.

## 2. Your first session

```bash
cd ~/projects/my-app
tmux-project                     # = tl launch tmux project
```

You are now *inside* tmux, in a session named `my-app`. The status bar shows the session name on the
left and the windows (`work`, `scratch`) next to it; `*` marks the current one.

Every tmux key starts with the **prefix**: press `Ctrl+b`, **release it**, then press the key. To leave
without stopping anything, **detach**: `Ctrl+b` then `d`. Everything keeps running:

```bash
tmux-ls                          # my-app: 2 windows (created ...)
tmux-attach my-app               # back where you were
```

## 3. The keys you need

Default tmux 3.4 keys. "`Ctrl+b` `d`" means: press `Ctrl+b`, release, press `d`.

| To do this | Press |
|---|---|
| **Detach** (session keeps running) | `Ctrl+b` `d` |
| Next / previous window | `Ctrl+b` `n` / `Ctrl+b` `p` |
| Go to window 0…9 | `Ctrl+b` `0` … `9` |
| Pick a window or session from a tree | `Ctrl+b` `w` (sessions: `Ctrl+b` `s`) |
| Move to the pane left / right / up / down | `Ctrl+b` `←` `→` `↑` `↓` |
| Next pane | `Ctrl+b` `o` |
| **Zoom** the pane to full window, and back | `Ctrl+b` `z` |
| Split left / right | `Ctrl+b` `%` |
| Split top / bottom | `Ctrl+b` `"` |
| Resize the pane | `Ctrl+b` `Alt+←` `→` `↑` `↓` |
| Cycle pane arrangements | `Ctrl+b` `Space` |
| Close the pane (asks y/n) | `Ctrl+b` `x` |
| New window / close window (asks y/n) | `Ctrl+b` `c` / `Ctrl+b` `&` |
| Rename the window / the session | `Ctrl+b` `,` / `Ctrl+b` `$` |
| Previous / next session | `Ctrl+b` `(` / `Ctrl+b` `)` |
| **Scroll** back through output | `Ctrl+b` `[` (or `Ctrl+b` `PageUp`), then `↑` `↓` `PageUp` `PageDown`; `q` leaves |
| Paste what you copied | `Ctrl+b` `]` |
| Every key binding | `Ctrl+b` `?` (`q` leaves) |
| Type a tmux command | `Ctrl+b` `:` |

**Copying text:** in scroll mode, `Ctrl+Space` starts a selection and `Alt+w` copies it (emacs keys, the
default). If `$EDITOR` or `$VISUAL` contains `vi`, tmux uses vi keys instead: `Space` to start, `Enter`
to copy.

**Mouse:** off by default. To click panes and windows, drag borders and scroll with the wheel:

```bash
echo 'set -g mouse on' >> ~/.tmux.conf
tmux source-file ~/.tmux.conf    # apply to the running server
```

## 4. Every command

Each command is a shortcut for a `tl launch` line. Both take the same arguments.

| Shortcut | Same as | Opens in | Session name |
|---|---|---|---|
| `tmux-ai-agents` | `tl launch tmux ai-agents` | current directory | `ai-<directory>` |
| `tmux-claude-projects` | `tl launch tmux claude-projects` | `~/projects` | `claude-projects` |
| `tmux-ctf` | `tl launch tmux ctf` | `~/ops/ctf` | `ctf` |
| `tmux-docker` | `tl launch tmux docker` | `~/docker` | `docker` |
| `tmux-malware-analysis` | `tl launch tmux malware-analysis` | `~/ops/malware` | `malware-analysis` |
| `tmux-osint` | `tl launch tmux osint` | `~/ops/osint` | `osint` |
| `tmux-pentest` | `tl launch tmux pentest` | `~/ops/pentest` | `pentest` |
| `tmux-project` | `tl launch tmux project` | current directory | `<directory>` |

What each workflow contains (tabs and panes): [The 8 workflows](../README.md#the-8-workflows).
Directories come from the manifest; `tl help workflows` shows yours.

Type `tmux-` and press `Tab` to complete the name, then `Tab` again for directories and options.

`claude-projects` is a sample multi-project cockpit: its project tabs point at the author's own
directories. Edit them in your manifest before using it ([Customize](../README.md#customize)).

## 5. Options

| Shortcut | Same as | Effect |
|---|---|---|
| `tmux-pentest .` | `tl launch tmux pentest .` | open in the current directory, session `pt-<directory>` |
| `tmux-pentest ~/case` | `tl launch tmux pentest ~/case` | open in `~/case`, session `pt-case` (`--cwd DIR` is the same) |
| `tmux-pentest --new acme` | `tl launch tmux pentest --new acme` | create `~/ops/pentest/acme`, open it, session `pt-acme` |
| `tmux-pentest --label red-team` | `tl launch tmux pentest --label red-team` | choose the session name |
| `tmux-pentest -d` | `tl launch tmux pentest -d` | create the session **detached** (stay where you are) |
| `tmux-pentest --new acme -d` | `tl launch tmux pentest --new acme -d` | options combine |

- Give **one** place: `DIR`, `.` or `--new NAME`, not two.
- The prefix (`pt-`, `ma-`, `os-`, …) keeps names apart: `tmux-pentest .` and `tmux-osint .` from
  the same directory give `pt-<dir>` and `os-<dir>`.
- tmux stores `.` and `:` in session names as `_`, so `my.app` becomes `pt-my_app`.

![Options: directory, --new, --label, detached](demo/05-options.gif)

## 6. Managing sessions

| Shortcut | Same as | Does |
|---|---|---|
| `tmux-ls` | `tmux list-sessions` | list sessions |
| `tmux-attach <session>` | `tmux attach -t <session>` | go back into a session (`Tab` completes names) |
| `tmux-kill <session>` | `tmux kill-session -t <session>` | stop one session and everything running in it |
| `tmux-kill-all` | `tmux kill-server` | stop **every** tmux session, including ones you made by hand |
| `t` | `tmux` | the multiplexer itself, e.g. `t ls` |

If a name was already taken in your shell (an alias `t`, say), terminal-layouts keeps yours and says so
once at startup. To replace it, change the line in `~/.zshrc` to `eval "$(command tl init zsh --force)"` (it replaces every taken name) and open a new terminal.

## 7. Recipes

**One directory per engagement, resumed the next day**

```bash
tmux-pentest --new acme          # creates ~/ops/pentest/acme, session pt-acme
# Ctrl+b d ... close the terminal ... next morning:
tmux-attach pt-acme
```

Sessions survive closing the terminal and dropped SSH connections, **not a reboot**: save your work
before shutting down.

**Several workflows on one project**

```bash
cd ~/projects/my-app
tmux-project -d                  # session my-app, detached
tmux-ai-agents                   # session ai-my-app
# Ctrl+b s to jump between them, or Ctrl+b ( and Ctrl+b )
```

**Over SSH:** start sessions on the server; if the connection drops, reconnect and `tmux-attach`.

**After editing the manifest:** layouts are generated fresh on every launch, but running a shortcut
again while its session exists simply goes back into the old one. Rebuild it from **outside** that
session (detach first with `Ctrl+b` `d`, or the kill also stops the shell you are typing in):
`tmux-kill pt-acme && tmux-pentest --new acme`.

**Plain tmuxp, without tl:** `tl install` writes every layout to `~/.config/tmuxp` (the only `tl`
command that writes there); then `tmuxp load -y pentest`. `tl gen tmux pentest` prints the YAML
without writing anything.

## 8. Troubleshooting

| You see | Do this |
|---|---|
| `error: tmux not found — install tmux >= 3.4` | install tmux (section 1) |
| `error: tmuxp not found — pipx install tmuxp` | `pipx install tmuxp` |
| `command not found: tmux-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing tmux-pentest ...` | the name was taken: use `tl launch tmux pentest`, or put `--force` in your `tl init` line (section 6) |
| `error: directory /home/you/ops/pentest does not exist (create it, or launch with DIR, '.' or --new NAME)` | `mkdir -p ~/ops/pentest`, or `tmux-pentest .`, or `tmux-pentest --new NAME` |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; tmux will open those panes in $HOME` | a tab of that workflow points to a missing directory; create it (`claude-projects`: edit it, section 4) |
| `error: --run-commands is Herdr-only (tmux and Zellij always run pane commands)` | drop the option: tmux always starts the pane commands |
| `sessions should be nested with care, unset $TMUX to force` | you are already inside tmux: switch with `Ctrl+b` `s`, or `tmux switch-client -t pt-acme` |
| Keys do nothing | release `Ctrl+b` before pressing the next key |
| tmux vanished, the shell says `suspended` | `Ctrl+b` `Ctrl+z` suspends tmux (Ctrl held too long): type `fg` |
| Running the shortcut again opens the old session | that is on purpose (section 7): kill it first to rebuild |

## 9. Learn more

- `tl help launch` and `tl help init`: every option, in the terminal; `tl launch -h`: examples.
- `Ctrl+b` `?` inside tmux; `man tmux`.
- [Zellij tutorial](zellij.md) · [Herdr tutorial](herdr.md) · [all GIFs](../README.md#learn-it-in-6-gifs)

![The tl commands](demo/06-cli.gif)

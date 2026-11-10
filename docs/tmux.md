# Tmux for beginners, with Terminal-layouts

tmux keeps your terminals alive in **sessions** that survive closing the window or losing an SSH
connection. A session holds **windows** (tabs, listed in the status bar at the bottom), and each window
is split into **panes**. Terminal-layouts turns every workflow into a ready-made session.

![Every workflow in tmux](demo/02-tmux.gif)

**Contents:** [1 Install](#1-install) · [2 First session](#2-your-first-session) ·
[3 Keys](#3-the-keys-you-need) · [4 Sessions](#4-managing-sessions) · [5 Recipes](#5-recipes) ·
[6 Troubleshooting](#6-troubleshooting)

This page covers what is specific to tmux. Every workflow, option and `tl` command is in
[Commands and options](usage.md).

## 1. Install

You need **tmux 3.4+** and **tmuxp**, which loads the layouts.

```bash
sudo apt install tmux pipx       # Ubuntu 24.04+ / Debian 13+   (macOS: brew install tmux pipx)
pipx ensurepath                  # then open a new terminal, so ~/.local/bin is on your PATH
pipx install tmuxp
tmux -V && tmuxp --version
```

`tmux -V` older than 3.4 (Ubuntu 22.04 ships 3.2a, Debian 12 3.3a)? Install a newer tmux, for example
with Homebrew.

Then install `tl` and enable the shell commands: [Install](../README.md#install), three lines.

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

Type `tmux-` and press `Tab` to see the other workflows.

## 3. The keys you need

Six keys are enough to work in a session. "`Ctrl+b` `d`" means: press `Ctrl+b`, release, press `d`.

| To do this | Press |
|---|---|
| **Detach** (session keeps running) | `Ctrl+b` `d` |
| Next / previous window | `Ctrl+b` `n` / `Ctrl+b` `p` |
| Move to the pane left / right / up / down | `Ctrl+b` `←` `→` `↑` `↓` |
| **Zoom** the pane to full window, and back | `Ctrl+b` `z` |
| **Scroll** back through output | `Ctrl+b` `[`, then `↑` `↓` `PageUp` `PageDown`; `q` leaves |
| List every key | `Ctrl+b` `?` (`q` leaves) |

The mouse is off by default. To click panes and windows, drag borders and scroll with the wheel:

```bash
echo 'set -g mouse on' >> ~/.tmux.conf
tmux source-file ~/.tmux.conf    # apply to the running server
```

Everything else (splitting, resizing, copying text, renaming) is in the official
[tmux Getting Started guide](https://github.com/tmux/tmux/wiki/Getting-Started) and in `man tmux`.

## 4. Managing sessions

| Shortcut | Same as | Does |
|---|---|---|
| `tmux-ls` | `tmux list-sessions` | list sessions |
| `tmux-attach <session>` | `tmux attach -t <session>` | go back into a session (`Tab` completes names) |
| `tmux-kill <session>` | `tmux kill-session -t <session>` | stop one session and everything running in it |
| `tmux-kill-all` | `tmux kill-server` | stop **every** tmux session, including ones you made by hand |
| `t` | `tmux` | the multiplexer itself, e.g. `t ls` |

Two things are specific to tmux:

- `-d` creates the session **detached**, so you stay where you are: `tmux-pentest --new acme -d`.
- tmux stores `.` and `:` in session names as `_`, so `my.app` becomes `pt-my_app`.

## 5. Recipes

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

## 6. Troubleshooting

| You see | Do this |
|---|---|
| `error: tmux not found — install tmux >= 3.4` | install tmux (section 1) |
| `error: tmuxp not found — pipx install tmuxp` | `pipx install tmuxp` |
| `command not found: tmux-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing tmux-pentest ...` | the name was taken: see [Names your shell already has](usage.md#names-your-shell-already-has) |
| `error: directory /home/you/ops/pentest does not exist (create it, or launch with DIR, '.' or --new NAME)` | `mkdir -p ~/ops/pentest`, or `tmux-pentest .`, or `tmux-pentest --new NAME` |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; tmux will open those panes in $HOME` | a tab of that workflow points to a missing directory; create it, or for `claude-projects` [edit the workflow](workflows.md#changing-a-workflow) |
| `error: --run-commands is Herdr-only (tmux and Zellij always run pane commands)` | drop the option: tmux always starts the pane commands |
| `sessions should be nested with care, unset $TMUX to force` | you are already inside tmux: switch with `Ctrl+b` `s`, or `tmux switch-client -t pt-acme` |
| Keys do nothing | release `Ctrl+b` before pressing the next key |
| tmux vanished, the shell says `suspended` | `Ctrl+b` `Ctrl+z` suspends tmux (Ctrl held too long): type `fg` |
| Running the shortcut again opens the old session | that is on purpose (section 5): kill it first to rebuild |

More: `Ctrl+b` `?` inside tmux, `man tmux`, `tl help launch`.

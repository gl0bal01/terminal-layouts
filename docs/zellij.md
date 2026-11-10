# Zellij for beginners, with Terminal-layouts

Zellij keeps your terminals alive in **sessions** you can detach from and come back to. A session holds
**tabs** (top bar), each split into **panes**, plus optional **floating panes**. The bar at the bottom
always shows the keys of the current mode, so you rarely need to remember them. Terminal-layouts turns
every workflow into a ready-made session.

![Every workflow in Zellij](demo/03-zellij.gif)

**Contents:** [1 Install](#1-install) · [2 First session](#2-your-first-session) ·
[3 Keys](#3-the-keys-you-need) · [4 Sessions](#4-managing-sessions) · [5 Recipes](#5-recipes) ·
[6 Troubleshooting](#6-troubleshooting)

This page covers what is specific to Zellij. Every workflow, option and `tl` command is in
[Commands and options](usage.md).

## 1. Install

You need a recent **Zellij** (CI tests 0.45.1). No tmuxp needed.

```bash
brew install zellij pipx         # macOS / Linuxbrew. Zellij also: cargo install --locked zellij, or a
                                 # release binary (github.com/zellij-org/zellij/releases); pipx also:
                                 # sudo apt install pipx
pipx ensurepath                  # then open a new terminal, so ~/.local/bin is on your PATH
zellij --version
```

Then install `tl` and enable the shell commands: [Install](../README.md#install), three lines.

## 2. Your first session

```bash
cd ~/projects/my-app
zellij-project                   # = tl launch zellij project
```

You are now *inside* Zellij, in a session named `my-app`, with the tabs `work` and `scratch` at the
top. Zellij works in **modes**: press `Ctrl+t` and the bottom bar switches to the keys of *Tab* mode;
press a key there (say `2` to go to tab 2), or `Esc` to go back.

To leave without stopping anything, **detach**: `Ctrl+o` then `d`. Everything keeps running:

```bash
zellij-ls                        # my-app [Created 2m ago]
zellij-attach my-app             # back where you were
```

Type `zellij-` and press `Tab` to see the other workflows.

## 3. The keys you need

The bar at the bottom shows the keys of the current mode, so this list is short. "`Ctrl+o` `d`" means:
press `Ctrl+o`, then `d`. `Esc` leaves a mode.

| To do this | Press |
|---|---|
| **Detach** (session keeps running) | `Ctrl+o` `d` |
| Go to a tab | `Ctrl+t`, then `1`…`9` or `←` `→` |
| Move to the pane left / right / up / down | `Alt+←` `→` `↑` `↓` |
| **Fullscreen** the pane, and back | `Ctrl+p` `f` |
| **Scroll** back through output | `Ctrl+s`, then `↑` `↓` `PageUp` `PageDown` |
| **Lock**: send every key to the program in the pane, until pressed again | `Ctrl+g` |
| **Quit**: end the session and **every program in it** | `Ctrl+q` |

The mouse is on by default: click panes and tabs, drag borders, scroll with the wheel.

**A key does not reach your program?** Zellij takes `Ctrl+p`, `Ctrl+t`, `Ctrl+s`, … for itself. Press
`Ctrl+g` (lock), use the program, then `Ctrl+g` again.

Everything else (splitting, resizing, floating panes, search, key presets) is in the official
[Zellij documentation](https://zellij.dev/documentation/).

## 4. Managing sessions

A session runs until you quit it (`Ctrl+q`) or kill it. Zellij can also keep a session that ended as
**exited** (resurrectable), marked `EXITED` in `zellij-ls`: `zellij-attach` brings its layout back
(the programs are not restarted; `zellij-attach -f <session>` runs them again), `zellij-delete`
forgets it.

| Shortcut | Same as | Does |
|---|---|---|
| `zellij-ls` | `zellij list-sessions` | list sessions, running and exited |
| `zellij-attach <session>` | `zellij attach <session>` | go back into a session, or bring an exited one back (`Tab` completes names) |
| `zellij-kill <session>` | `zellij kill-session <session>` | stop a running session |
| `zellij-kill-all` | `zellij kill-all-sessions` | stop every running session (asks first; `-y` skips the question) |
| `zellij-delete <session>` | `zellij delete-session <session>` | forget an exited session; `--force` stops a running one first |
| `zellij-delete-all` | `zellij delete-all-sessions` | forget every exited session (asks first; `-y` skips the question) |
| `z` | `zellij` | Zellij itself, e.g. `z ls` |

Inside Zellij, `Ctrl+o` `w` opens the session manager: switch to another session without detaching.

There is no detached start for Zellij (`-d` is tmux only): open the session, then `Ctrl+o` `d`.

zoxide also defines `z`. Terminal-layouts keeps zoxide's and says so once at startup: type `zellij`
instead. See [Names your shell already has](usage.md#names-your-shell-already-has).

## 5. Recipes

**One directory per engagement, resumed the next day**

```bash
zellij-pentest --new acme        # creates ~/ops/pentest/acme, session pt-acme
# Ctrl+o d ... close the terminal ... next morning:
zellij-attach pt-acme
```

Sessions survive closing the terminal and dropped SSH connections, **not a reboot**: save your work
before shutting down.

**Several workflows on one project**

```bash
cd ~/projects/my-app
zellij-project                   # session my-app; Ctrl+o d to detach
zellij-ai-agents                 # session ai-my-app
# inside: Ctrl+o w to switch between my-app and ai-my-app
```

Start sessions from a plain terminal, not from a Zellij pane: inside Zellij, `zellij-…` opens a second
Zellij within the pane. Detach first, or switch with `Ctrl+o` `w`.

**After editing the manifest:** layouts are generated fresh on every launch, but a session that
already exists keeps its old layout. Start it again from **outside** that session (detach first with
`Ctrl+o` `d`): `zellij-delete --force pt-acme; zellij-pentest --new acme`.

## 6. Troubleshooting

| You see | Do this |
|---|---|
| `error: zellij not found — see https://zellij.dev/documentation/installation` | install Zellij (section 1) |
| `command not found: zellij-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing z ...` | nothing to do: type `zellij` instead of `z` (section 4) |
| `Session with name "pt-acme" already exists. Use attach command to connect to it or specify a different name.` | `zellij-attach pt-acme`, or `--label` another name, or `zellij-delete --force pt-acme` first (section 5) |
| `error: directory /home/you/ops/pentest does not exist (create it, or launch with DIR, '.' or --new NAME)` | `mkdir -p ~/ops/pentest`, or `zellij-pentest .`, or `zellij-pentest --new NAME` |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; zellij will open those panes in $HOME` | a tab of that workflow points to a missing directory; create it, or for `claude-projects` [edit the workflow](workflows.md#changing-a-workflow) |
| A Zellij opens inside your Zellij pane | you launched from inside Zellij: detach (`Ctrl+o` `d`) and launch again, or switch with `Ctrl+o` `w` |
| `error: --detach is tmux-only` | drop `-d`; detach with `Ctrl+o` `d` |
| `error: --run-commands is Herdr-only (tmux and Zellij always run pane commands)` | drop the option: Zellij always starts the pane commands |
| `Ctrl+p` / `Ctrl+s` do something else in your editor | lock Zellij with `Ctrl+g` while you use it (section 3) |

More: `Ctrl+o` `c` inside Zellij (configuration), [zellij.dev/documentation](https://zellij.dev/documentation/),
`tl help launch`.

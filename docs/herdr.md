# Herdr for beginners, with Terminal-layouts

[Herdr](https://herdr.dev/) is a terminal workspace manager built for AI coding agents. A background
**server** keeps everything running; the `herdr` app you open is a client you can close and reopen.
The server holds **workspaces** (listed in the sidebar), each with **tabs**, each split into **panes**.
Terminal-layouts builds every workflow as a workspace in the running server. There is no layout file
to install.

![Every workflow as a Herdr workspace](demo/04-herdr.gif)

**Contents:** [1 Install](#1-install) · [2 First workspace](#2-your-first-workspace) ·
[3 Keys](#3-the-keys-you-need) · [4 Pane commands](#4-pane-commands) ·
[5 Workspaces](#5-managing-workspaces) · [6 Recipes](#6-recipes) ·
[7 Troubleshooting](#7-troubleshooting) · [8 Limits](#8-limits)

This page covers what is specific to Herdr. Every workflow, option and `tl` command is in
[Commands and options](usage.md).

## 1. Install

You need **Herdr 0.8.2 or newer** (tested on 0.8.2 and 0.9.5). Install it from
[herdr.dev](https://herdr.dev/), then check:

```bash
herdr --version
```

Then install `tl` and enable the shell commands: [Install](../README.md#install), three lines.

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

Type `herdr-` and press `Tab` to see the other workflows.

## 3. The keys you need

Herdr is mouse-first: click workspaces, tabs and panes, drag split borders, right-click for menus,
drag-select text to copy it. On the keyboard, every key starts with the **prefix**: press `Ctrl+b`,
release it, then the key.

| To do this | Press |
|---|---|
| **Detach** (everything keeps running) | `Ctrl+b` `q` |
| Pick a workspace | `Ctrl+b` `w` |
| Next / previous tab | `Ctrl+b` `n` / `Ctrl+b` `p` |
| Move to the pane left / down / up / right | `Ctrl+b` `h` / `j` / `k` / `l` |
| **Zoom** the pane, and back | `Ctrl+b` `z` |
| **Scroll** back through output | `Ctrl+b` `[`; `q` leaves |
| List every key | `Ctrl+b` `?` |

**tmux inside Herdr?** Both use `Ctrl+b`. Give Herdr another prefix: set `prefix = "ctrl+a"` under
`[keys]` in `~/.config/herdr/config.toml`, then reload with `Ctrl+b` `Shift+r`.

Everything else (splitting, resizing, renaming, the full key list) is in the official
[Herdr documentation](https://herdr.dev/tui/docs/).

## 4. Pane commands

tmux and Zellij always run the commands a workflow gives its panes (a `git status` watcher,
`docker stats`). In Herdr they are **off** by default, and every pane starts as a plain shell. To run
them:

```bash
tl gen herdr pentest             # read the plan first: prints it, touches nothing
herdr-pentest --run-commands     # then run every non-empty command in it
```

`--run-commands` applies to the whole workflow, and the security workflows contain network tools.
It never starts an agent: the bundled workflows leave agent panes empty.

## 5. Managing workspaces

Every `herdr-<workflow>` run creates a **new** workspace.

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

## 6. Recipes

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

Give each agent that writes code its own Git worktree, and review before you merge.

**From another terminal:** `herdr-<workflow>` also works outside Herdr. It targets your default Herdr
session (or `HERDR_SOCKET_PATH`); open `herdr` to see the result. Inside a Herdr pane it targets that
session.

**Opened one twice by mistake?** `herdr-ls`, then `herdr-close <id>`.

## 7. Troubleshooting

| You see | Do this |
|---|---|
| `error: Herdr executable not found; install Herdr first` | install Herdr (section 1) |
| `error: Herdr server unavailable; start 'herdr server' or open Herdr first` | run `herdr` (or `herdr server` in another terminal), then try again |
| `error: Herdr client/server protocol mismatch; restart the Herdr server` | you upgraded Herdr: `herdr server stop` (this **stops every pane and agent**: let them finish first), then `herdr` |
| `command not found: herdr-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing h ...` | the name was taken: see [Names your shell already has](usage.md#names-your-shell-already-has) |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; Herdr will open those panes in $HOME` | create that directory, or pass `DIR` / `.` / `--new NAME`; for `claude-projects` [edit the workflow](workflows.md#changing-a-workflow) |
| `error: --detach is tmux-only` | drop `-d`: the workspace is created in the server anyway |
| A launch failed halfway | nothing to clean up: tl closes the workspace it was building |
| An agent did not start | on purpose: type it in the pane (`--run-commands` only runs manifest commands) |

More: `Ctrl+b` `?` inside Herdr, [herdr.dev/tui/docs](https://herdr.dev/tui/docs/), `tl help herdr`.

## 8. Limits

The Herdr backend is experimental. It lays out the workspace and stops there.

- `tl` never starts a Herdr server and never starts an agent. Agent lifecycle, token use, cost
  tracking and Git worktrees stay with Herdr and the agents.
- It never closes a workspace that existed before, and never deletes a worktree. It only closes a
  workspace it just created and failed to finish.
- `close_on_exit: true` in a manifest is not honoured: a pane stays open after its command exits. The
  plan lists a warning.
- Tabs marked `tmux_only` or `zellij_only` are left out.
- `tl install` writes nothing for Herdr.

How the workspace is built, step by step: [Development](development.md#herdr-launcher).

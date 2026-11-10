# Zellij for beginners, with terminal-layouts

Zellij keeps your terminals alive in **sessions** you can detach from and come back to. A session holds
**tabs** (top bar), each split into **panes**, plus optional **floating panes**. The bar at the bottom
always shows the keys of the current mode, so you rarely need to remember them. terminal-layouts turns
every workflow into a ready-made session: one command and the whole workspace is there.

![Every workflow in Zellij](demo/03-zellij.gif)

**Contents:** [1 Install](#1-install) · [2 First session](#2-your-first-session) ·
[3 Keys](#3-the-keys-you-need) · [4 Every command](#4-every-command) · [5 Options](#5-options) ·
[6 Sessions](#6-managing-sessions) · [7 Recipes](#7-recipes) · [8 Troubleshooting](#8-troubleshooting) ·
[9 Learn more](#9-learn-more)

---

## 1. Install

You need a recent **Zellij** (CI tests 0.45.1) and **tl**, installed with [pipx](https://pipx.pypa.io/).
No tmuxp needed.

```bash
brew install zellij pipx         # macOS / Linuxbrew. Zellij also: cargo install --locked zellij, or a
                                 # release binary (github.com/zellij-org/zellij/releases); pipx also:
                                 # sudo apt install pipx
pipx ensurepath                  # then open a new terminal, so ~/.local/bin is on your PATH
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"
zellij --version && tl --version
```

`--force` replaces an older `tl` (the PyPI release predates the shell commands).

Then add the shell commands to `~/.zshrc` (bash: `~/.bashrc` and `tl init bash`), and open a new
terminal:

```bash
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc
layouts                          # lists every command it defined
```

Only want Zellij? Use `eval "$(command tl init zsh --backends zellij)"` instead of the line above.

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

## 3. The keys you need

Default Zellij 0.45 keys. "`Ctrl+t` `n`" means: press `Ctrl+t`, then `n` (no need to hold anything).
`Esc` or `Enter` leaves a mode.

**Without a mode** (work everywhere):

| To do this | Press |
|---|---|
| Move to the pane left / right / up / down (left/right continue to the next tab) | `Alt+←` `→` `↑` `↓` (or `Alt+h` `l` `k` `j`) |
| New pane | `Alt+n` |
| Show / hide floating panes | `Alt+f` |
| Bigger / smaller pane | `Alt+=` / `Alt+-` |
| Cycle pane arrangements | `Alt+[` / `Alt+]` |
| Move the tab left / right | `Alt+i` / `Alt+o` |
| **Lock**: send every key to the program in the pane, until pressed again | `Ctrl+g` |
| **Quit**: end the session and **every program in it** (to leave safely: `Ctrl+o` `d`) | `Ctrl+q` |

**Modes:**

| Mode | Enter with | Then |
|---|---|---|
| Pane | `Ctrl+p` | `n` new · `r` split right · `d` split down · `x` close · `f` **fullscreen** · `w` floating · `c` rename · arrows move |
| Tab | `Ctrl+t` | `1`…`9` go to tab · `←` `→` previous / next · `n` new · `x` close · `r` rename · `Tab` last tab |
| Resize | `Ctrl+n` | arrows grow the pane that way · `+` / `-` |
| Move | `Ctrl+h` | arrows move the pane itself |
| **Scroll** | `Ctrl+s` | `↑` `↓` `PageUp` `PageDown`, `u` / `d` half page · `s` **search** (type, `Enter`, then `n` / `p`) · `e` open the output in `$EDITOR` |
| Session | `Ctrl+o` | `d` **detach** · `w` session manager (switch to or create sessions) · `c` configuration |
| tmux | `Ctrl+b` | tmux-style keys: `%` `"` split · `c` new tab · `n` `p` tabs · `z` fullscreen · `d` detach · `[` scroll |

**Mouse:** on by default. Click panes and tabs, drag borders, scroll with the wheel. Selecting text
copies it.

**A key does not reach your program?** Zellij takes `Ctrl+p`, `Ctrl+t`, `Ctrl+s`, … for itself. Press
`Ctrl+g` (lock), use the program, `Ctrl+g` again; do it before an editor's own `Ctrl+q` too. If you picked the *Unlock-First* key preset in the
configuration screen (`Ctrl+o` `c`), it is the other way round: `Ctrl+g` first, then the mode key.

## 4. Every command

Each command is a shortcut for a `tl launch` line. Both take the same arguments.

| Shortcut | Same as | Opens in | Session name |
|---|---|---|---|
| `zellij-ai-agents` | `tl launch zellij ai-agents` | current directory | `ai-<directory>` |
| `zellij-claude-projects` | `tl launch zellij claude-projects` | `~/projects` | `claude-projects` |
| `zellij-ctf` | `tl launch zellij ctf` | `~/ops/ctf` | `ctf` |
| `zellij-docker` | `tl launch zellij docker` | `~/docker` | `docker` |
| `zellij-malware-analysis` | `tl launch zellij malware-analysis` | `~/ops/malware` | `malware-analysis` |
| `zellij-osint` | `tl launch zellij osint` | `~/ops/osint` | `osint` |
| `zellij-pentest` | `tl launch zellij pentest` | `~/ops/pentest` | `pentest` |
| `zellij-project` | `tl launch zellij project` | current directory | `<directory>` |

What each workflow contains (tabs and panes): [The 8 workflows](../README.md#the-8-workflows).
Directories come from the manifest; `tl help workflows` shows yours.

Type `zellij-` and press `Tab` to complete the name, then `Tab` again for directories and options.

`claude-projects` is a sample multi-project cockpit: its project tabs point at the author's own
directories. Edit them in your manifest before using it ([Customize](../README.md#customize)).

## 5. Options

| Shortcut | Same as | Effect |
|---|---|---|
| `zellij-pentest .` | `tl launch zellij pentest .` | open in the current directory, session `pt-<directory>` |
| `zellij-pentest ~/case` | `tl launch zellij pentest ~/case` | open in `~/case`, session `pt-case` (`--cwd DIR` is the same) |
| `zellij-pentest --new acme` | `tl launch zellij pentest --new acme` | create `~/ops/pentest/acme`, open it, session `pt-acme` |
| `zellij-pentest --label red-team` | `tl launch zellij pentest --label red-team` | choose the session name |

- Give **one** place: `DIR`, `.` or `--new NAME`, not two.
- The prefix (`pt-`, `ma-`, `os-`, …) keeps names apart: `zellij-pentest .` and `zellij-osint .` from
  the same directory give `pt-<dir>` and `os-<dir>`.
- There is no detached start for Zellij (`-d` is tmux only): open it, then `Ctrl+o` `d`.

## 6. Managing sessions

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

If a name was already taken in your shell (zoxide's `z`, for example), terminal-layouts keeps yours and
says so once at startup: nothing to do, type `zellij` instead of `z`. To replace such a name anyway,
change the line in `~/.zshrc` to `eval "$(command tl init zsh --force)"`; it replaces **every** taken
name, zoxide's `z` included.

## 7. Recipes

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

**Plain Zellij, without tl:** `tl install` writes every layout to `~/.config/zellij/layouts` (the only
`tl` command that writes there); then, outside Zellij, `zellij --layout pentest` (inside a session it
adds the tabs to that session instead). `tl gen zellij pentest` prints the KDL
without writing anything.

## 8. Troubleshooting

| You see | Do this |
|---|---|
| `error: zellij not found — see https://zellij.dev/documentation/installation` | install Zellij (section 1) |
| `command not found: zellij-pentest` | add the `eval "$(command tl init zsh)"` line, open a new terminal |
| `terminal-layouts: kept your existing z ...` | nothing to do: type `zellij` instead of `z` (`--force` would also replace zoxide's `z`, section 6) |
| `Session with name "pt-acme" already exists. Use attach command to connect to it or specify a different name.` | `zellij-attach pt-acme`, or `--label` another name, or `zellij-delete --force pt-acme` first (section 7) |
| `error: directory /home/you/ops/pentest does not exist (create it, or launch with DIR, '.' or --new NAME)` | `mkdir -p ~/ops/pentest`, or `zellij-pentest .`, or `zellij-pentest --new NAME` |
| `error: /home/you/case is not a directory` | the `DIR` you gave does not exist: create it (`mkdir -p ~/case`) or fix the path |
| `warning: directory ... does not exist; zellij will open those panes in $HOME` | a tab of that workflow points to a missing directory; create it (`claude-projects`: edit it, section 4) |
| A Zellij opens inside your Zellij pane | you launched from inside Zellij: detach (`Ctrl+o` `d`) and launch again, or switch with `Ctrl+o` `w` |
| `error: --detach is tmux-only` | drop `-d`; detach with `Ctrl+o` `d` |
| `error: --run-commands is Herdr-only (tmux and Zellij always run pane commands)` | drop the option: Zellij always starts the pane commands |
| `Ctrl+p` / `Ctrl+s` do something else in your editor | lock Zellij with `Ctrl+g` while you use it (section 3) |

## 9. Learn more

- `tl help launch` and `tl help init`: every option, in the terminal; `tl launch -h`: examples.
- `Ctrl+o` `c` inside Zellij (configuration); [zellij.dev/documentation](https://zellij.dev/documentation/).
- [tmux tutorial](tmux.md) · [Herdr tutorial](herdr.md) · [all GIFs](../README.md#learn-it-in-6-gifs)

![The tl commands](demo/06-cli.gif)

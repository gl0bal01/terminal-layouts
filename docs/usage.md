# Commands and options

Everything here works the same in tmux, Zellij and Herdr. For the keys and session handling of one
backend, read its tutorial: [Tmux](tmux.md) · [Zellij](zellij.md) · [Herdr](herdr.md).

**Contents:** [Shell commands](#shell-commands) · [Opening a workflow](#opening-a-workflow) ·
[Where it opens and what it is called](#where-it-opens-and-what-it-is-called) ·
[Sessions](#sessions) · [The tl command](#the-tl-command) ·
[Names your shell already has](#names-your-shell-already-has) ·
[Static layouts](#static-layouts)

## Shell commands

One line in `~/.zshrc` (bash: `~/.bashrc` and `tl init bash`) defines every command and its tab
completion:

```bash
eval "$(command tl init zsh)"
```

Run `layouts` to list what it defined. A workflow you add to the manifest gets its commands
automatically.

To define the commands of some backends only, add `--backends`, a comma-separated list of `tmux`,
`zellij` and `herdr`: `eval "$(command tl init zsh --backends tmux)"`.

## Opening a workflow

`<backend>-<workflow>` opens a workflow. It is a shortcut for `tl launch <backend> <workflow>` and
takes the same arguments.

| Workflow | Opens in | Prefix | tmux / Zellij session | Herdr workspace |
|---|---|---|---|---|
| `ai-agents` | current directory | `ai-` | `ai-<directory>` | `ai-<directory>` |
| `claude-projects` | `~/projects` | `cp-` | `claude-projects` | `Claude Projects` |
| `ctf` | `~/ops/ctf` | `ctf-` | `ctf` | `CTF` |
| `docker` | `~/docker` | `dk-` | `docker` | `Docker` |
| `malware-analysis` | `~/ops/malware` | `ma-` | `malware-analysis` | `Malware Analysis` |
| `osint` | `~/ops/osint` | `os-` | `osint` | `OSINT` |
| `pentest` | `~/ops/pentest` | `pt-` | `pentest` | `Pentest` |
| `project` | current directory | none | `<directory>` | `<directory>` |

This table describes the bundled manifest; `tl help workflows` prints the same for the manifest you
use. The tabs and panes of each workflow are in [Workflows](workflows.md).

## Where it opens and what it is called

Shown with `tmux-pentest`; `zellij-pentest` and `herdr-pentest` take the same arguments.

| Command | Opens in | Name |
|---|---|---|
| `tmux-pentest` | `~/ops/pentest`, the directory of the workflow | `pentest` |
| `tmux-pentest .` | the current directory | `pt-<directory>` |
| `tmux-pentest ~/case` | `~/case` (`--cwd ~/case` is the same) | `pt-case` |
| `tmux-pentest --new acme` | `~/ops/pentest/acme`, created if missing | `pt-acme` |
| `tmux-pentest --label red-team` | the directory of the workflow | `red-team` |

- Give one place at most: `DIR`, `.`, `--cwd DIR` or `--new NAME`.
- The prefix keeps names apart: `tmux-pentest .` and `tmux-osint .` from the same directory give
  `pt-<directory>` and `os-<directory>`.
- Options combine: `tmux-pentest --new acme --label red-team`.
- Two options belong to one backend each: `-d` starts a tmux session detached, and `--run-commands`
  makes Herdr run the pane commands (tmux and Zellij always run them).

![Options: directory, --new, --label, detached](demo/05-options.gif)

## Sessions

| | tmux | Zellij | Herdr |
|---|---|---|---|
| List | `tmux-ls` | `zellij-ls` | `herdr-ls` |
| Go back in | `tmux-attach <session>` | `zellij-attach <session>` | open `herdr` |
| Stop one | `tmux-kill <session>` | `zellij-kill <session>` | `herdr-close <id>` |
| Stop all | `tmux-kill-all` | `zellij-kill-all` | |
| Forget exited sessions | | `zellij-delete <session>` · `zellij-delete-all` | |
| The tool itself | `t` | `z` | `h` |

What each one does exactly: [Tmux](tmux.md#4-managing-sessions) ·
[Zellij](zellij.md#4-managing-sessions) · [Herdr](herdr.md#5-managing-workspaces).

## The tl command

| Command | Does |
|---|---|
| `tl launch BACKEND WORKFLOW [options]` | open a workflow; what every `<backend>-<workflow>` runs |
| `tl list` | list the workflow ids |
| `tl gen BACKEND WORKFLOW` | print the tmuxp YAML, the Zellij KDL or the Herdr plan; touches nothing |
| `tl validate` | check every manifest against the schema |
| `tl init zsh\|bash` | print the shell commands and completion |
| `tl install` | write static layouts to `~/.config` ([below](#static-layouts)) |
| `tl help [TOPIC]` | the manual; topics: `workflows`, `launch`, `init`, `herdr`, `install` |

`tl -h` gives an overview and `tl COMMAND -h` the options and examples of one command. `tl help` is
generated from your manifest and also lists the environment variables, exit codes and files touched.

![The tl commands: help, list, gen, validate, launch, install](demo/06-cli.gif)

## Names your shell already has

`tl init` never replaces a name that exists in your shell, such as zoxide's `z` or an alias `t`. It
keeps yours and lists the kept names once at startup. You can then:

- do nothing, and type `tmux`, `zellij` or `herdr` (or `tl launch ...`) instead of the kept name;
- hide the notice with `TL_INIT_QUIET=1`;
- replace **every** kept name with `eval "$(command tl init zsh --force)"`.

## Static layouts

The commands above generate a fresh layout on every launch and write nothing to `~/.config`. To use
plain `tmuxp` or `zellij` without `tl`, write the layouts once:

```bash
tl install                   # ~/.config/tmuxp/*.yaml and ~/.config/zellij/layouts/*.kdl
tmuxp load -y pentest
zellij --layout pentest      # from outside Zellij; inside a session it adds the tabs to that session
```

Files with those names are overwritten. Run it again after editing the manifest. Herdr has no layout
file, so `tl install` does not apply to it.

# AI-agent workspaces: tmux, Zellij and Herdr

The canonical YAML manifest can now produce **three** backends. Herdr is different from tmuxp and Zellij: it exposes a running server with workspace/tab/pane APIs, rather than accepting a static layout file. The generated JSON is a deterministic, inspectable **execution plan**, not a Herdr config file.

## Quick start

Prerequisites: Python 3.10+ and Herdr 0.8.2 or newer (tested against 0.8.2 and 0.9.5). Herdr support is newer than the PyPI release (0.1.0), so install `tl` from the repository:

~~~sh
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"
echo 'source ~/terminal-layouts/shell/herdr-layouts.zsh' >> ~/.zshrc   # helpers + tab completion (clone needed)
~~~

Then, with Herdr running (`herdr`, or `herdr server` headless):

~~~sh
cd ~/projects/my-app
hag                              # = tl launch herdr ai-agents --cwd "$PWD"   (workspace "my-app")
hpt-new acme                     # = tl launch herdr pentest --new acme       (~/ops/pentest/acme, "pt-acme")
hma .                            # = tl launch herdr malware-analysis --cwd "$PWD"
hls                              # list workspaces;  hk <id> closes one;  hh shows every helper
tl gen herdr ai-agents           # inspect the plan only; touches nothing
~~~

`tl launch herdr <workflow>` options:

| Option | Effect |
|---|---|
| `--cwd DIR` | Run the workflow in `DIR` instead of its manifest directory (tabs with their own `cwd` keep it). The workspace is named after `DIR` unless `--label` is given. |
| `--new NAME` | Create `<workflow dir>/NAME` and launch there, named `<prefix>NAME` (`pt-`, `ma-`, …, from the manifest). |
| `--label TEXT` | Workspace name shown in Herdr. |
| `--run-commands` | Also run the manifest pane commands (see below). |

Tab completion (zsh and bash) covers `tl` subcommands, targets, workflow names and options, the helpers, and `hk <TAB>` (live workspace ids with their labels). It is enabled by sourcing any of `shell/{tmux,zellij,herdr}-layouts.zsh`; in zsh, source them after `compinit` (oh-my-zsh does that for you).

Run inside a Herdr pane, `tl launch` targets that session; otherwise it targets the default session (or `HERDR_SOCKET_PATH`).

Agent panes start as ordinary shells. Enter **opencode**, **pi**, **claude** or **codex** manually in the corresponding pane. No agent process, provider API call, or shell watcher is started automatically by this backend.

To **explicitly** execute nonempty manifest pane commands (for example the git-status watcher), opt in:

~~~sh
tl launch herdr ai-agents --run-commands
~~~

This opt-in applies to *all* nonempty commands in the chosen workflow. Review the YAML first; workflows such as security tooling can contain network or other side-effectful commands. Do not use the flag casually.

## How the adapter works

1. Validate the manifest against the existing JSON Schema and resolve `$paths.*` / `~` references (tab and pane level).
2. Generate the versioned JSON plan with stable ordering. Repeat runs produce byte-identical output for the same environment.
3. Check the Herdr executable and that `herdr status server --json` reports a running, protocol-compatible server; never auto-start a server.
4. Create the workspace, first tab and root pane, then create subsequent tabs. Every pane is created with an explicit `--cwd`: its own pane `cwd`, else the tab's, else the workflow's, else the directory you launch from. Relative paths are anchored at the parent directory (pane → tab → workflow), and `$PWD` / `${PWD}` always mean the directory you launch from.
5. Split panes using Herdr's real CLI and returned IDs, preserving *nested topology* by creating sibling boundaries before descending into child trees. Manifest `size` percentages become `--ratio` values; unsized siblings share what is left equally. Sizes that cannot add up (over 100 %, or leaving nothing for unsized siblings) are scaled to fit and listed as plan warnings.
6. Rename panes, give the manifest's focused pane the tab focus (`split --focus`), focus the chosen tab, and optionally execute pane commands.

If any step fails, the workspace created by that run is closed again and the error names the failing Herdr command, so a failed launch leaves the server as it was.

Herdr's CLI command forms and response IDs are documented at https://herdr.dev/tui/docs/cli-reference/ . The installed version of **herdr --help** is authoritative.

## Limitations and safety

- *close_on_exit: true* is not honoured: like the tmuxp and Zellij outputs, a pane stays open after its command exits. The plan lists a warning when a manifest asks for it.
- Tabs labeled *tmux_only* or *zellij_only* are omitted from Herdr plans.
- A pane directory that does not exist is reported as a warning before launch; Herdr itself would silently open that pane in `$HOME`.
- Commands are not run by default. Agent identity, agent lifecycle, token use, cost tracking, Git worktree creation and agent coordination remain Herdr/agent responsibilities, **not** capabilities of this adapter.
- Re-running *tl launch* creates another workspace; only *tl gen* is idempotent.
- The launcher never closes preexisting workspaces or deletes worktrees; it only closes a workspace it just created and failed to finish.
- *tl install* still installs only tmuxp and Zellij layouts. Herdr uses its CLI rather than a static install directory.

For safe parallel development, use separate Git worktrees per writing agent and perform an explicit review before merging.

## Validation

~~~sh
make test        # plan determinism, every manifest, mocked-CLI adapter tests, shell helpers + completion (bash and zsh)
make e2e-herdr   # live: real Herdr server, every workflow (no mocks)
make ci          # every CI job locally on HEAD; `make hooks` runs it on each pushed commit
~~~

`make e2e-herdr` downloads the pinned Herdr release (sha256-checked, linux-x86_64), or uses `HERDR_BIN=/path/to/herdr` (also forwarded by `make ci`). It starts a throwaway server with its own HOME, XDG config/state/cache/data/runtime directories and socket, so a Herdr session you are working in is never touched. For every workflow it checks against the live server: tab labels and order, active tab, pane names, split directions and ratios, on-screen sibling order, focused pane, pane directories and that no command runs without `--run-commands`. It also checks `--run-commands`, the shell helpers under bash and zsh (`hag`, `hpt-new`, `hls`, `hk`), rollback after a mid-launch failure, the stopped-server error and the missing-directory warning. CI runs the same target on every push and pull request.

# AI-agent workspaces: tmux, Zellij and Herdr

The canonical YAML manifest can now produce **three** backends. Herdr is different from tmuxp and Zellij: it exposes a running server with workspace/tab/pane APIs, rather than accepting a static layout file. The generated JSON is a deterministic, inspectable **execution plan**, not a Herdr config file.

## Quick start

Prerequisites: Python 3.10+, project dependencies, and a recent Herdr CLI. Start Herdr normally or run its headless server in another terminal.

~~~sh
tl validate
tl gen tmux ai-agents
tl gen zellij ai-agents
tl gen herdr ai-agents > ai-agents.herdr.json
herdr server                     # in another terminal, unless already running
tl launch herdr ai-agents        # create only workspace/tabs/panes
~~~

Agent panes start as ordinary shells. Enter **opencode**, **pi**, **claude** or **codex** manually in the corresponding pane. No agent process, provider API call, or shell watcher is started automatically by this backend.

To **explicitly** execute nonempty manifest pane commands (for example the git-status watcher), opt in:

~~~sh
tl launch herdr ai-agents --run-commands
~~~

This opt-in applies to *all* nonempty commands in the chosen workflow. Review the YAML first; workflows such as security tooling can contain network or other side-effectful commands. Do not use the flag casually.

## How the adapter works

1. Validate the manifest against the existing JSON Schema and resolve directory references.
2. Generate the versioned JSON plan with stable ordering. Repeat runs produce byte-identical output for the same environment.
3. Check the Herdr executable and running server; never auto-start a server.
4. Create the workspace, first tab and root pane, then create subsequent tabs.
5. Split panes using Herdr's real CLI and returned IDs, preserving *nested topology* by creating sibling boundaries before descending into child trees.
6. Rename panes, focus the chosen tab, and optionally execute pane commands.

Herdr's CLI command forms and response IDs are documented at https://herdr.dev/tui/docs/cli-reference/ . The installed version of **herdr --help** is authoritative.

## Limitations and safety

- Herdr pane *size*, pane-level focus and *close_on_exit* have no exact mapping in this version; the JSON plan lists warnings rather than silently asserting parity.
- Multi-child pane splits preserve tree structure, not necessarily exact fractional widths/heights.
- Tabs labeled *tmux_only* or *zellij_only* are omitted from Herdr plans.
- A pane-level directory incompatible with its existing root terminal directory is rejected at launch. Prefer tab-level *cwd*.
- Commands are not run by default. Agent identity, agent lifecycle, token use, cost tracking, Git worktree creation and agent coordination remain Herdr/agent responsibilities, **not** capabilities of this adapter.
- Re-running *tl launch* creates another workspace; only *tl gen* is idempotent.
- An error during layout creation may leave a partial workspace for inspection; the launcher never closes preexisting workspaces or deletes worktrees.
- *tl install* still installs only tmuxp and Zellij layouts. Herdr uses its CLI rather than a static install directory.

For safe parallel development, use separate Git worktrees per writing agent and perform an explicit review before merging.

## Validation

~~~sh
make test
python3 -m unittest discover -s tests -p 'test_herdr.py' -v
~~~

Tests cover plan determinism, all canonical manifests, nested splitting and shell/agent command opt-in. They use a mocked Herdr CLI and therefore do **not** certify a live Herdr server integration; a real-server smoke test is recommended before merging.

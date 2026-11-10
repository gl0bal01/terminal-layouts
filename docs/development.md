# Development

How to work on Terminal-layouts itself: set up a clone, run the checks, and find your way around the
code. To change a workflow without touching the code, read [Workflows](workflows.md) instead.

**Contents:** [Setup](#setup) · [Make targets](#make-targets) · [How it works](#how-it-works) ·
[Repository layout](#repository-layout) · [Tests](#tests) · [CI](#ci) ·
[Herdr launcher](#herdr-launcher) · [Recording the GIFs](#recording-the-gifs)

## Setup

```bash
git clone https://github.com/gl0bal01/terminal-layouts && cd terminal-layouts
pip install pyyaml jsonschema    # the only runtime dependencies (Python 3.10+)
make doctor                      # which of python3, tmux, tmuxp, zellij, herdr are installed
make test
make hooks                       # optional: run the full CI before every git push
```

Inside the clone, `python3 -m terminal_layouts.cli` is the working-tree `tl`, and it is what Make
uses. To put your working tree on `PATH` as `tl`, run `pipx install --force --editable .`

## Make targets

`make` on its own lists them.

| Target | Does |
|---|---|
| **Check** | |
| `make test` | `schema` + `parity` + idempotence + the unit tests (generators, launchers, shell commands under bash and zsh, docs links) |
| `make schema` | validate every manifest against `schema.json` (`tl validate`) |
| `make parity` | generate tmux and Zellij layouts and fail if they describe different workspaces |
| `make e2e` | `e2e-herdr` + `e2e-mux` |
| `make e2e-herdr` | launch every workflow on a real, throwaway Herdr server and compare the result with the manifest |
| `make e2e-mux` | the same on real, isolated tmux and Zellij |
| `make ci` | every CI job, locally, on the committed tree (`scripts/ci-local.sh`) |
| `make hooks` | enable the pre-push hook that runs `make ci` on each pushed commit |
| `make doctor` | report which tools are installed |
| **Generate** | |
| `make all` | `tmux` + `zellij` + `herdr` |
| `make tmux` | write `dist/tmux/*.yaml` |
| `make zellij` | write `dist/zellij/*.kdl` |
| `make herdr` | write `dist/herdr/*.json` (inert plans) |
| `make list` | list the workflows |
| `make clean` | remove `dist/` |
| **Install** | |
| `make install` | write static layouts to `~/.config` (`tl install`, from the working tree) |
| `make setup` | `make install`, then print the line to add to `~/.zshrc` |

`dist/` is a build artifact and is ignored by git.

Variables you can override on the command line:

| Variable | Default | Use |
|---|---|---|
| `PYTHON` | `python3` | the interpreter, e.g. a venv: `make test PYTHON=.venv/bin/python` |
| `HERDR_BIN` | pinned download in `.cache/herdr/` | your own Herdr build for `e2e-herdr` (`make ci` forwards it) |
| `ZELLIJ_BIN` | pinned download in `.cache/zellij/` | your own Zellij build for `e2e-mux` (`make ci` forwards it) |

`make test` needs zsh. `make e2e` also needs tmux and tmuxp. The pinned Herdr and Zellij binaries are
downloaded for linux-x86_64 and checked against a sha256; on another platform, pass `HERDR_BIN` and
`ZELLIJ_BIN`. To bump a pinned release, change its version and sha256 together at the top of the
`Makefile`.

## How it works

```
manifest/workflows/*.yaml ──┬──► gen_tmux   ──► tmuxp YAML ──► tmuxp load
   (single source of truth) ├──► gen_zellij ──► KDL layout ──► zellij --layout
                            └──► gen_herdr  ──► JSON plan  ──► launch_herdr ──► herdr CLI ──► running server
```

Every generator is a pure function of the manifest: same input, same bytes out. tmux and Zellij
receive a layout file. Herdr has no layout format, so `gen_herdr` produces a plan (an ordered list of
steps) that `launch_herdr` carries out through the `herdr` CLI.

For tmux and Zellij, `tl launch` generates the layout into a temporary file each time, then hands it
to the backend, so nothing on disk can go stale. `tl install` is the one command that writes layouts to `~/.config`.

Tab structure and emojis are canonical from the Zellij side; the tmux output is generated to match.

## Repository layout

```
terminal_layouts/             the Python package (the tl command)
  cli.py                      argument parsing, one function per command
  common.py                   manifest loading, path and $paths.* resolution
  validate.py                 schema validation, unique prefixes
  gen_tmux.py  gen_zellij.py  gen_herdr.py      the three generators
  launch_mux.py               tl launch for tmux and Zellij
  launch_herdr.py             tl launch for Herdr: carries out the plan
  shell_init.py               tl init: the shell commands
  shell/completion.{zsh,bash} tab completion, inlined by tl init
  manual.py                   tl help, generated from the manifest
  manifest/                   schema.json, defaults.yaml, workflows/*.yaml (bundled in the wheel)
tests/                        see below
docs/                         this documentation; demo/ holds the GIFs and their tapes
scripts/ci-local.sh           every CI job, locally
.githooks/pre-push            runs ci-local.sh on each pushed commit
Makefile  pyproject.toml
```

## Tests

| Check | Where | Fails when |
|---|---|---|
| Schema | `make schema` | a manifest does not match `schema.json`, or two workflows share a prefix |
| Parity | `tests/test-parity.sh` | the tmux and Zellij outputs differ in tabs, panes or names |
| Idempotence | `tests/test-idempotence.sh` | generating twice gives different bytes (Herdr plans included) |
| Unit | `tests/test_*.py` | generators, launchers (with a mocked CLI), `tl help`, shell commands and completion under bash and zsh |
| Docs | `tests/test_docs.py` | a command or option is missing from the docs, or a link, image or anchor leads nowhere |
| Live | `tests/herdr_live.py`, `tests/mux_live.py` | a real server ends up with tabs, panes, split ratios, focus or directories that differ from the manifest |

The Herdr live test also covers `--run-commands` (and that no command runs without it), the shell
commands under bash and zsh, rollback after a failure in the middle of a launch, the stopped-server
error and the missing-directory warning.

The live tests start their own servers with a private HOME, XDG directories and sockets. A tmux,
Zellij or Herdr session you are working in is never touched.

## CI

GitHub Actions runs `make test` on Python 3.10 and 3.12 and `make e2e` on 3.12, on every push to
`main` and every pull request.

`make ci` runs the same jobs locally, in the same order, each on a clean export of `HEAD` in a fresh
venv. Uncommitted changes are therefore **not** tested: commit first. It runs every job even after a
failure, then prints a pass/fail summary with a log path per job (`.cache/ci-local/`). It needs
[uv](https://docs.astral.sh/uv/), zsh and tmux. The PyPI upload is the one step it cannot run.

A CI step added to `.github/workflows/` goes into `scripts/ci-local.sh` in the same commit.

## Herdr launcher

`tl launch herdr` does this, in order:

1. Validate the manifest and resolve `$paths.*` and `~`.
2. Generate the plan. `tl gen herdr WORKFLOW` prints it.
3. Check that the `herdr` executable exists and that `herdr status server --json` reports a running
   server with a compatible protocol. It never starts a server.
4. Create the workspace, its first tab and root pane, then the other tabs. Every pane gets an
   explicit `--cwd`: its own, else the tab's, else the workflow's, else the directory you launch
   from. Relative paths resolve against the parent (pane, tab, workflow); `$PWD` always means the
   directory you launch from.
5. Split panes with the ids the CLI returns. Sibling boundaries are created before descending into a
   child tree, which preserves nesting. `size` percentages become `--ratio` values, and siblings
   without a size share the rest equally. Sizes that cannot add up (over 100 %, or nothing left for
   unsized siblings) are scaled to fit and listed as plan warnings.
6. Rename the panes, focus the manifest's focused pane and tab, and run the pane commands if
   `--run-commands` was given.

If a step fails, the workspace created by that run is closed and the error names the failing `herdr`
command, so a failed launch leaves the server as it was. A pane directory that does not exist is
reported as a warning before launch, because Herdr would silently open that pane in `$HOME`.

The Herdr CLI is documented at <https://herdr.dev/tui/docs/cli-reference/>; `herdr --help` of the
installed version is authoritative. What the backend does not do: [Limits](herdr.md#8-limits).

## Recording the GIFs

The GIFs in `docs/demo/` are real recordings made with [vhs](https://github.com/charmbracelet/vhs)
from the `.tape` files next to them. `docs/demo-env.sh` builds a throwaway environment under
`/tmp/tldemo` with its own HOME and its own tmux, Zellij and Herdr servers.

```bash
bash docs/demo-env.sh && vhs docs/demo/01-install.tape           # 01 starts without tl installed
bash docs/demo-env.sh --install && vhs docs/demo/02-tmux.tape && bash docs/demo-env.sh --stop    # 02 to 06
```

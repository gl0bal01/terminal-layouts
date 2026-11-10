<div align="center">

# terminal-layouts

**One declarative manifest → reproducible tmux, Zellij *and* Herdr workspaces. Zero drift, by construction.**

Stop hand-maintaining terminal layouts that silently fall out of sync.
Describe each workspace **once**; tmux, Zellij and Herdr all open it from the same source of truth.

<br>

![Install terminal-layouts and enable the shell commands](docs/demo/01-install.gif)

<sub><code>pipx install</code>, one line in <code>~/.zshrc</code>, then every workflow is <code>tmux-…</code>, <code>zellij-…</code> or <code>herdr-…</code> + Tab. <a href="#learn-it-in-6-gifs">Learn it in 6 GIFs ↓</a></sub>

</div>

---

## The problem this solves

tmux and Zellij speak different dialects — tmux consumes `tmuxp` YAML, Zellij consumes KDL — so
the *same* workspace ends up encoded **twice**, in two syntaxes, usually in two repos. Over time they
diverge: an emoji here, a renamed pane there, a window present in one and missing in the other. That
divergence is not a one-off bug you fix; it is the **steady-state outcome** of keeping two
hand-written sources in sync by discipline alone.

`terminal-layouts` removes the second source. A single schema-validated manifest is the only thing you
edit. Deterministic generators emit both outputs from it, and **parity is enforced by the build** — a
structural-equivalence test fails CI the moment the two ever describe different workspaces.

> The manifest is the contract; the `.yaml`/`.kdl` files are disposable build artifacts.
> You stop maintaining outputs and start maintaining intent.

### Why adopt this as your main terminal config

- **Single source of truth** — edit one field, regenerate both multiplexers. No copy-paste, no dialect translation.
- **Drift is impossible** — JSON Schema + parity + idempotence run in CI on every change.
- **Switch multiplexers freely** — the same workspace exists in tmux *and* Zellij. Try Zellij without rebuilding your muscle memory or your layouts.
- **Batteries included** — 8 workflows (dev, DevOps, security, research) ship ready to use.
- **Reproducible everywhere** — `pipx install` and one line in `~/.zshrc` reproduce your exact workspaces on any machine.
- **Zero lock-in** — outputs are plain `tmuxp`/Zellij files; the manifest is portable YAML.

| | Two hand-written repos | terminal-layouts |
|---|---|---|
| Source of truth | duplicated (YAML *and* KDL) | **single manifest** |
| Drift between tmux/Zellij | inevitable, manual to catch | **impossible (parity test)** |
| Add / rename a pane | edit two files, two syntaxes | **edit one field** |
| Correctness | eyeballed | **schema + parity + idempotence in CI** |
| Distribution | `git clone` + hand-copy | `pipx install` + one shell line |
| Output | committed artifacts that rot | regenerated on demand |

---

## Quick start

```bash
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc    # bash: tl init bash, in ~/.bashrc
exec zsh

layouts                      # every command, with directories and descriptions
tmux-pentest --new acme      # tmux:   ~/ops/pentest/acme, session pt-acme
zellij-docker                # Zellij: ~/docker
herdr-ai-agents              # Herdr:  this directory, workspace ai-<directory>
tl help                      # the manual
```

Each backend needs its own tool: tmux 3.4+ with tmuxp, Zellij, or Herdr 0.8.2+. `tl install` also
writes static layouts to `~/.config` for plain `tmuxp load` / `zellij --layout`. The PyPI release
(0.1.0) predates `tl launch`, the shell commands and Herdr; install from the repository as above.

**New to tmux, Zellij or Herdr?** One beginner tutorial per terminal: install, the keys you need,
every command with its `tl` equivalent, recipes and troubleshooting —
[tmux](docs/tmux.md) · [Zellij](docs/zellij.md) · [Herdr](docs/herdr.md).

---

## Learn it in 6 GIFs

Every command is `<backend>-<workflow>`; `layouts` lists them all, `tl help` explains them. Each GIF
is a real recording (throwaway HOME, canned data in the monitor panes), rendered from `docs/demo/*.tape`.

**1 · Install** — `pipx install`, one `eval` line, `layouts`, Tab on `tmux-` / `zellij-` / `herdr-`.

![Install and enable the shell commands](docs/demo/01-install.gif)

**2 · tmux** — every workflow: `tmux-ai-agents`, `tmux-claude-projects`, `tmux-ctf`, `tmux-docker`,
`tmux-malware-analysis`, `tmux-osint`, `tmux-pentest`, `tmux-project`; then `tmux-ls`, `tmux-kill-all`.

![Every workflow in tmux](docs/demo/02-tmux.gif)

**3 · Zellij** — the same workflows, same names: `zellij-<workflow>`, `zellij-ls`, `zellij-kill-all`.

![Every workflow in Zellij](docs/demo/03-zellij.gif)

**4 · Herdr** — `herdr-<workflow>` creates each workspace in the running Herdr; `herdr-ls`, `herdr-close <id>`.

![Every workflow as a Herdr workspace](docs/demo/04-herdr.gif)

**5 · Options** — `.` / `DIR` (open there, named `<prefix><dir>`), `--new NAME`, `--label`, `-d`,
`tmux-ls` · `tmux-attach` · `tmux-kill`.

![Options: directory, --new, --label, detached](docs/demo/05-options.gif)

**6 · The `tl` commands** — `tl -h`, the `tl help` manual (paged; `tl help <topic>` + Tab), `tl list`,
`tl gen`, `tl validate`, `tl launch` (what every `<backend>-<workflow>` runs), `tl install`, `tl launch -h`.

![The tl commands: help, list, gen, validate, launch, install](docs/demo/06-cli.gif)

Re-record them with `bash docs/demo-env.sh` + [vhs](https://github.com/charmbracelet/vhs) (see the
comment at the top of each tape).

---

## Herdr backend (experimental)

[Herdr](https://herdr.dev/) has no layout file: `tl` builds the workspace in the running Herdr server.
Agents are never started for you, and manifest pane commands run only with `--run-commands`. Tabs,
panes, sizes, focus and directories match the Zellij layout; `make e2e` checks every workflow against
a real Herdr (0.8.2+, tested on 0.8.2 and 0.9.5), in CI too. Start with the
[Herdr tutorial](docs/herdr.md); internals and limits: [AI-agent workspaces](docs/ai-agents.md).

---

## The 8 workflows

Each workflow is a set of named, emoji-tagged tabs with purpose-built panes. Structure and emojis are
**canonical from the Zellij side**; the tmux output is generated to match exactly.

### 🖥️ `project` — focused single project
The everyday driver. A `work` tab (editor/agent on the left, live `git status` + logs on the right)
plus a `scratch` tab. Open it in any directory.

| Tab | Panes |
|---|---|
| 🖥️ work | editor/agent · git status (auto-refresh) · logs |
| 🧪 scratch | two free shells |

### 🏠 `claude-projects` — multi-project cockpit
Run several projects at once. A `cockpit` overview tab, one dev tab per active project, and a scratch.
Each project tab carries its own agent + git + logs trio.

| Tab | Panes |
|---|---|
| 🏠 cockpit | monitor · shell · usage |
| 🔍 brand-search · 🛒 scout-contracts · 🏗️ contracts-agents · 🏗️ content-factory-contracts · 📦 x-bot | claude · git · logs (per project) |
| 🧪 scratch | two free shells |

### `ai-agents` — AI agent workbench
A coordinated shell workspace with cockpit, implementation, research and review tabs. OpenCode, Pi, Claude Code and Codex are started manually so API usage remains explicit. The same manifest works with tmuxp, Zellij and Herdr (see the [Herdr backend](docs/ai-agents.md)).

### 🐳 `docker` — containers & Compose
Compose control on the left; **live** `docker ps` and `docker stats` watchers on the right; a debug tab
for `exec`-ing into containers.

| Tab | Panes |
|---|---|
| 🐳 stack | compose · live container status · images |
| 📜 logs | logs · live resource stats |
| 🔧 debug | exec into container · build |

### 🎯 `pentest` — penetration testing
A full engagement, tab by tab. Recon → exploit → post-exploitation → loot, with a live `ss` socket
monitor and a `ps` process monitor wired in.

| Tab | Panes |
|---|---|
| 🎯 recon | scanner · enum · netmon (live `ss`) · notes |
| ⚔️ exploit | msf · payload · listener · proxy |
| 🔓 post | session · pivot · procmon (live `ps`) · loot-drop |
| 📝 loot | cracker · report · shell |

### 🔬 `malware-analysis` — reverse engineering
Static → dynamic → network → IOC, with live file/process/connection monitors for detonation.

| Tab | Panes |
|---|---|
| 🔬 static | inspect · disasm · hex · yara |
| 🧪 dynamic | trace · sandbox · procmon · filemon |
| 🌐 network | capture · dns · conntrack · fakenet |
| 📋 ioc | hashes · strings-out · report · shell |

### 🎯 `osint` — open-source intelligence
Target profiling → web/infra → social → timeline, with notes and evidence panes kept alongside.

| Tab | Panes |
|---|---|
| 🎯 target | recon · infra · ip-lookup · notes |
| 🌐 web | wayback · metadata · tech-stack · certificates |
| 📡 social | profiles · email · leaks · phone |
| 🗂️ timeline | report · correlate · evidence · shell |

### 🏁 `ctf` — capture the flag
A cockpit plus a tab per category: web, pwn, crypto, forensics, misc. (No timer pane — deliberately
dropped as noise.)

| Tab | Panes |
|---|---|
| 🏁 cockpit | notes · shell · submit |
| 🌐 web | requests · source · proxy · exploit |
| 💥 pwn | debugger · disasm · exploit · checksec |
| 🔐 crypto | python · script · tools · shell |
| 🔎 forensics | analyze · hex · carve · pcap |
| 🧰 misc | solve · recon · decode · shell |

---

## Shell commands

`eval "$(command tl init zsh)"` (bash: `tl init bash`) defines one command per workflow and backend,
`<backend>-<workflow>`, the same as `tl launch <backend> <workflow>`, plus session commands and tab
completion. A new workflow gets its commands automatically.

| | tmux | Zellij | Herdr |
|---|---|---|---|
| open | `tmux-<workflow>` | `zellij-<workflow>` | `herdr-<workflow>` |
| where / name | `.` · `DIR` · `--new NAME` · `--label NAME` | same | same |
| extra option | `-d` (detached) | — | `--run-commands` |
| list | `tmux-ls` | `zellij-ls` | `herdr-ls` |
| attach | `tmux-attach <s>` | `zellij-attach <s>` | — |
| kill / close | `tmux-kill <s>` · `tmux-kill-all` | `zellij-kill <s>` · `zellij-kill-all` · `zellij-delete[-all]` | `herdr-close <id>` |
| the tool itself | `t` | `z` | `h` |

Names your shell already has (zoxide's `z`, an alias) are kept and listed once at startup; `--force`
in the `tl init` line replaces them, `TL_INIT_QUIET=1` hides the notice. Every option, per terminal:
[tmux](docs/tmux.md) · [Zellij](docs/zellij.md) · [Herdr](docs/herdr.md), or `tl help init`.

<details>
<summary>Coming from the old short aliases?</summary>

They are replaced by readable names; `source shell/*-layouts.zsh` lines still work (they now call `tl init`), but one `eval` line is faster.

| old (tmux · Zellij · Herdr) | new |
|---|---|
| `tag` · `zag` · `hag` | `tmux-ai-agents` · `zellij-ai-agents` · `herdr-ai-agents` |
| `tai` · `zp`/`zai` · `hai` | `tmux-claude-projects` · `zellij-claude-projects` · `herdr-claude-projects` |
| `tproject` · `zo <dir>`/`zproject` · `hproject` | `tmux-project` · `zellij-project <dir>` · `herdr-project` (project runs in the current directory) |
| `tdk` `tpt` `tma` `tos` `tctf` (same with `z…`, `h…`) | `tmux-docker` `tmux-pentest` `tmux-malware-analysis` `tmux-osint` `tmux-ctf` (same with `zellij-`, `herdr-`) |
| `tpt .` · `tpt-new acme` | `tmux-pentest .` · `tmux-pentest --new acme` |
| `tls` `ta` `tks` `tka` | `tmux-ls` `tmux-attach` `tmux-kill` `tmux-kill-all` |
| `zls` `za` `zks` `zka` `zds` `zda` | `zellij-ls` `zellij-attach` `zellij-kill` `zellij-kill-all` `zellij-delete` `zellij-delete-all` |
| `hls` · `hks`/`hk` | `herdr-ls` · `herdr-close` |
| `th` `zh` `hh` (`thelp` `zhelp` `hhelp`) | `layouts` |

`TL_ALWAYS_REGEN` and the `TMUX_LAYOUTS_*` variables are gone: layouts are always fresh, and paths
come from `defaults.yaml` / `TL_MANIFEST_DIR`.

</details>

---

## Help

`tl help` is the manual, generated from the manifest you use (workflows, every command and option,
environment, exit codes, files touched), paged on a terminal and plain text when piped.

```bash
tl -h               # overview: 3 examples + the commands
tl help             # the whole manual
tl help launch      # one part: workflows, launch, init, herdr, install (Tab completes)
tl launch -h        # one command: options, examples, what it touches
```

---

## Customize

Workflows live in `terminal_layouts/manifest/workflows/*.yaml` (format below). In a clone:

```bash
git clone https://github.com/gl0bal01/terminal-layouts && cd terminal-layouts
make test       # schema + parity + idempotence + unit + bash/zsh tests
make help       # every target: doctor, install, e2e (real Herdr/tmux/Zellij), ci, hooks, ...
```

`tl` uses the manifest bundled when it was installed: point `TL_MANIFEST_DIR` at
`terminal_layouts/manifest` in your clone (or any tree of your own), or reinstall with
`pipx install --force .`, to use your edits.
Directory roots (`~/ops/pentest`, …) live in `defaults.yaml` (`paths:`); a workflow's `prefix:` names
the sessions opened from a directory (`prefix: pt-` → `pt-acme`) and must be unique (`tl validate`).

### Manifest format

```yaml
id: project
name: Projet
cwd: $PWD                     # or $paths.<root> from defaults.yaml
tabs:
  - id: work
    name: work
    emoji: 🖥️
    focus: true
    panes:
      - direction: row         # left | right  (Zellij vertical split)
        children:
          - id: claude
            size: 70%
            focus: true
            command: ""        # empty = plain shell (decorated on tmux)
          - direction: column  # top | bottom (Zellij horizontal split)
            size: 30%
            children:
              - id: git
                command: watch -n 5 -c git status -sb
              - id: logs
```

Key fields:
- `direction: row` → panes side-by-side. Maps to Zellij `split_direction="vertical"`, tmux `main-vertical`, Herdr `pane split --direction right`.
- `direction: column` → panes stacked. Maps to Zellij `split_direction="horizontal"`, Herdr `pane split --direction down`.
- `size` → Zellij `size`, tmux `main-pane-width`, Herdr `--ratio` (unsized siblings share the rest).
- `cwd` on a tab → every backend; on a pane → honoured by Herdr only (relative paths resolve against the tab).
- `command` + `args[]` → a program with discrete arguments (use `args` when an argument contains spaces, e.g. a `--format` string).
- `tmux_only` / `zellij_only` on a tab → emit for one target only.
- `$paths.*` → reference a root defined in `defaults.yaml`.

---

## How it works

```
manifest/workflows/*.yaml ──┬──► gen_tmux   ──► ~/.config/tmuxp/*.yaml   (tmuxp)
   (single source of truth) ├──► gen_zellij ──► ~/.config/zellij/layouts/*.kdl
                            │        │
                            │        └──► parity test: both must describe the same workspace
                            └──► gen_herdr  ──► JSON plan ──► tl launch herdr ──► running Herdr server
                                                                   │
                                     live e2e test: server state ◄─┘ must match the manifest
```

```
terminal-layouts/
├── terminal_layouts/             # Python package (the `tl` CLI)
│   ├── cli.py  common.py  gen_tmux.py  gen_zellij.py  validate.py
│   ├── gen_herdr.py  launch_herdr.py  launch_mux.py  shell_init.py  manual.py (tl help)
│   ├── shell/completion.{zsh,bash}   # inlined by `tl init`
│   └── manifest/                 # source of truth (bundled in the wheel)
│       ├── schema.json  defaults.yaml
│       └── workflows/*.yaml      # the 8 workflows
├── shell/                        # compatibility wrappers around `tl init`
├── tests/                        # parity, idempotence, unit, bash/zsh, live Herdr/tmux/Zellij
├── docs/                         # tmux.md zellij.md herdr.md (tutorials), ai-agents.md, demo/ (GIFs)
├── scripts/ci-local.sh           # every CI job, locally (`make ci`)
├── .githooks/pre-push            # `make hooks`
├── pyproject.toml  Makefile
```

## Quality gates

- **Schema** — every manifest validated against `schema.json`.
- **Parity** — tmux and Zellij outputs must be structurally equivalent (same tabs, same panes, same names).
- **Idempotence** — regenerating produces byte-identical output (Herdr plans included).
- **Live** — every workflow is launched on real, throwaway Herdr, tmux and Zellij servers (also through the bash/zsh commands) and the resulting tabs, panes, split ratios, focus and directories must match the manifest.

All of them run in CI on every push and PR (Python 3.10 + 3.12, plus a live Herdr job on a pinned, sha256-checked release). `make ci` runs the same jobs locally; `make hooks` runs it before each push.

## License

MIT

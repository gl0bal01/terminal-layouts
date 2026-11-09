<div align="center">

# terminal-layouts

**One declarative manifest → reproducible tmux *and* Zellij workspaces. Zero drift, by construction.**

Stop hand-maintaining two sets of terminal layouts that silently fall out of sync.
Describe each workspace **once**; generate both `tmuxp` YAML and Zellij KDL from the same source of truth.

`make install` and every workflow below lands in your config — ready to launch.

<br>

![Zellij malware-analysis layout](docs/zellij-malware.gif)

<sub>The <code>malware-analysis</code> workflow in Zellij — one manifest also generates the matching tmux layout.</sub>

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
- **Reproducible everywhere** — `make install` on any machine reproduces your exact workspaces; nothing to copy by hand.
- **Zero lock-in** — outputs are plain `tmuxp`/Zellij files; the manifest is portable YAML.

| | Two hand-written repos | terminal-layouts |
|---|---|---|
| Source of truth | duplicated (YAML *and* KDL) | **single manifest** |
| Drift between tmux/Zellij | inevitable, manual to catch | **impossible (parity test)** |
| Add / rename a pane | edit two files, two syntaxes | **edit one field** |
| Correctness | eyeballed | **schema + parity + idempotence in CI** |
| Distribution | `git clone` + hand-copy | `make install` (or `uvx`) |
| Output | committed artifacts that rot | regenerated on demand |

---

## Quick start

```bash
git clone https://github.com/gl0bal01/terminal-layouts
cd terminal-layouts

make doctor     # check tmux / tmuxp / zellij / herdr are present
make install    # write all 8 workflows to ~/.config (tmuxp + zellij)
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc     # shortcuts + tab completion (bash: tl init bash)
```

`make install` writes every workflow into your multiplexer config dirs:

- `~/.config/tmuxp/<workflow>.yaml`
- `~/.config/zellij/layouts/<workflow>.kdl`

Then open any workspace — `<backend>-<workflow>`, Tab completes, `layouts` lists everything:

```bash
tmux-docker                          # tmux:   docker workspace   (= tl launch tmux docker)
zellij-pentest --new acme            # Zellij: ~/ops/pentest/acme, session pt-acme
herdr-ai-agents                      # Herdr:  ai-agents here, named ai-<this directory>
tmuxp load -y docker                 # plain tmuxp / zellij --layout pentest still work
```

### Make targets

```bash
make all       # generate tmux + Zellij layouts and Herdr plans into ./dist (preview)
make install   # write layouts to ~/.config (tmuxp + zellij)
make doctor    # check required + recommended tools
make setup     # install + print the shell line to add
make test      # schema + parity + idempotence + unit + shell (bash/zsh) tests
make herdr     # generate Herdr JSON plans into ./dist/herdr
make e2e       # live tests: real Herdr, tmux and Zellij (throwaway servers)
make ci        # run every CI job locally (on HEAD)
make hooks     # run `make ci` on each pushed commit (pre-push hook)
make list      # list available workflows
make clean     # remove ./dist
```

### Install without cloning

The package is on [PyPI](https://pypi.org/project/terminal-layouts/).

**uvx** — run on demand, no install ([`uv`](https://docs.astral.sh/uv/) bootstraps Python if missing):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # one-time
uvx terminal-layouts install                       # write all layouts to ~/.config
uvx terminal-layouts gen tmux docker               # or emit one to stdout
```

**pipx** — install the `tl` command persistently:

```bash
pipx install terminal-layouts
tl install                                         # write all layouts to ~/.config
tl gen zellij pentest                              # or emit one to stdout
```

---

## Herdr backend (experimental)

[Herdr](https://herdr.dev/) is a live terminal workspace manager for AI coding agents. There is no
layout file to install: `tl` creates the workspace directly in the running Herdr.

**One-time setup**

```bash
pipx install --force "git+https://github.com/gl0bal01/terminal-layouts"   # Herdr support is newer than PyPI 0.1.0
echo 'eval "$(command tl init zsh)"' >> ~/.zshrc                                  # shortcuts + tab completion
```

**Every day**

```bash
herdr                 # start Herdr (or work from a pane inside it)
cd ~/projects/my-app
herdr-ai-agents                # ai-agents workbench here, workspace named "ai-my-app"
herdr-pentest --new acme       # pentest in ~/ops/pentest/acme, workspace "pt-acme"
herdr-malware-analysis .       # malware-analysis in the current directory
herdr-ls                       # list workspaces   ·  herdr-close <id>   ·  layouts  (everything)
```

Same commands without shortcuts: `tl launch herdr <workflow> [DIR|.] [--new NAME] [--label TEXT]`,
and `tl gen herdr <workflow>` prints the plan without touching Herdr. Agents are never started for you:
type `opencode`, `pi`, `claude` or `codex` in a pane. Manifest pane commands run only with `--run-commands`.

Tabs, panes, sizes, focus and directories match the Zellij layout; a failed launch closes the workspace
it created. Requires Herdr 0.8.2 or newer (tested on 0.8.2 and 0.9.5); `make e2e` checks every
workflow against a real Herdr server, in CI too. See [AI-agent workspaces](docs/ai-agents.md) for
details and limits.

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

## Shell commands (recommended)

One line in `~/.zshrc` (or `~/.bashrc` with `bash`) — no clone needed, any position in the file:

```bash
eval "$(command tl init zsh)"                        # every backend
eval "$(command tl init zsh --backends tmux,herdr)"  # only the ones you use
```

Nothing to memorise: every command is **`<backend>-<workflow>`**, generated from the manifest for
every workflow (a new workflow gets its commands automatically). Type `tmux-`, `zellij-` or `herdr-`
and press Tab; run **`layouts`** for the full list with directories and descriptions.

```bash
tmux-pentest                    # pentest in ~/ops/pentest        (= tl launch tmux pentest)
tmux-pentest .                  # ... in the current directory, session pt-<dir>
tmux-pentest --new acme         # ... in ~/ops/pentest/acme (created), session pt-acme
zellij-malware-analysis ~/case  # any directory
herdr-ai-agents                 # agent workbench here, workspace ai-<dir>
tmux-docker -d --label web      # tmux: -d = detached · Herdr: --run-commands
```

| sessions | tmux | Zellij | Herdr |
|---|---|---|---|
| list | `tmux-ls` | `zellij-ls` | `herdr-ls` |
| attach | `tmux-attach <s>` | `zellij-attach <s>` | — |
| kill / close | `tmux-kill <s>` · `tmux-kill-all` | `zellij-kill <s>` · `zellij-kill-all` · `zellij-delete[-all]` | `herdr-close <id>` |
| the multiplexer itself | `t` | `z` | `h` |

- **Tab completion** (zsh and bash) for `tl` and every command: workflow names, options, directories,
  live tmux/Zellij sessions and Herdr workspace ids.
- Names come from `<prefix><directory>` (`pt-acme`, `ai-my-app`): prefixes are unique per workflow,
  so two workflows opened from one directory never share a session.
- `command tl` keeps working when a plugin aliases `tl` (oh-my-zsh's tmux plugin does).
- **Your names win:** a name that already exists in your shell (zoxide's `z`, an oh-my-zsh alias, a
  command) is kept and listed once at startup. `tl init zsh --force` replaces them;
  `TL_INIT_QUIET=1` hides the notice.
- Layouts are generated fresh from the manifest on every launch, so they are never stale.
- Startup cost: about 0.1 s for `tl init`. To skip it, cache the output:
  `tl init zsh > ~/.cache/tl-init.zsh` and `source` that file (regenerate after upgrading `tl`).

**Coming from the old short aliases?** They are replaced by readable names; `source shell/*-layouts.zsh`
lines still work (they now call `tl init`), but one `eval` line is faster.

| old | new |
|---|---|
| `tpt`, `zpt` … (`tai`, `tdk`, `tma`, `tos`, `tctf`, `zp`) | `tmux-pentest`, `zellij-pentest` … (`*-claude-projects`, `*-docker`, `*-malware-analysis`, `*-osint`, `*-ctf`) |
| `tproject`, `zo <dir>` | `tmux-project`, `zellij-project <dir>` (project runs in the current directory) |
| `tpt-new acme` | `tmux-pentest --new acme` |
| `tpt .` | `tmux-pentest .` |
| `tls` `ta` `tks` `tka` | `tmux-ls` `tmux-attach` `tmux-kill` `tmux-kill-all` |
| `zls` `za` `zks` `zka` `zds` `zda` | `zellij-ls` `zellij-attach` `zellij-kill` `zellij-kill-all` `zellij-delete` `zellij-delete-all` |
| `th` `zh` (`thelp` `zhelp`) | `layouts` |

`TL_ALWAYS_REGEN` and the `TMUX_LAYOUTS_*` variables are gone: layouts are always fresh, and paths
come from `defaults.yaml` / `TL_MANIFEST_DIR`.

---

## Customize

Workflows live in `terminal_layouts/manifest/workflows/*.yaml`. Edit one, then:

```bash
make test       # validate against the schema + check parity (+ Herdr unit tests)
make install    # regenerate and write both outputs
```

Override the manifest tree without rebuilding via `TL_MANIFEST_DIR=/path/to/manifest`.
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
│   ├── gen_herdr.py  launch_herdr.py  launch_mux.py  shell_init.py
│   ├── shell/completion.{zsh,bash}   # inlined by `tl init`
│   └── manifest/                 # source of truth (bundled in the wheel)
│       ├── schema.json  defaults.yaml
│       └── workflows/*.yaml      # the 8 workflows
├── shell/                        # compatibility wrappers around `tl init`
├── tests/                        # parity, idempotence, unit, bash/zsh, live Herdr/tmux/Zellij
├── docs/                         # ai-agents.md (Herdr backend)
├── scripts/ci-local.sh           # every CI job, locally (`make ci`)
├── .githooks/pre-push            # `make hooks`
├── pyproject.toml  Makefile
```

## Quality gates

- **Schema** — every manifest validated against `schema.json`.
- **Parity** — tmux and Zellij outputs must be structurally equivalent (same tabs, same panes, same names).
- **Idempotence** — regenerating produces byte-identical output (Herdr plans included).
- **Live** — every workflow is launched on real, throwaway Herdr, tmux and Zellij servers (also through the bash/zsh shortcuts) and the resulting tabs, panes, split ratios, focus and directories must match the manifest.

All of them run in CI on every push and PR (Python 3.10 + 3.12, plus a live Herdr job on a pinned, sha256-checked release). `make ci` runs the same jobs locally; `make hooks` runs it before each push.

## License

MIT

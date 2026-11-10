# Workflows

A workflow is one YAML file: named tabs, each with a tree of panes. This page lists what the eight
bundled workflows contain, then shows how to change one or write your own.

**Contents:** [The bundled workflows](#the-bundled-workflows) ·
[Changing a workflow](#changing-a-workflow) · [Manifest format](#manifest-format)

## The bundled workflows

Pick one:

| | | | |
|:-:|:-:|:-:|:-:|
| 🖥️<br>**[project](#project)**<br>One project, one screen | 🤖<br>**[ai-agents](#ai-agents)**<br>Several coding agents, one project | 🏠<br>**[claude-projects](#claude-projects)**<br>Several projects at once | 🐳<br>**[docker](#docker)**<br>Containers and Compose |
| 🎯<br>**[pentest](#pentest)**<br>A full engagement, tab by tab | 🔬<br>**[malware-analysis](#malware-analysis)**<br>Reverse a sample, from static to IOC | 📡<br>**[osint](#osint)**<br>An investigation, with the evidence beside it | 🏁<br>**[ctf](#ctf)**<br>A cockpit and one tab per category |

Each one opens with `tmux-<name>`, `zellij-<name>` or `herdr-<name>`. The sketch under each workflow
shows its first tab. Session names and options: [Commands and options](usage.md#opening-a-workflow).

### project

🖥️ **One project, one screen.** The everyday driver: your editor or agent on the left, `git status` refreshing itself on the right, logs underneath.

`tmux-project` · `zellij-project` · `herdr-project` · opens in current directory

```text
work
┌────────────────────────────────────────┬─────────────────┐
│ editor / agent                         │ git             │
│                                        │ live git status │
│                                        ├─────────────────┤
│                                        │ logs            │
│                                        │                 │
└────────────────────────────────────────┴─────────────────┘
```

| Tab | Panes |
|---|---|
| 🖥️ work | editor or agent · `git status` (refreshes itself) · logs |
| 🧪 scratch | two free shells |

[↑ all workflows](#the-bundled-workflows)

### ai-agents

🤖 **Several coding agents, one project.** A coordinator in the cockpit, then one tab per role. Agent panes start as plain shells: you start OpenCode, Pi, Claude Code or Codex yourself, so API usage stays explicit.

`tmux-ai-agents` · `zellij-ai-agents` · `herdr-ai-agents` · opens in current directory

```text
cockpit
┌────────────────────────────┬─────────────────────────────┐
│ coordinator                │ git                         │
│                            │ live git status             │
│                            ├─────────────────────────────┤
│                            │ notes                       │
│                            │                             │
└────────────────────────────┴─────────────────────────────┘
```

| Tab | Panes |
|---|---|
| cockpit | coordinator · git (live status) · notes |
| implement | opencode · tests |
| research | pi · evidence |
| review | codex · diff (live `git diff --stat`) |

[↑ all workflows](#the-bundled-workflows)

### claude-projects

🏠 **Several projects at once.** An overview tab, one tab per project, and a scratch. This one is a **sample**: its project tabs point at the author's own directories, so [edit it](#changing-a-workflow) before you use it.

`tmux-claude-projects` · `zellij-claude-projects` · `herdr-claude-projects` · opens in `~/projects`

```text
cockpit
┌──────────────────────────────────┬───────────────────────┐
│ monitor                          │ usage                 │
│ btop                             │ ccusage               │
├──────────────────────────────────┤                       │
│ shell                            │                       │
│                                  │                       │
└──────────────────────────────────┴───────────────────────┘
```

| Tab | Panes |
|---|---|
| 🏠 cockpit | monitor (`btop`) · shell · usage (`ccusage`) |
| 🔍 brand-search · 🛒 scout-contracts · 🏗️ contracts-agents · 🏗️ content-factory-contracts · 📦 x-bot | claude · git (live status) · logs, in each |
| 🧪 scratch | two free shells |

[↑ all workflows](#the-bundled-workflows)

### docker

🐳 **Containers and Compose.** Compose on the left, the container list refreshing itself on the right, then tabs for logs and for getting inside a container.

`tmux-docker` · `zellij-docker` · `herdr-docker` · opens in `~/docker`

```text
stack
┌──────────────────────────────────┬───────────────────────┐
│ compose                          │ containers            │
│                                  │ live docker ps        │
│                                  ├───────────────────────┤
│                                  │ images                │
│                                  │                       │
└──────────────────────────────────┴───────────────────────┘
```

| Tab | Panes |
|---|---|
| 🐳 stack | compose · containers (live `docker ps`) · images |
| 📜 logs | logs · stats (a `docker stats` snapshot) |
| 🔧 debug | exec into a container · build |

[↑ all workflows](#the-bundled-workflows)

### pentest

🎯 **A full engagement, tab by tab.** Recon, exploit, post-exploitation, loot. A socket monitor and a process monitor run where you need them.

`tmux-pentest` · `zellij-pentest` · `herdr-pentest` · opens in `~/ops/pentest`

```text
recon
┌────────────────────────────────────────┬─────────────────┐
│ scanner                                │ netmon          │
│                                        │ live ss         │
├────────────────────────────────────────┼─────────────────┤
│ enum                                   │ notes           │
│                                        │                 │
└────────────────────────────────────────┴─────────────────┘
```

| Tab | Panes |
|---|---|
| 🎯 recon | scanner · enum · netmon (live `ss`) · notes |
| ⚔️ exploit | msf · payload · listener · proxy |
| 🔓 post | session · pivot · procmon (live `ps`) · loot-drop |
| 📝 loot | cracker · report · shell |

[↑ all workflows](#the-bundled-workflows)

### malware-analysis

🔬 **Reverse a sample, from static to IOC.** Static analysis, detonation with live process, file and connection monitors, network capture, then the IOC write-up.

`tmux-malware-analysis` · `zellij-malware-analysis` · `herdr-malware-analysis` · opens in `~/ops/malware`

```text
static
┌──────────────────────────────────┬───────────────────────┐
│ inspect                          │ hex                   │
│                                  │                       │
├──────────────────────────────────┼───────────────────────┤
│ disasm                           │ yara                  │
│                                  │                       │
└──────────────────────────────────┴───────────────────────┘
```

| Tab | Panes |
|---|---|
| 🔬 static | inspect · disasm · hex · yara |
| 🧪 dynamic | trace · sandbox · procmon (live `ps`) · filemon (live `ls /tmp`) |
| 🌐 network | capture · dns (live `ss`) · conntrack (live `ss`) · fakenet |
| 📋 ioc | hashes · strings-out · report · shell |

[↑ all workflows](#the-bundled-workflows)

### osint

📡 **An investigation, with the evidence beside it.** Profile the target, dig through web and infrastructure, cover social sources, then assemble the timeline.

`tmux-osint` · `zellij-osint` · `herdr-osint` · opens in `~/ops/osint`

```text
target
┌──────────────────────────────────┬───────────────────────┐
│ recon                            │ ip-lookup             │
│                                  │                       │
├──────────────────────────────────┼───────────────────────┤
│ infra                            │ notes                 │
│                                  │                       │
└──────────────────────────────────┴───────────────────────┘
```

| Tab | Panes |
|---|---|
| 🎯 target | recon · infra · ip-lookup · notes |
| 🌐 web | wayback · metadata · tech-stack · certificates |
| 📡 social | profiles · email · leaks · phone |
| 🗂️ timeline | report · correlate · evidence · shell |

[↑ all workflows](#the-bundled-workflows)

### ctf

🏁 **A cockpit and one tab per category.** Notes and flag submission in the cockpit, then a tab each for web, pwn, crypto, forensics and misc.

`tmux-ctf` · `zellij-ctf` · `herdr-ctf` · opens in `~/ops/ctf`

```text
cockpit
┌──────────────────────────────────┬───────────────────────┐
│ notes                            │ submit                │
│                                  │                       │
├──────────────────────────────────┤                       │
│ shell                            │                       │
│                                  │                       │
└──────────────────────────────────┴───────────────────────┘
```

| Tab | Panes |
|---|---|
| 🏁 cockpit | notes · shell · submit |
| 🌐 web | requests · source · proxy · exploit |
| 💥 pwn | debugger · disasm · exploit · checksec |
| 🔐 crypto | python · script · tools · shell |
| 🔎 forensics | analyze · hex · carve · pcap |
| 🧰 misc | solve · recon · decode · shell |

[↑ all workflows](#the-bundled-workflows)

## Changing a workflow

`tl` reads the manifest that was bundled when you installed it. To use your own, point
`TL_MANIFEST_DIR` at a manifest tree: a directory with `schema.json`, `defaults.yaml` and
`workflows/*.yaml`. The simplest tree is the one in a clone:

```bash
git clone https://github.com/gl0bal01/terminal-layouts && cd terminal-layouts
export TL_MANIFEST_DIR="$PWD/terminal_layouts/manifest"    # put this in ~/.zshrc, before the tl init line
$EDITOR terminal_layouts/manifest/workflows/claude-projects.yaml
tl validate                                # schema, and prefixes must be unique
tl gen zellij claude-projects              # look at the result; touches nothing
```

Without `TL_MANIFEST_DIR`, reinstall after each edit: `pipx install --force .`

- **A new workflow** is a new file in `workflows/`. Open a new shell and its `tmux-…`, `zellij-…` and
  `herdr-…` commands exist.
- **Directory roots** such as `~/ops/pentest` live under `paths:` in `defaults.yaml`. A workflow
  refers to one as `$paths.pentest`.
- **A session that is already open keeps its old layout.** Close it and launch again; each tutorial
  shows how ([Tmux](tmux.md#5-recipes), [Zellij](zellij.md#5-recipes)).

## Manifest format

The `project` workflow, shortened:

```yaml
id: project                    # the name in tmux-project, tl launch tmux project
name: Projet                   # display name (the Herdr workspace name)
prefix: ""                     # starts session names opened from a directory, e.g. pt- gives pt-acme
cwd: $PWD                      # where it opens: $PWD, a path, or $paths.<root> from defaults.yaml
tabs:
  - id: work
    name: work
    emoji: 🖥️
    focus: true                # the tab shown first
    panes:
      - direction: row         # children side by side
        children:
          - id: claude
            size: 70%
            focus: true        # the pane with the cursor
            command: ""        # empty = plain shell (tmux adds a title and a hint line)
          - direction: column  # children stacked
            size: 30%
            children:
              - id: git
                command: watch -n 5 -c git status -sb
              - id: logs
```

A workflow needs `id`, `name` and `tabs`; a tab needs `id`, `name` and `panes`. A pane is either a
leaf (it needs `id`) or a container (it needs `direction` and `children`), nested as deep as you like.

| Field | On | Meaning |
|---|---|---|
| `direction` | container | `row`: children side by side. `column`: children stacked |
| `size` | pane, container | share of the parent, such as `70%`; siblings without a size share the rest |
| `command` | pane | what runs in the pane; empty or absent means a plain shell |
| `args` | pane | arguments as a list, for an argument that contains spaces (a `--format` string) |
| `name`, `description` | pane | pane title (defaults to `id`); tmux prints the description as a hint in panes without a command |
| `focus` | tab, pane, container | the tab shown first, the pane with the cursor |
| `cwd` | workflow, tab | directory, for every backend; relative paths resolve against the parent. A static Zellij layout (`tl install`, `tl gen zellij`) carries the tab `cwd` only: the workflow `cwd` is applied by `tl launch` |
| `cwd` | pane | honoured by Herdr only |
| `tmux_only`, `zellij_only` | tab | emit the tab for that backend only (Herdr skips both) |
| `prefix` | workflow | session-name prefix; must be unique across workflows |

`schema.json` is the full reference, and `tl validate` checks your files against it.

How each field maps to the backends:

| Manifest | Zellij | Herdr |
|---|---|---|
| `direction: row` | `split_direction="vertical"` | `pane split --direction right` |
| `direction: column` | `split_direction="horizontal"` | `pane split --direction down` |
| `size` | `size` | `--ratio` |

Zellij and Herdr reproduce the pane tree exactly. tmux cannot nest freely, so its generator knows two
shapes: one pane beside a column of panes becomes `main-vertical`, with `main-pane-width` taken from
the `size` of the main pane; any other tree becomes `tiled`, with the panes in tree order. Every
backend gets the same tabs, panes and names.

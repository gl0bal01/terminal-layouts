# terminal-layouts

Unified manifest that generates both **tmux** (`tmuxp`) and **Zellij** layouts from a single source of truth.

> **Status**: skeleton. One workflow (`project`) is wired up as a proof of concept. The remaining 6 workflows (claude-projects, docker, pentest, malware-analysis, osint, ctf) will be ported next.

## Why

Two separate repos (`tmux-layouts` + `zellij-layouts`) drifted. Same 7 workflows, but different emojis, pane names, structures, and missing features on each side. This repo holds a single manifest and generates both outputs — divergence becomes impossible by construction.

## Layout

```
terminal-layouts/
├── manifest/
│   ├── schema.json           # JSON Schema for workflow manifests
│   ├── defaults.yaml         # paths, prefixes, emojis, defaults
│   └── workflows/
│       └── project.yaml      # one workflow (skeleton)
├── generators/
│   ├── common.py             # manifest loader + path resolver
│   ├── gen-tmux.py           # → dist/tmux/<wf>.yaml
│   ├── gen-zellij.py         # → dist/zellij/<wf>.kdl
│   └── validate.py           # schema validation
├── tests/
│   ├── test-parity.sh        # tmux/zellij structural equivalence
│   └── test-idempotence.sh   # re-run produces identical output
├── dist/                     # generated (gitignored)
└── Makefile
```

## Quick start

```bash
make all       # generate tmux + zellij layouts
make test      # schema + parity + idempotence
make list      # show available workflows
make clean     # remove dist/
```

## Manifest format (sketch)

```yaml
id: project
name: Projet
cwd: $paths.projects        # resolved from defaults.yaml
tabs:
  - id: work
    name: work
    emoji: 🖥️
    focus: true
    panes:
      - direction: row       # left | right (Zellij vertical split)
        children:
          - id: claude
            size: 70%
            focus: true
            command: ""
          - direction: column  # top | bottom (Zellij horizontal split)
            size: 30%
            children:
              - id: git
                command: watch -n 5 -c git status -sb
              - id: logs
                command: ""
  - id: scratch
    name: scratch
    emoji: 🧪
    panes:
      - direction: row
        children:
          - id: shell-1
          - id: shell-2
```

Key fields:
- `direction: row` = panes side-by-side (left|right). Maps to Zellij `split_direction="vertical"`, tmux `main-vertical` + `main-pane-width`.
- `direction: column` = panes stacked (top|bottom). Maps to Zellij `split_direction="horizontal"`, tmux side-panes stack.
- `tmux_only: true` / `zellij_only: true` on a tab = emit only for that target.
- `command: ""` = plain shell pane (with cosmetic decoration on tmux).
- `$paths.projects` = reference into `defaults.yaml`.

## Roadmap

- [x] Skeleton: schema + 1 workflow + 2 generators + Makefile + tests
- [ ] Port remaining 6 workflows from tmux-layouts/zellij-layouts
- [ ] Shared shell helpers (`shared/shell-helpers.sh`)
- [ ] Shell aliases (`tmux/tmux-layouts.zsh`, `zellij/zellij-layouts.zsh`)
- [ ] `.` (current directory) support for Zellij
- [ ] `make install`, `make doctor`, `make setup`
- [ ] CI (GitHub Actions): schema + parity + idempotence on every PR
- [ ] Migration guide + archive old repos

## License

MIT

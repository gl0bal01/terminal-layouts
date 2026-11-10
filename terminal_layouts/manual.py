"""`tl help [TOPIC]`: the manual, generated from the manifest.

Workflow directories and prefixes, and every <backend>-<workflow> and session
command, come from the manifest and shell_init: the manual lists exactly what
`tl init` defines. Plain text, at most 79 columns, no colour, nothing taken
from the terminal or the clock: one manifest gives byte-identical output.
"""
from __future__ import annotations

import functools
import textwrap

from terminal_layouts import __version__, shell_init

WIDTH = 79
TOPICS = ("workflows", "launch", "init", "herdr", "install")


def _wrap(text: str, indent: str, first: str | None = None) -> list[str]:
    # Never at a hyphen (tmux-malware-analysis); only a word longer than a line is cut.
    return textwrap.wrap(text, WIDTH, initial_indent=indent if first is None else first,
                         subsequent_indent=indent, break_on_hyphens=False)


def _intro() -> str:
    return f"""\
tl - terminal-layouts {__version__} manual

  One YAML manifest describes each workspace once: tabs, panes, sizes, focus,
  directories and commands. tl opens it as a tmux session (through tmuxp), a
  Zellij session or a Herdr workspace, generating the layout fresh each time,
  and defines shell commands so that opening one is a single word.
  Examples use the bundled workflows (pentest, docker, ...); WORKFLOWS and
  SHELL COMMANDS list the ones of the manifest in use.

  tl help              this manual, in a pager on a terminal (see ENVIRONMENT)
  tl help TOPIC        one part: {", ".join(TOPICS)}
  tl COMMAND -h        options and examples of one command
  tl help | grep -- --new    piped, the manual is plain text

QUICK START
  1. Add the shell commands to ~/.zshrc (bash: ~/.bashrc and tl init bash):
       eval "$(command tl init zsh)"
  2. Open a new shell and list what it defined:
       layouts
  3. Open a workflow; Tab completes commands, directories and options:
       tmux-pentest --new acme     creates ~/ops/pentest/acme, session pt-acme
       zellij-docker               ~/docker in Zellij, session docker
       herdr-ai-agents             this directory as Herdr workspace ai-<dir>
  4. Manage what is running:
       tmux-ls   tmux-attach pt-acme   tmux-kill pt-acme   herdr-ls
  5. Optional, for plain tmuxp load / zellij --layout: tl install
  Without the shell commands: tl launch tmux pentest --new acme

COMMANDS
  launch BACKEND WORKFLOW [DIR|.]   open a workflow          tl help launch
  init zsh|bash                     print shell commands     tl help init
  list                              workflow ids             tl help workflows
  gen tmux|zellij|herdr WORKFLOW    print a layout / Herdr plan to stdout
  validate                          check every manifest
  install                           write layouts to ~/.config  tl help install
  help [TOPIC]                      this manual
  --version                         print the version
"""


def _row(w: dict, width: int, dir_width: int) -> str:
    return f"  {w['id']:<{width}}  {w['dir']:<{dir_width}}  {w['prefix'] or '-'}"


def _workflows(rows: list[dict]) -> str:
    width = max([len("WORKFLOW"), *(len(w["id"]) for w in rows)])
    # Directories too long for one 79-column row get their own line instead.
    prefix_width = max([len("PREFIX"), *(len(w["prefix"] or "-") for w in rows)])
    dir_width = max([len("DIRECTORY"), *(len(w["dir"]) for w in rows
                                         if 2 + width + 2 + len(w["dir"]) + 2 + prefix_width <= WIDTH)])
    table = [f"  {'WORKFLOW':<{width}}  {'DIRECTORY':<{dir_width}}  PREFIX"]
    for w in rows:
        row = _row(w, width, dir_width)
        if len(row) <= WIDTH:
            table.append(row)
        else:
            table += [f"  {w['id']}", *_wrap(f"directory {w['dir']}", "      "),
                      f"      prefix {w['prefix'] or '-'}"]
        table += _wrap(w["description"], "      ")
    return f"""\
WORKFLOWS
  {len(rows)} workflow(s) in the manifest. DIRECTORY is where a workflow opens
  unless you give DIR, . or --new; PREFIX starts the names of sessions opened
  from a directory (pt- + acme = pt-acme). tl list prints the ids only.

{chr(10).join(table)}

  Edit workflows in a clone (terminal_layouts/manifest/workflows/ID.yaml) or
  point TL_MANIFEST_DIR at your own tree, then run tl validate. Directory
  roots (~/ops/pentest, ...) are the paths: of defaults.yaml. tl gen BACKEND
  WORKFLOW prints a layout or Herdr plan, without opening anything.
"""


LAUNCH = """\
LAUNCH
  tl launch BACKEND WORKFLOW [DIR|.] [--new NAME] [--label NAME] [-d]
            [--run-commands]
  BACKEND-WORKFLOW [same arguments]       the shell command, see tl help init

  BACKEND
    tmux     a tmux session, loaded by tmuxp (needs tmux and tmuxp)
    zellij   a new Zellij session (needs zellij)
    herdr    a workspace in the running Herdr server (see tl help herdr)

  Where it opens, and its name
    (nothing)       the workflow DIRECTORY (tl help workflows), named
                    WORKFLOW (Herdr: the workflow name, e.g. Pentest);
                    current-directory workflows open here, named
                    PREFIX<directory name>
    DIR, .          DIR (. = here), named PREFIX<DIR name>, e.g. pt-acme
    --cwd DIR       same as DIR
    --new NAME      create <workflow DIRECTORY>/NAME and missing parents
                    (an existing one is reused), open it there, named
                    PREFIXNAME; if the launch fails, NAME is removed again
                    when tl created it and it is still empty
    --label NAME    the session / workspace name, instead of the above
    -d, --detach    tmux only: create the session without attaching
    --run-commands  Herdr only: also run the manifest pane commands (tmux
                    and Zellij always run them)
  Give at most one of DIR, --cwd and --new. DIR may follow the options.
  tmux turns "." and ":" in session names into "_" (pt-my.app -> pt-my_app).
  A pane directory that does not exist is a warning: that pane opens in
  $HOME.

  Examples (bundled workflows)
    tl launch tmux pentest                ~/ops/pentest, session pentest
    tl launch zellij malware-analysis .   here, session ma-<this directory>
    tl launch tmux docker -d --label web  detached tmux session web
    tl launch herdr project ~/src/app     Herdr workspace app
"""


def _init(rows: list[dict]) -> str:
    lines = []
    for backend in shell_init.BACKENDS:
        option = shell_init.OPTIONS[backend]
        lines.append(f"  {backend}" + (f"   extra option {option.strip('[]')}" if option else ""))
        names = " ".join(f"{backend}-{w['id']}" for w in rows)
        lines += _wrap(names, " " * 11, "    open   ") or ["    open   (no workflows)"]
        for suffix, _body, text, _completer in shell_init.SESSIONS[backend]:
            lines.append(f"    {backend + '-' + suffix:<18} {text}")
        lines.append(f"    {shell_init.CORE[backend]:<18} = {backend} itself")
    return f"""\
SHELL COMMANDS
  tl init zsh|bash [--backends LIST] [--force]
  eval "$(command tl init zsh)"          in ~/.zshrc (bash: ~/.bashrc)

  tl init only prints shell code; eval defines, for every workflow and
  backend, BACKEND-WORKFLOW [DIR|.] [--new NAME] [--label NAME], which runs
  tl launch BACKEND WORKFLOW with the same arguments (tl help launch),
  plus session commands, and tab completion (zsh and bash) for all of them
  and for tl itself:

{chr(10).join(lines)}
  layouts              every command defined, with directories and prefixes

  --backends LIST   comma-separated subset of tmux,zellij,herdr (default: all)
  --force           replace commands or aliases you already have with these
                    names (without it they are kept)
  A name your shell already has (zoxide's z, an alias, a command) is kept
  and listed once at startup; TL_INIT_QUIET=1 hides that notice. bash in
  POSIX mode defines nothing (it forbids "-" in names). command tl still
  works when a plugin aliases tl. Faster startup: tl init zsh >
  ~/.cache/tl-init.zsh, source that file, regenerate it after upgrading tl
  or editing the manifest.
"""


HERDR = """\
HERDR
  Herdr has no layout file: tl launch herdr (and herdr-WORKFLOW) builds the
  workspace in the running Herdr server through the herdr CLI. Start Herdr
  first (herdr, or herdr server to run it headless); tl never starts one.
  Inside a Herdr pane it targets that server, otherwise the default one, or
  HERDR_SOCKET_PATH. Needs Herdr 0.8.2 or newer.

  Pane commands run only with --run-commands, and then every non-empty
  command of the Herdr plan (tl gen herdr WORKFLOW) runs: read it first.
  The bundled workflows leave agent panes empty: type opencode, pi, claude
  or codex in a pane yourself.

  herdr-ls                list workspaces (* = focused)
  herdr-close ID...       close workspaces (ids from herdr-ls; Tab completes)
  tl gen herdr WORKFLOW   print the JSON plan; touches nothing

  A failed launch closes the workspace it created. Every launch creates a
  new workspace. tl install does not apply to Herdr.
"""


INSTALL = """\
INSTALL
  tl install [--tmux-only | --zellij-only] [--tmuxp-dir DIR]
             [--zellij-dir DIR]

  Writes every workflow as a static layout, for plain tmuxp and zellij:
    $XDG_CONFIG_HOME/tmuxp/WORKFLOW.yaml           ~/.config/tmuxp
    $XDG_CONFIG_HOME/zellij/layouts/WORKFLOW.kdl   ~/.config/zellij/layouts
  Files with those names are overwritten; nothing else is touched. Then:
    tmuxp load -y pentest        zellij --layout pentest     (bundled pentest)
  --tmux-only / --zellij-only write one kind; --tmuxp-dir / --zellij-dir
  write elsewhere. tl launch and the shell commands do not need this: they
  generate the layout fresh every time. Re-run after editing the manifest.
"""


OUTRO = """\
ENVIRONMENT
  TL_MANIFEST_DIR     manifest tree (defaults.yaml, schema.json, workflows/)
                      to use instead of the one bundled with tl
  XDG_CONFIG_HOME     base of tl install's directories (default ~/.config)
  TL_INIT_QUIET=1     hide the "kept your existing ..." notice of tl init
  HERDR_SOCKET_PATH   Herdr server to use (read by the herdr CLI)
  MANPAGER, PAGER     pager for tl help on a terminal (default less -FRX)

FILES
  Only tl install writes to ~/.config. Everything else:
    help, list, gen, validate, init   read the manifest, print to stdout
    launch      tmux, Zellij: a temporary layout file, deleted when they exit
                or detach. Herdr: a new workspace. --new: creates the
                directory NAME (and missing parents)
  The session commands (tmux-kill, zellij-delete, herdr-close, ...) run
  tmux, zellij and herdr.

EXIT STATUS
  0   success
  1   failure: unknown workflow, missing tool, Herdr error, workflow
      directory missing (tmux, Zellij), invalid manifest (tl validate lists
      the problems)
  2   usage error: bad arguments or option combination, DIR that is not a
      directory, unknown help topic or init backend
  tl launch tmux|zellij exits with the status of tmuxp / zellij (128+N when
  it was killed by signal N, as in a shell).
"""


def render(topic: str | None = None) -> str:
    """The whole manual, or the section of one TOPICS entry."""
    rows = functools.cache(shell_init.workflows)  # loaded only by the parts that list workflows
    sections = {"workflows": lambda: _workflows(rows()), "launch": lambda: LAUNCH,
                "init": lambda: _init(rows()), "herdr": lambda: HERDR, "install": lambda: INSTALL}
    if topic is not None:
        return sections[topic]()
    return "\n".join([_intro(), *(sections[t]() for t in TOPICS), OUTRO])

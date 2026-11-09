# herdr-layouts.zsh — part of terminal-layouts
# Herdr workspace helpers. Source from ~/.zshrc (or ~/.bashrc):
#   source ~/terminal-layouts/shell/herdr-layouts.zsh
#
# Herdr is a live server, not a layout file, so there is nothing to install:
# every helper runs `tl launch herdr <workflow>` against the running Herdr
# (start it with `herdr`). From inside a Herdr pane the workspace is created
# in that session. Directories come from the manifest (defaults.yaml).
# Extra arguments go to `tl launch`, e.g.  hpt . --run-commands

command -v h >/dev/null 2>&1 || alias h='herdr'

_herdr_tl() {
  if ! command -v tl >/dev/null 2>&1; then
    printf '%s\n' "terminal-layouts: \`tl\` not found — pipx install terminal-layouts" >&2
    return 127
  fi
  tl launch herdr "$@"
}

# <workflow> [.] [tl launch args...]   "." = run in the current directory
_herdr_fixed() {
  local layout="$1"
  shift
  if [[ "${1:-}" == "." ]]; then
    shift
    _herdr_tl "$layout" --cwd "$PWD" "$@"
  else
    _herdr_tl "$layout" "$@"
  fi
}

# <usage> <workflow> <name> [tl launch args...]   <workflow dir>/<name>, label <prefix><name>
_herdr_new() {
  local usage="$1" layout="$2"
  shift 2
  if [[ -z "${1:-}" || "$1" == -* ]]; then
    echo "Usage: $usage"
    return 2
  fi
  local name="$1"
  shift
  _herdr_tl "$layout" --new "$name" "$@"
}

# Agent workbench in a directory (default: here), labelled with its name.
hag() {
  local dir="$PWD"
  if [[ -n "${1:-}" && "$1" != -* ]]; then
    dir="$1"
    shift
  fi
  _herdr_tl ai-agents --cwd "$dir" "$@"
}

# Project layout in the current directory, optionally with a workspace label.
hproject() {
  local label="${PWD##*/}"
  if [[ -n "${1:-}" && "$1" != -* ]]; then
    label="$1"
    shift
  fi
  _herdr_tl project --cwd "$PWD" --label "${label:-project}" "$@"
}

hai()  { _herdr_fixed claude-projects "$@"; }
hdk()  { _herdr_fixed docker "$@"; }
hpt()  { _herdr_fixed pentest "$@"; }
hma()  { _herdr_fixed malware-analysis "$@"; }
hos()  { _herdr_fixed osint "$@"; }
hctf() { _herdr_fixed ctf "$@"; }

hai-new()  { _herdr_new "hai-new <project-name>" project "$@"; }
hdk-new()  { _herdr_new "hdk-new <stack-name>" docker "$@"; }
hpt-new()  { _herdr_new "hpt-new <engagement>" pentest "$@"; }
hma-new()  { _herdr_new "hma-new <sample-name>" malware-analysis "$@"; }
hos-new()  { _herdr_new "hos-new <target-name>" osint "$@"; }
hctf-new() { _herdr_new "hctf-new <ctf-name>" ctf "$@"; }

# Workspaces: list (* = focused) and close by id.
hls() {
  local out
  out="$(herdr workspace list)" || return $?
  printf '%s' "$out" | python3 -c '
import json, sys
for w in json.load(sys.stdin)["result"]["workspaces"]:
    mark = "*" if w.get("focused") else " "
    wid, label, tabs, panes = w["workspace_id"], w["label"], w["tab_count"], w["pane_count"]
    print(f"{mark} {wid:<6} {label}  ({tabs} tabs, {panes} panes)")
'
}

hk() {
  if (( $# == 0 )); then
    echo "Usage: hk <workspace-id>...   (ids from hls)"
    return 2
  fi
  local id rc=0
  for id in "$@"; do
    if herdr workspace close "$id" >/dev/null; then echo "closed $id"; else rc=1; fi
  done
  return $rc
}

hh() {
  cat <<'EOF'
Herdr workspaces  (terminal-layouts)
  Start Herdr first:  herdr  (h)   — nothing to install, layouts are created live.
  Extra args go to `tl launch`:  --run-commands  --label <text>

  hag [dir]          ai-agents workbench in dir (default: here), labelled <dir name>
  hproject [label]   project workspace in current directory
  hai                claude-projects workspace
  hdk                docker workspace
  hpt                pentest workspace
  hma                malware-analysis workspace
  hos                osint workspace
  hctf               ctf workspace

Launch in current directory
  hai . | hdk . | hpt . | hma . | hos . | hctf .

Create named workspaces  (<workflow dir>/<name>, label <prefix><name>)
  hai-new <name>     ~/projects/<name>
  hdk-new <name>     ~/docker/<name>, dk-<name>
  hpt-new <name>     ~/ops/pentest/<name>, pt-<name>
  hma-new <name>     ~/ops/malware/<name>, ma-<name>
  hos-new <name>     ~/ops/osint/<name>, os-<name>
  hctf-new <name>    ~/ops/ctf/<name>, ctf-<name>

Workspaces
  hls                list workspaces (* = focused)
  hk <id>...         close workspaces

Agents are never started for you: type opencode / pi / claude / codex in a pane.
Tab completion works for tl, hk and these helpers.
EOF
}

alias hhelp='hh'

# tl + helper tab completion (zsh or bash).
if [ -n "${ZSH_VERSION:-}" ]; then
  eval '. "${${(%):-%x}:A:h}/tl-completion.zsh"'
elif [ -n "${BASH_VERSION:-}" ]; then
  # shellcheck source=tl-completion.bash
  . "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/tl-completion.bash"
fi

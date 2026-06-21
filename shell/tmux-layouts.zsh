# tmux-layouts.zsh — part of terminal-layouts
# tmux layout helpers. Source from ~/.zshrc after running `tl install`:
#   source ~/terminal-layouts/shell/tmux-layouts.zsh
#
# Layouts are pre-installed to ~/.config/tmuxp/ by `tl install`.
# By default aliases load those installed files directly (fast, no regen).
#
# OPT-IN REGEN: set TL_ALWAYS_REGEN=1 to regenerate each layout from the
# `tl` CLI before loading it. Requires `tl` on PATH.
#   export TL_ALWAYS_REGEN=1
#
# The `tl` CLI generates layouts:   tl gen tmux <workflow>
# Install all layouts once:         tl install

alias t='tmux'

# Clear old launcher aliases when re-sourcing after an update.
unalias tai tproject tdk tpt tma tos tctf 2>/dev/null || true

# Resolve this file's directory in both zsh and bash. The zsh-only param
# expansion is eval-guarded so bash's parser never chokes on it; the zsh
# branch keeps the original :A:h (canonical, symlink-resolved) behavior.
if [ -n "${ZSH_VERSION:-}" ]; then
  eval '_TMUX_LAYOUTS_DIR="${${(%):-%N}:A:h}"'
else
  _TMUX_LAYOUTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# ── User-configurable paths/prefixes ────────────────────────────────
# Optional config file (sourced by this file so overrides survive re-sourcing).
# Intended to set TMUX_LAYOUTS_* variables only (it is sourced, like a shell rc).
_tmux_layouts_cfg="${TMUX_LAYOUTS_CONFIG:-$HOME/.config/tmux-layouts/config}"
[ -f "$_tmux_layouts_cfg" ] && . "$_tmux_layouts_cfg"
unset _tmux_layouts_cfg

# Layered defaults: set a root and subdirs follow; override any one alone.
: "${TMUX_LAYOUTS_PROJECTS:=$HOME/projects}"
: "${TMUX_LAYOUTS_DOCKER:=$HOME/docker}"
: "${TMUX_LAYOUTS_OPS:=$HOME/ops}"
: "${TMUX_LAYOUTS_PENTEST:=$TMUX_LAYOUTS_OPS/pentest}"
: "${TMUX_LAYOUTS_MALWARE:=$TMUX_LAYOUTS_OPS/malware}"
: "${TMUX_LAYOUTS_OSINT:=$TMUX_LAYOUTS_OPS/osint}"
: "${TMUX_LAYOUTS_CTF:=$TMUX_LAYOUTS_OPS/ctf}"
: "${TMUX_LAYOUTS_PREFIX_DK:=dk-}"
: "${TMUX_LAYOUTS_PREFIX_PT:=pt-}"
: "${TMUX_LAYOUTS_PREFIX_MA:=ma-}"
: "${TMUX_LAYOUTS_PREFIX_OS:=os-}"
: "${TMUX_LAYOUTS_PREFIX_CTF:=ctf-}"

# ── XDG-aware tmuxp config directory ────────────────────────────────
_tmux_layouts_tmuxp_dir() {
  printf '%s\n' "${XDG_CONFIG_HOME:-$HOME/.config}/tmuxp"
}

# ── Opt-in regen helper ──────────────────────────────────────────────
# If TL_ALWAYS_REGEN is set and non-empty, regenerate the installed layout
# file for <workflow> via `tl gen tmux <workflow>` before loading.
# Falls back to the existing installed file if `tl` is not on PATH.
_tl_maybe_regen() {
  local workflow="$1"
  if [[ -n "${TL_ALWAYS_REGEN:-}" ]]; then
    if command -v tl >/dev/null 2>&1; then
      local dest
      dest="$(_tmux_layouts_tmuxp_dir)/${workflow}.yaml"
      mkdir -p "$(_tmux_layouts_tmuxp_dir)"
      tl gen tmux "$workflow" > "$dest" || {
        printf '%s\n' "terminal-layouts: warning: tl gen tmux $workflow failed; using existing file" >&2
      }
    else
      printf '%s\n' "terminal-layouts: warning: TL_ALWAYS_REGEN is set but \`tl\` is not on PATH — using installed layout" >&2
    fi
  fi
}

_tmux_layout_usage() {
  cat <<'EOF'
Usage:
  tai                   launch claude-projects workspace
  tai .                 launch claude-projects workspace in the current directory
  tproject              launch project layout in the current directory
  tproject <name>       launch project layout in the current directory with session <name>
  tdk|tpt|tma|tos|tctf  launch fixed workflow layouts
  tdk .|tpt .|tma .|tos .|tctf .
                        launch the layout in the current directory
EOF
}

_tmux_layout_fixed() {
  local usage="$1" layout="$2"
  shift 2
  if (( $# == 1 )) && [[ "$1" == "." ]]; then
    local name="${PWD##*/}"
    [[ -z "$name" || "$name" == "/" ]] && name="$layout"
    _tmux_layout_load_with_cwd "$layout" "$name" "$PWD"
    return $?
  elif (( $# != 0 )); then
    echo "Usage: $usage"
    return 2
  fi
  _tmux_layout_load "$layout"
}

_tmux_layout_file() {
  local layout="$1" candidate
  for candidate in "$(_tmux_layouts_tmuxp_dir)/$layout.yaml" "$HOME/.config/tmuxp/$layout.yaml"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "Layout not found: $layout (run \`tl install\` to install layouts)" >&2
  return 1
}

_tmuxp_load() {
  if ! command -v tmux >/dev/null 2>&1; then
    printf '%s\n' "terminal-layouts: tmux not found — install tmux >= 3.4" >&2
    return 127
  fi
  if ! command -v tmuxp >/dev/null 2>&1; then
    printf '%s\n' "terminal-layouts: tmuxp not found — install it: pipx install tmuxp" >&2
    return 127
  fi
  tmuxp --color never load --no-progress -y "$@"
}

_tmux_layout_yaml_dq() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s\n' "\"$value\""
}

_tmux_layout_temp_with_cwd() {
  local template="$1" cwd="$2" tmp line wrote=0
  tmp="$(mktemp "${TMPDIR:-/tmp}/tmuxp-layout.XXXXXX.yaml")" || return 1

  {
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" == start_directory:* ]]; then
        printf '%s\n' "start_directory: $(_tmux_layout_yaml_dq "$cwd")"
        wrote=1
      else
        printf '%s\n' "$line"
      fi
    done < "$template"

    if (( ! wrote )); then
      printf '%s\n' "start_directory: $(_tmux_layout_yaml_dq "$cwd")"
    fi
  } >| "$tmp"

  printf '%s\n' "$tmp"
}

_tmux_layout_load_with_cwd() {
  local layout="$1" session="$2" cwd="$3" template tmp rc
  _tl_maybe_regen "$layout"
  template="$(_tmux_layout_file "$layout")" || return 1
  tmp="$(_tmux_layout_temp_with_cwd "$template" "$cwd")" || return 1
  _tmuxp_load -s "$session" "$tmp"
  rc=$?
  rm -f "$tmp"
  return $rc
}

_tmux_layout_load() {
  local layout="$1" target
  _tl_maybe_regen "$layout"
  if target="$(_tmux_layout_file "$layout" 2>/dev/null)"; then
    _tmuxp_load "$target"
  else
    _tmuxp_load "$layout"
  fi
}

_tmux_layout_project_here() {
  local name="${1:-${PWD##*/}}"
  if [[ -z "$name" || "$name" == "/" ]]; then
    name="project"
  fi
  _tmux_layout_load_with_cwd project "$name" "$PWD"
}

# Layout launchers (work both inside and outside tmux — tmuxp creates and switches client).
tai() {
  case "$1" in
    "")
      _tmux_layout_load claude-projects
      ;;
    .)
      local name="${PWD##*/}"
      [[ -z "$name" || "$name" == "/" ]] && name="claude"
      _tmux_layout_load_with_cwd claude-projects "$name" "$PWD"
      ;;
    -h|--help|help)
      _tmux_layout_usage
      ;;
    *)
      echo "Unknown option: $1"
      _tmux_layout_usage
      return 2
      ;;
  esac
}

tproject() {
  if (( $# > 1 )); then
    echo "Usage: tproject [session-name]"
    return 2
  fi
  _tmux_layout_project_here "$1"
}

tdk()  { _tmux_layout_fixed "tdk [.]"  docker "$@"; }
tpt()  { _tmux_layout_fixed "tpt [.]"  pentest "$@"; }
tma()  { _tmux_layout_fixed "tma [.]"  malware-analysis "$@"; }
tos()  { _tmux_layout_fixed "tos [.]"  osint "$@"; }
tctf() { _tmux_layout_fixed "tctf [.]" ctf "$@"; }

# Session helpers.
alias tls='tmux list-sessions'
alias ta='tmux attach -t'
alias tks='tmux kill-session -t'
alias tka='tmux kill-server'

_tmux_layout_new() {
  local usage="$1" layout="$2" prefix="$3" base="$4" name="$5"
  if [[ -z "$name" ]]; then
    echo "Usage: $usage"
    return 1
  fi
  mkdir -p "$base/$name"
  _tmux_layout_load_with_cwd "$layout" "${prefix}${name}" "$base/$name"
}

tai-new()  { _tmux_layout_new "tai-new <project-name>"  project          ""                          "$TMUX_LAYOUTS_PROJECTS" "$1"; }
tdk-new()  { _tmux_layout_new "tdk-new <stack-name>"    docker           "$TMUX_LAYOUTS_PREFIX_DK"    "$TMUX_LAYOUTS_DOCKER"   "$1"; }
tpt-new()  { _tmux_layout_new "tpt-new <engagement>"    pentest          "$TMUX_LAYOUTS_PREFIX_PT"    "$TMUX_LAYOUTS_PENTEST"  "$1"; }
tma-new()  { _tmux_layout_new "tma-new <sample-name>"   malware-analysis "$TMUX_LAYOUTS_PREFIX_MA"    "$TMUX_LAYOUTS_MALWARE"  "$1"; }
tos-new()  { _tmux_layout_new "tos-new <target-name>"   osint            "$TMUX_LAYOUTS_PREFIX_OS"    "$TMUX_LAYOUTS_OSINT"    "$1"; }
tctf-new() { _tmux_layout_new "tctf-new <ctf-name>"     ctf              "$TMUX_LAYOUTS_PREFIX_CTF"   "$TMUX_LAYOUTS_CTF"      "$1"; }

th() {
  cat <<'EOF'
tmux layouts  (terminal-layouts)
  Layouts are pre-installed by `tl install`. Set TL_ALWAYS_REGEN=1 to
  regenerate from the `tl` CLI before each load (requires `tl` on PATH).

  tai             claude-projects workspace
  tai .           claude-projects workspace in $PWD
  tproject        project workspace in current directory
  tdk             docker workspace
  tpt             pentest workspace
  tma             malware-analysis workspace
  tos             osint workspace
  tctf            ctf workspace

Launch in current directory (any layout)
  tai .           claude-projects workspace in $PWD
  tdk .           docker workspace in $PWD
  tpt .           pentest workspace in $PWD
  tma .           malware-analysis workspace in $PWD
  tos .           osint workspace in $PWD
  tctf .          ctf workspace in $PWD

Create named workspaces
  (paths shown are defaults; set TMUX_LAYOUTS_* to override)
  tai-new <name>     ~/projects/<name>, session <name>
  tdk-new <name>     ~/docker/<name>, session dk-<name>
  tpt-new <name>     ~/ops/pentest/<name>, session pt-<name>
  tma-new <name>     ~/ops/malware/<name>, session ma-<name>
  tos-new <name>     ~/ops/osint/<name>, session os-<name>
  tctf-new <name>    ~/ops/ctf/<name>, session ctf-<name>

Sessions
  tls             list sessions
  ta <name>       attach to session
  tks <name>      kill session
  tka             kill all sessions (kill-server)

Install / regen
  tl install      write all layouts to ~/.config/tmuxp/ (run once after install)
  tl gen tmux <workflow>   print a single layout YAML to stdout
  TL_ALWAYS_REGEN=1        regen layout before each load (requires tl on PATH)
EOF
}

alias thelp='th'

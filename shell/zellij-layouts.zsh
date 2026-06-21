# Zellij layout helpers for terminal-layouts.
# Source from ~/.zshrc after running: tl install
#
# Layouts are pre-installed to ~/.config/zellij/layouts/*.kdl by `tl install`.
# By default, aliases launch using those installed files directly (fast, no regen).
#
# TL_ALWAYS_REGEN: if this variable is set and non-empty, each launch will
# regenerate the layout first via `tl gen zellij <workflow>` before opening.
# This ensures you always run the latest generated KDL at the cost of a small
# delay. If `tl` is not on PATH when TL_ALWAYS_REGEN is set, a warning is
# printed and the pre-installed layout is used as a fallback.
#
# Example:
#   export TL_ALWAYS_REGEN=1   # regenerate on every launch
#   unset TL_ALWAYS_REGEN      # use installed layouts (default)

# ---------------------------------------------------------------------------
# Internal helper: optionally regenerate a workflow's KDL before launching.
# Usage: _tl_maybe_regen <workflow>
# ---------------------------------------------------------------------------
_tl_maybe_regen() {
  local workflow="$1"
  [[ -z "$TL_ALWAYS_REGEN" ]] && return 0

  if ! command -v tl &>/dev/null; then
    echo "tl: warning: TL_ALWAYS_REGEN is set but \`tl\` is not on PATH — using installed layout for '${workflow}'" >&2
    return 0
  fi

  local cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/zellij/layouts"
  mkdir -p "$cfg_dir"
  tl gen zellij "$workflow" > "$cfg_dir/${workflow}.kdl"
}

# ---------------------------------------------------------------------------
# Core alias.
# ---------------------------------------------------------------------------
alias z='zellij'

# ---------------------------------------------------------------------------
# Layout launchers.
# ---------------------------------------------------------------------------

zp() {
  _tl_maybe_regen claude-projects
  zellij -n claude-projects -s claude
}

zo() {
  _tl_maybe_regen project
  zellij -n project options --default-cwd "$@"
}

zdk() {
  _tl_maybe_regen docker
  zellij -n docker -s docker options --default-cwd ~/docker
}

zpt() {
  _tl_maybe_regen pentest
  zellij -n pentest -s pentest options --default-cwd ~/ops/pentest
}

zma() {
  _tl_maybe_regen malware-analysis
  zellij -n malware-analysis -s malware options --default-cwd ~/ops/malware
}

zos() {
  _tl_maybe_regen osint
  zellij -n osint -s osint options --default-cwd ~/ops/osint
}

zctf() {
  _tl_maybe_regen ctf
  zellij -n ctf -s ctf options --default-cwd ~/ops/ctf
}

# ---------------------------------------------------------------------------
# Session management.
# ---------------------------------------------------------------------------
alias zls='zellij list-sessions'
alias za='zellij attach'
alias zks='zellij kill-session'
alias zka='zellij kill-all-sessions'
alias zds='zellij delete-session'
alias zda='zellij delete-all-sessions'

# ---------------------------------------------------------------------------
# Named-workspace creators.
# ---------------------------------------------------------------------------
_zellij_layout_new() {
  local usage="$1"
  local layout="$2"
  local session_prefix="$3"
  local base_dir="$4"
  local name="$5"

  [[ -z "$name" ]] && { echo "Usage: $usage"; return 1; }

  _tl_maybe_regen "$layout"
  mkdir -p "$base_dir/$name"
  zellij -n "$layout" -s "${session_prefix}${name}" options --default-cwd "$base_dir/$name"
}

zp-new() {
  _zellij_layout_new "zp-new <project-name>" project "" "$HOME/projects" "$1"
}

zdk-new() {
  _zellij_layout_new "zdk-new <stack-name>" docker "dk-" "$HOME/docker" "$1"
}

zpt-new() {
  _zellij_layout_new "zpt-new <engagement-name>" pentest "pt-" "$HOME/ops/pentest" "$1"
}

zma-new() {
  _zellij_layout_new "zma-new <sample-name>" malware-analysis "ma-" "$HOME/ops/malware" "$1"
}

zos-new() {
  _zellij_layout_new "zos-new <target-name>" osint "os-" "$HOME/ops/osint" "$1"
}

zctf-new() {
  _zellij_layout_new "zctf-new <ctf-name>" ctf "ctf-" "$HOME/ops/ctf" "$1"
}

# ---------------------------------------------------------------------------
# Help.
# ---------------------------------------------------------------------------
zh() {
  cat <<'EOF'
Zellij layouts  (terminal-layouts)
  Run `tl install` once to write all layouts to ~/.config/zellij/layouts/.
  Set TL_ALWAYS_REGEN=1 to regenerate each layout via `tl gen zellij` on every launch.

Launchers
  zp              claude-projects workspace
  zo <dir>        single-project layout in any directory
  zdk             docker workspace
  zpt             pentest workspace
  zma             malware-analysis workspace
  zos             osint workspace
  zctf            ctf workspace

Create named workspaces
  zp-new <name>      ~/projects/<name>, session <name>
  zdk-new <name>     ~/docker/<name>, session dk-<name>
  zpt-new <name>     ~/ops/pentest/<name>, session pt-<name>
  zma-new <name>     ~/ops/malware/<name>, session ma-<name>
  zos-new <name>     ~/ops/osint/<name>, session os-<name>
  zctf-new <name>    ~/ops/ctf/<name>, session ctf-<name>

Sessions
  zls             list sessions
  za <name>       attach to session
  zks <name>      kill session (running)
  zka             kill all sessions
  zds <name>      delete session (exited)
  zda             delete all sessions (exited)
EOF
}

alias zhelp='zh'

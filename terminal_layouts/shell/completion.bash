# bash tab completion for `tl` and the generated <backend>-<workflow> commands.
# Inlined by `tl init bash`.
# Works with bash 3.2+ (macOS): no mapfile; compopt is optional (bash 4+).
# shellcheck disable=SC2207  # COMPREPLY=($(compgen ...)): words never contain spaces

# Directory candidates, one per line, inserted quoted (names may have spaces).
_tlc_dirs() {
  local IFS=$'\n'
  compopt -o filenames 2>/dev/null
  COMPREPLY=($(compgen -d -- "$1"))
}

_tlc_opts() {
  case "$1" in
    herdr) echo "--label --run-commands" ;;
    tmux) echo "--label --detach -d" ;;
    *) echo "--label" ;;  # zellij, or target not typed yet
  esac
}

_tl_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmd="${COMP_WORDS[1]:-}" words="" i n=0 target=""
  COMPREPLY=()
  case "$prev" in
    --cwd|--tmuxp-dir|--zellij-dir) _tlc_dirs "$cur"; return ;;
    --new|--label) return ;;
    --backends) COMPREPLY=($(compgen -W "herdr tmux zellij herdr,tmux,zellij" -- "$cur")); return ;;
  esac
  if (( COMP_CWORD == 1 )); then
    words="gen launch init list validate install --help --version"
  else
    # Count positional words after the subcommand, skipping options and their values.
    for (( i = 2; i < COMP_CWORD; i++ )); do
      case "${COMP_WORDS[i]}" in
        --cwd|--new|--label|--tmuxp-dir|--zellij-dir|--backends) (( i++ )) ;;
        -*) ;;
        *) (( n++ )); (( n == 1 )) && target="${COMP_WORDS[i]}" ;;
      esac
    done
    case "$cmd" in
      gen)
        case $n in 0) words="tmux zellij herdr" ;; 1) words="$(command tl list 2>/dev/null)" ;; esac ;;
      launch)
        if [[ "$cur" == -* ]]; then
          words="--cwd --new --help $(_tlc_opts "$target")"
        else
          case $n in
            0) words="herdr tmux zellij" ;;
            1) words="$(command tl list 2>/dev/null)" ;;
            2) _tlc_dirs "$cur"; return ;;
          esac
        fi ;;
      init)
        if [[ "$cur" == -* ]]; then words="--backends --force --help"
        elif (( n == 0 )); then words="zsh bash"; fi ;;
      install) words="--tmux-only --zellij-only --tmuxp-dir --zellij-dir --help" ;;
    esac
  fi
  COMPREPLY=($(compgen -W "$words" -- "$cur"))
}

# <backend>-<workflow>: ONE of an optional directory ("." = here) or --new NAME,
# plus options (tl launch rejects a second location).
_tlc_launch() {
  local cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}" i placed=""
  COMPREPLY=()
  case "$prev" in --new|--label) return ;; esac
  for (( i = 1; i < COMP_CWORD; i++ )); do
    case "${COMP_WORDS[i]}" in
      --new) placed=1; (( i++ )) ;;
      --label) (( i++ )) ;;
      -*) ;;
      *) placed=1 ;;
    esac
  done
  if [[ "$cur" != -* ]]; then
    [[ -z "$placed" ]] && _tlc_dirs "$cur"
    return
  fi
  local new="--new"
  [[ -n "$placed" ]] && new=""
  COMPREPLY=($(compgen -W "$new $(_tlc_opts "$1")" -- "$cur"))
}
_tlc_launch_herdr()  { _tlc_launch herdr; }
_tlc_launch_tmux()   { _tlc_launch tmux; }
_tlc_launch_zellij() { _tlc_launch zellij; }

_tlc_herdr_workspaces() {
  local ids
  ids="$(herdr workspace list 2>/dev/null | python3 -c '
import json, sys
print(" ".join(w["workspace_id"] for w in json.load(sys.stdin)["result"]["workspaces"]))
' 2>/dev/null)"
  COMPREPLY=($(compgen -W "$ids" -- "${COMP_WORDS[COMP_CWORD]}"))
}
_tlc_tmux_sessions() {
  COMPREPLY=($(compgen -W "$(tmux list-sessions -F '#S' 2>/dev/null)" -- "${COMP_WORDS[COMP_CWORD]}"))
}
_tlc_zellij_sessions() {
  COMPREPLY=($(compgen -W "$(zellij list-sessions --short --no-formatting 2>/dev/null)" -- "${COMP_WORDS[COMP_CWORD]}"))
}

# _TLC_REGS_<backend> hold "function:name" pairs from `tl init`; only names
# this integration owns (_TL_OWNED) get completion, never a command it skipped.
_tlc_register_all() {
  complete -F _tl_complete tl terminal-layouts
  local entry
  for entry in ${_TLC_REGS_tmux:-} ${_TLC_REGS_zellij:-} ${_TLC_REGS_herdr:-}; do
    case " $_TL_OWNED " in *" ${entry#*:} "*) complete -F "${entry%%:*}" "${entry#*:}" ;; esac
  done
}
_tlc_register_all

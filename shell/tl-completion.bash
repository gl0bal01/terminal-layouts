# tl-completion.bash — bash tab completion for `tl` (terminal-layouts) and the
# Herdr helpers. Sourced by shell/*-layouts.zsh when they run under bash.
# Works with bash 3.2+ (macOS): no mapfile; compopt is optional (bash 4+).
# shellcheck disable=SC2207  # COMPREPLY=($(compgen ...)): words never contain spaces

# Directory candidates, one per line, inserted quoted (names may have spaces).
_tlc_dirs() {
  local IFS=$'\n'
  compopt -o filenames 2>/dev/null
  COMPREPLY=($(compgen -d -- "$1"))
}

_tl_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmd="${COMP_WORDS[1]:-}" words="" i n=0
  COMPREPLY=()
  case "$prev" in
    --cwd|--tmuxp-dir|--zellij-dir) _tlc_dirs "$cur"; return ;;
    --new|--label) return ;;
  esac
  if (( COMP_CWORD == 1 )); then
    words="gen launch list validate install --help --version"
  else
    # Count positional words after the subcommand, skipping options and their values.
    for (( i = 2; i < COMP_CWORD; i++ )); do
      case "${COMP_WORDS[i]}" in
        --cwd|--new|--label|--tmuxp-dir|--zellij-dir) (( i++ )) ;;
        -*) ;;
        *) (( n++ )) ;;
      esac
    done
    case "$cmd" in
      gen)
        case $n in 0) words="tmux zellij herdr" ;; 1) words="$(tl list 2>/dev/null)" ;; esac ;;
      launch)
        if [[ "$cur" == -* ]]; then
          words="--run-commands --cwd --new --label --help"
        else
          case $n in 0) words="herdr" ;; 1) words="$(tl list 2>/dev/null)" ;; esac
        fi ;;
      install) words="--tmux-only --zellij-only --tmuxp-dir --zellij-dir --help" ;;
    esac
  fi
  COMPREPLY=($(compgen -W "$words" -- "$cur"))
}

_tlc_hks() {
  local ids
  ids="$(herdr workspace list 2>/dev/null | python3 -c '
import json, sys
print(" ".join(w["workspace_id"] for w in json.load(sys.stdin)["result"]["workspaces"]))
' 2>/dev/null)"
  COMPREPLY=($(compgen -W "$ids" -- "${COMP_WORDS[COMP_CWORD]}"))
}

# hai/hdk/...: optional "." first, then tl launch options.
_tlc_here() {
  local words="--run-commands --label"
  (( COMP_CWORD == 1 )) && words=". $words"
  COMPREPLY=($(compgen -W "$words" -- "${COMP_WORDS[COMP_CWORD]}"))
}

# hag: optional directory first, then options.
_tlc_hag() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  if (( COMP_CWORD == 1 )) && [[ "$cur" != -* ]]; then _tlc_dirs "$cur"; return; fi
  COMPREPLY=($(compgen -W "--run-commands --label" -- "$cur"))
}

# *-new and hproject: a free-form name/label first, then options.
_tlc_named() {
  COMPREPLY=()
  (( COMP_CWORD == 1 )) && return
  COMPREPLY=($(compgen -W "--run-commands --label" -- "${COMP_WORDS[COMP_CWORD]}"))
}

complete -F _tl_complete tl terminal-layouts
complete -F _tlc_hks hks
complete -F _tlc_here hai hdk hpt hma hos hctf
complete -F _tlc_hag hag
complete -F _tlc_named hproject hai-new hdk-new hpt-new hma-new hos-new hctf-new

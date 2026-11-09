# tl-completion.bash — bash tab completion for `tl` (terminal-layouts) and the
# Herdr helpers. Sourced by shell/*-layouts.zsh when they run under bash.
# Works with bash 3.2+ (macOS). Directory names are split on newlines only.
# shellcheck disable=SC2207  # COMPREPLY=($(compgen ...)) with IFS=newline

_tl_complete() {
  local IFS=$'\n'
  local cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmd="${COMP_WORDS[1]:-}" words="" i n=0
  COMPREPLY=()
  case "$prev" in
    --cwd|--tmuxp-dir|--zellij-dir) COMPREPLY=($(compgen -d -- "$cur")); return ;;
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
  words="${words// /$'\n'}"
  COMPREPLY=($(compgen -W "$words" -- "$cur"))
}

_hk_complete() {
  local IFS=$'\n'
  local ids
  ids="$(herdr workspace list 2>/dev/null | python3 -c '
import json, sys
print("\n".join(w["workspace_id"] for w in json.load(sys.stdin)["result"]["workspaces"]))
' 2>/dev/null)"
  COMPREPLY=($(compgen -W "$ids" -- "${COMP_WORDS[COMP_CWORD]}"))
}

_herdr_launch_complete() {
  local IFS=$'\n'
  local cur="${COMP_WORDS[COMP_CWORD]}" words="--run-commands --label"
  (( COMP_CWORD == 1 )) && words=". $words"
  words="${words// /$'\n'}"
  COMPREPLY=($(compgen -W "$words" -- "$cur"))
}

complete -F _tl_complete tl terminal-layouts
complete -F _hk_complete hk
complete -F _herdr_launch_complete hai hdk hpt hma hos hctf
complete -o dirnames hag

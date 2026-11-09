# zsh tab completion for `tl` and the generated shortcuts. Inlined by `tl init zsh`.
# Registration waits for compinit if it has not run yet (any ~/.zshrc order works).

_tl() {
  local curcontext="$curcontext" state line
  _arguments -C \
    '(- *)--version[show version and exit]' \
    '(- *)'{-h,--help}'[show help and exit]' \
    '1:command:((gen\:"print a layout or Herdr plan" launch\:"open a workflow (Herdr, tmux, Zellij)" init\:"print shell shortcuts + completion" list\:"list workflows" validate\:"validate manifests" install\:"install tmuxp + Zellij layouts"))' \
    '*::arg:->args' && return
  local -a workflows
  case $line[1] in
    gen)
      workflows=(${(f)"$(tl list 2>/dev/null)"})
      _arguments '1:target:(tmux zellij herdr)' "2:workflow:(${workflows})" ;;
    launch)
      workflows=(${(f)"$(tl list 2>/dev/null)"})
      _arguments '1:target:(herdr tmux zellij)' "2:workflow:(${workflows})" \
        '3::directory (. = here):_directories' \
        '(--new 3)--cwd[run in this directory]:directory:_directories' \
        '(--cwd 3)--new[create <workflow dir>/NAME and launch there]:name: ' \
        '--label[workspace / session name]:name: ' \
        '--run-commands[Herdr: also run the manifest pane commands]' \
        '(-d --detach)'{-d,--detach}'[tmux: create the session without attaching]' ;;
    init)
      _arguments '1:shell:(zsh bash)' \
        '--backends[only these backends]:backends:_values -s , backend herdr tmux zellij' \
        '--force[replace existing commands/aliases with the same names]' ;;
    install)
      _arguments \
        '(--zellij-only)--tmux-only[tmuxp layouts only]' \
        '(--tmux-only)--zellij-only[Zellij layouts only]' \
        '--tmuxp-dir[tmuxp layout directory]:directory:_directories' \
        '--zellij-dir[Zellij layout directory]:directory:_directories' ;;
  esac
}

_tlc_opts_herdr=('--label[workspace name]:name: ' '--run-commands[also run the manifest pane commands]')
_tlc_opts_tmux=('--label[session name]:name: ' '(-d --detach)'{-d,--detach}'[create without attaching]')
_tlc_opts_zellij=('--label[session name]:name: ')
_tlc_launch_herdr()  { _arguments '1::directory (. = here):_directories' $_tlc_opts_herdr; }
_tlc_launch_tmux()   { _arguments '1::directory (. = here):_directories' $_tlc_opts_tmux; }
_tlc_launch_zellij() { _arguments '1::directory (. = here):_directories' $_tlc_opts_zellij; }
_tlc_new_herdr()  { _arguments '1:name: ' $_tlc_opts_herdr; }
_tlc_new_tmux()   { _arguments '1:name: ' $_tlc_opts_tmux; }
_tlc_new_zellij() { _arguments '1:name: ' $_tlc_opts_zellij; }

_tlc_hks() {
  local -a ids
  ids=(${(f)"$(herdr workspace list 2>/dev/null | python3 -c '
import json, sys
for w in json.load(sys.stdin)["result"]["workspaces"]:
    print(w["workspace_id"] + ":" + w["label"].replace(":", "\\:"))
' 2>/dev/null)"})
  _describe -t workspaces 'Herdr workspace' ids
}
_tlc_tmux_sessions() {
  local -a s
  s=(${(f)"$(tmux list-sessions -F '#S' 2>/dev/null)"})
  _describe -t sessions 'tmux session' s
}
_tlc_zellij_sessions() {
  local -a s
  s=(${(f)"$(zellij list-sessions --short --no-formatting 2>/dev/null)"})
  _describe -t sessions 'Zellij session' s
}

# _TLC_REGS holds "function:name" pairs from every `tl init` eval; only names
# this integration owns (_TL_OWNED) get completion, never a command it skipped.
_tlc_register_all() {
  (( $+functions[compdef] )) || return 1
  compdef _tl tl terminal-layouts
  local entry
  for entry in ${=_TLC_REGS}; do
    case " $_TL_OWNED " in *" ${entry#*:} "*) compdef ${entry%%:*} ${entry#*:} ;; esac
  done
}
_tlc_register_deferred() {
  _tlc_register_all && add-zsh-hook -d precmd _tlc_register_deferred
}
if ! _tlc_register_all; then
  autoload -Uz add-zsh-hook
  add-zsh-hook precmd _tlc_register_deferred
fi

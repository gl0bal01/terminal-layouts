# tl-completion.zsh — zsh tab completion for `tl` (terminal-layouts) and the
# Herdr helpers. Sourced by shell/*-layouts.zsh. If compinit has not run yet
# (e.g. sourced above oh-my-zsh), registration waits for the first prompt.

_tl() {
  local curcontext="$curcontext" state line
  _arguments -C \
    '(- *)--version[show version and exit]' \
    '(- *)'{-h,--help}'[show help and exit]' \
    '1:command:((gen\:"print a layout or Herdr plan" launch\:"create a Herdr workspace" list\:"list workflows" validate\:"validate manifests" install\:"install tmuxp + Zellij layouts"))' \
    '*::arg:->args' && return
  local -a workflows
  case $line[1] in
    gen)
      workflows=(${(f)"$(tl list 2>/dev/null)"})
      _arguments '1:target:(tmux zellij herdr)' "2:workflow:(${workflows})" ;;
    launch)
      workflows=(${(f)"$(tl list 2>/dev/null)"})
      _arguments '1:target:(herdr)' "2:workflow:(${workflows})" \
        '--run-commands[also run the manifest pane commands]' \
        '(--new)--cwd[run the workflow in this directory]:directory:_directories' \
        '(--cwd)--new[create <workflow dir>/NAME and launch there]:name: ' \
        '--label[Herdr workspace label]:label: ' ;;
    install)
      _arguments \
        '(--zellij-only)--tmux-only[tmuxp layouts only]' \
        '(--tmux-only)--zellij-only[Zellij layouts only]' \
        '--tmuxp-dir[tmuxp layout directory]:directory:_directories' \
        '--zellij-dir[Zellij layout directory]:directory:_directories' ;;
  esac
}

# Herdr workspace ids, described by their labels (for hks).
_tlc_hks() {
  local -a ids
  ids=(${(f)"$(herdr workspace list 2>/dev/null | python3 -c '
import json, sys
for w in json.load(sys.stdin)["result"]["workspaces"]:
    print(w["workspace_id"] + ":" + w["label"].replace(":", "\\:"))
' 2>/dev/null)"})
  _describe -t workspaces 'Herdr workspace' ids
}

_tlc_launch_opts=(
  '--run-commands[also run the manifest pane commands]'
  '--label[Herdr workspace label]:label: '
)
_tlc_here()     { _arguments '1::where:((.\:"current directory"))' $_tlc_launch_opts; }
_tlc_new()      { _arguments '1:name: ' $_tlc_launch_opts; }
_tlc_hag()      { _arguments '1::directory:_directories' $_tlc_launch_opts; }
_tlc_hproject() { _arguments '1::workspace label: ' $_tlc_launch_opts; }

_tlc_register() {
  (( $+functions[compdef] )) || return 1
  compdef _tl tl terminal-layouts
  compdef _tlc_hks hks
  compdef _tlc_here hai hdk hpt hma hos hctf
  compdef _tlc_new hai-new hdk-new hpt-new hma-new hos-new hctf-new
  compdef _tlc_hag hag
  compdef _tlc_hproject hproject
}

_tlc_register_deferred() {
  _tlc_register && add-zsh-hook -d precmd _tlc_register_deferred
}

if ! _tlc_register; then
  autoload -Uz add-zsh-hook
  add-zsh-hook precmd _tlc_register_deferred
fi

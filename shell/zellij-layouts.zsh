# zellij-layouts.zsh — kept so existing `source .../shell/zellij-layouts.zsh` lines keep working.
# Shortcuts and tab completion now come from `tl init`; one line in ~/.zshrc (or
# ~/.bashrc) covers every backend and is faster than sourcing several files:
#   eval "$(tl init zsh)"                  # t* (tmux), z* (Zellij), h* (Herdr)
#   eval "$(tl init zsh --backends zellij)"    # only this backend
if _tl_init_out="$(tl init "${ZSH_VERSION:+zsh}${BASH_VERSION:+bash}" --backends zellij 2>/dev/null)"; then
  eval "$_tl_init_out"
else
  printf '%s\n' "terminal-layouts: these shortcuts need a tl that has \`tl init\` (pipx install --force terminal-layouts)" >&2
fi
unset _tl_init_out

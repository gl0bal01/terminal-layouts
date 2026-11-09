# tmux-layouts.zsh — kept so existing `source .../shell/tmux-layouts.zsh` lines keep working.
# Shortcuts and tab completion now come from `tl init`; one line in ~/.zshrc (or
# ~/.bashrc) covers every backend and is faster than sourcing several files:
#   eval "$(command tl init zsh)"                  # t* (tmux), z* (Zellij), h* (Herdr)
#   eval "$(command tl init zsh --backends tmux)"    # only this backend
if ! command -v tl >/dev/null 2>&1; then
  printf '%s\n' "terminal-layouts: tl not found — pipx install terminal-layouts" >&2
elif _tl_init_out="$(command tl init "${ZSH_VERSION:+zsh}${BASH_VERSION:+bash}" --backends tmux)"; then
  eval "$_tl_init_out"
else
  printf '%s\n' "terminal-layouts: \`tl init\` failed (see above); an old tl lacks it: pipx install --force terminal-layouts" >&2
fi
unset _tl_init_out

# 06-cli — the tl commands behind the shell commands: -h, help, list, gen, validate, launch, init, install
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh --install && vhs docs/demo/06-cli.tape && bash docs/demo-env.sh --stop
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh
# (tl pre-installed there by --install; tl install writes into its HOME only).
# Hidden clears run `clear`, not Ctrl+L: the pager leaves scrollback, and vhs's
# Wait+Screen reads the top of the buffer, so it would never see new output.
Output docs/demo/06-cli.gif

Set Shell "bash"
Set FontSize 14
Set Width 1280
Set Height 760
Set Padding 14
Set Framerate 24
Set TypingSpeed 45ms
Set Theme "Catppuccin Mocha"

Hide
Type "exec /tmp/tldemo/env zsh -i"
Enter
Sleep 1500ms
Type "cd ~/projects/demo && clear"
Enter
Sleep 500ms
Show

# 1. the overview: 3 examples + every command
Type@20ms "# tl -h = overview, tl --version"
Enter
Sleep 600ms
Type "tl --version"
Sleep 300ms
Enter
Sleep 800ms
Type "tl -h"
Sleep 300ms
Enter
Sleep 5s
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 2. the manual, in a pager
Type@20ms "# tl help = the full manual, generated from the manifest (Space = next page, q = quit)"
Enter
Sleep 600ms
Type "tl help"
Sleep 300ms
Enter
Sleep 3s
Space
Sleep 2500ms
Space
Sleep 2500ms
Type "q"
Sleep 300ms
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 3. one part of it; Tab lists the topics
Type@20ms "# tl help TOPIC = one part (Tab lists them)"
Enter
Sleep 600ms
Type "tl help "
Sleep 300ms
Tab
Sleep 2s
Type "workflows"
Sleep 300ms
Enter
Sleep 5s
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 4. list and gen open nothing
Type@20ms "# tl list, tl gen BACKEND WORKFLOW = print, open nothing"
Enter
Sleep 600ms
Type "tl list"
Sleep 300ms
Enter
Sleep 1500ms
Type "tl gen tmux pentest | head -14"
Sleep 300ms
Enter
Sleep 4s
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 5. validate the manifest
Type@20ms "# tl validate = schema, ids and prefixes of every workflow"
Enter
Sleep 600ms
Type "tl validate"
Sleep 300ms
Enter
Sleep 3s
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 6. launch: what every <backend>-<workflow> command runs
Type@20ms "# tmux-pentest is: tl launch tmux pentest (same DIR, --new, --label, -d)"
Enter
Sleep 600ms
Type "tl init zsh | grep -A2 'function tmux-pentest '"
Sleep 300ms
Enter
Sleep 2500ms
Type "tl launch tmux pentest --new acme -d"
Sleep 300ms
Enter
Sleep 800ms
Hide
Wait+Screen@30s /Loaded workspace: pt-acme /
Show
Sleep 1200ms
Type "tmux-ls"
Sleep 300ms
Enter
Sleep 2500ms
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 7. install: the only command that writes into ~/.config
Type@20ms "# tl install = static layouts for plain tmuxp / zellij (only it writes ~/.config)"
Enter
Sleep 600ms
Type "tl install --tmux-only"
Sleep 300ms
Enter
Sleep 2500ms
Type "tmuxp ls"
Sleep 300ms
Enter
Sleep 3s
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 8. every command: description, examples, what it touches
Type@20ms "# tl COMMAND -h = options, examples and what it touches"
Enter
Sleep 600ms
Type "tl launch -h"
Sleep 300ms
Enter
Sleep 6s

Hide
Type "tmux-kill-all"
Enter
Sleep 500ms

# 05-options — launch options on tmux: . / DIR / --new / --label / -d, then ls / attach / kill
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh --install && vhs docs/demo/05-options.tape && bash docs/demo-env.sh --stop
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh
# (tl pre-installed there by --install; pane commands use canned stand-ins).
Output docs/demo/05-options.gif

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

# 1. '.' = this directory; the session is named <prefix><dir>
Type@20ms "# . = open it here, session pt-<dir>"
Enter
Sleep 600ms
Type "tmux-pentest ."
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[pt-demo\]/
Show
Sleep 2500ms
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# 2. any directory, -d = start detached
Type@20ms "# DIR = any directory, -d = detached"
Enter
Sleep 600ms
Type "tmux-pentest ~/case -d"
Sleep 300ms
Enter
Sleep 800ms
Hide
Wait+Screen@30s /Loaded workspace: pt-case /
Show
Sleep 1500ms

# 3. --new NAME: <workflow dir>/NAME is created, session <prefix>NAME
Type@20ms "# --new NAME = new engagement dir in ~/ops/pentest"
Enter
Sleep 600ms
Type "tmux-pentest --new acme -d"
Sleep 300ms
Enter
Sleep 800ms
Hide
Wait+Screen@30s /Loaded workspace: pt-acme /
Show
Sleep 1500ms
Type "ls ~/ops/pentest"
Sleep 300ms
Enter
Sleep 1500ms

# 4. --label NAME: pick the session name
Type@20ms "# --label NAME = your own session name"
Enter
Sleep 600ms
Type "tmux-pentest --label red-team -d"
Sleep 300ms
Enter
Sleep 800ms
Hide
Wait+Screen@30s /Loaded workspace: red-team /
Show
Sleep 1500ms

# 5. sessions: list, attach, kill
Hide
Ctrl+L
Sleep 200ms
Show
Type "tmux-ls"
Sleep 300ms
Enter
Sleep 3500ms
Type "tmux-attach pt-acme"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[pt-acme\]/
Show
Sleep 2500ms
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show
Type "tmux-kill red-team && tmux-ls"
Sleep 300ms
Enter
Sleep 3500ms

# Herdr only: also start the pane commands
Type@20ms "# Herdr: herdr-pentest --run-commands also runs the pane commands"
Enter
Sleep 600ms
Sleep 2s

Hide
Type "tmux-kill-all"
Enter
Sleep 500ms

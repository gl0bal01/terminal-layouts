# 02-tmux — every workflow as a tmux session (tour windows, detach)
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh --install && vhs docs/demo/02-tmux.tape && bash docs/demo-env.sh --stop
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh
# (tl pre-installed there by --install; pane commands use canned stand-ins).
Output docs/demo/02-tmux.gif

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

# ai-agents -> session ai-demo
Type "tmux-ai-agents"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[ai-demo\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# claude-projects -> session claude-projects
Type "tmux-claude-projects"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[claude-projects\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# ctf -> session ctf
Type "tmux-ctf"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[ctf\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# docker -> session docker
Type "tmux-docker"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[docker\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# malware-analysis -> session malware-analysis
Type "tmux-malware-analysis"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[malware-analysis\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# osint -> session osint
Type "tmux-osint"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[osint\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# pentest -> session pentest
Type "tmux-pentest"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[pentest\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# project -> session demo
Type "tmux-project"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /\[demo\]/
Show
Sleep 1500ms
Ctrl+B
Type "n"
Sleep 1s
Ctrl+B
Type "d"
Sleep 800ms
Hide
Ctrl+L
Sleep 200ms
Show

# every session is still running: list, then kill them all
Type "tmux-ls"
Sleep 300ms
Enter
Sleep 3500ms
Type "tmux-kill-all"
Sleep 300ms
Enter
Sleep 1500ms

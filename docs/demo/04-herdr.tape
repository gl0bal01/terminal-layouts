# 04-herdr — every workflow as a Herdr workspace, from a shell inside the Herdr TUI
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh --install && vhs docs/demo/04-herdr.tape && bash docs/demo-env.sh --stop
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh
# (tl pre-installed there by --install; pane commands use canned stand-ins).
Output docs/demo/04-herdr.gif

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

# Herdr TUI (isolated demo server: own HERDR_SOCKET_PATH, HOME and XDG dirs)
Type "herdr"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /spaces/
Show
Sleep 1500ms

# ai-agents: typed in the focused pane; the new workspace takes focus
Type "herdr-ai-agents"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /implement/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# claude-projects: typed in the focused pane; the new workspace takes focus
Type "herdr-claude-projects"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /scout-contracts/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# ctf: typed in the focused pane; the new workspace takes focus
Type "herdr-ctf"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /forensics/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# docker: typed in the focused pane; the new workspace takes focus
Type "herdr-docker"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /debug/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# malware-analysis: typed in the focused pane; the new workspace takes focus
Type "herdr-malware-analysis"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /dynamic/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# osint: typed in the focused pane; the new workspace takes focus
Type "herdr-osint"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /timeline/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# pentest: typed in the focused pane; the new workspace takes focus
Type "herdr-pentest"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /exploit/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s
Ctrl+B
Type "3"
Sleep 1s

# project: typed in the focused pane; the new workspace takes focus
Type "herdr-project ~/projects/my-app"
Sleep 300ms
Enter
Hide
Wait+Screen@60s /scratch/
Show
Sleep 1500ms
Ctrl+B
Type "2"
Sleep 1s

# list workspaces, close the first one (the plain shell Herdr opened with)
Type "herdr-ls"
Sleep 300ms
Enter
Sleep 3500ms
Type "herdr-close w1"
Sleep 300ms
Enter
Sleep 2500ms

# detach (Ctrl+B q): the workspaces keep running in the server
Ctrl+B
Type "q"
Sleep 1s
Ctrl+L
Type "herdr-ls"
Sleep 300ms
Enter
Sleep 3500ms

# stop the demo's own Herdr server
Hide
Type "herdr server stop"
Enter
Sleep 1s

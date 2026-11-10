# 03-zellij — every workflow as a Zellij session (tour tabs with Ctrl+T <n>, quit with Ctrl+Q)
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh --install && vhs docs/demo/03-zellij.tape && bash docs/demo-env.sh --stop
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh
# (tl pre-installed there by --install; pane commands use canned stand-ins).
Output docs/demo/03-zellij.gif

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

# ai-agents -> session ai-demo; quit (Ctrl+Q)
Type "zellij-ai-agents"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(ai-demo\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# claude-projects -> session claude-projects; quit (Ctrl+Q)
Type "zellij-claude-projects"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(claude-projects\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# ctf -> session ctf; quit (Ctrl+Q)
Type "zellij-ctf"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(ctf\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# docker -> session docker; quit (Ctrl+Q)
Type "zellij-docker"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(docker\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# malware-analysis -> session malware-analysis; quit (Ctrl+Q)
Type "zellij-malware-analysis"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(malware-analysis\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# osint -> session osint; quit (Ctrl+Q)
Type "zellij-osint"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(osint\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+Q
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# pentest -> session pentest; detach (Ctrl+O d): it keeps running
Type "zellij-pentest"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(pentest\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+T
Type "3"
Sleep 1s
Ctrl+O
Type "d"
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# project -> session demo; detach (Ctrl+O d): it keeps running
Type "zellij-project"
Sleep 300ms
Enter
Hide
Wait+Screen@30s /Zellij \(demo\)/
Show
Sleep 1200ms
Ctrl+T
Type "2"
Sleep 1s
Ctrl+O
Type "d"
Sleep 300ms
# Zellij needs a moment to hand the terminal back; cut the wait
Hide
Sleep 2500ms
Ctrl+L
Sleep 300ms
Show

# the detached sessions are still running: list them, then kill them all
Type "zellij-ls"
Sleep 300ms
Enter
Sleep 3500ms
Type "zellij-kill-all -y"
Sleep 300ms
Enter
Sleep 2s

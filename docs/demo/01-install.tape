# 01-install — install tl, enable the shell commands, discover them.
# Render from the repo root (needs vhs, ttyd, ffmpeg, pipx, tmuxp, zellij, herdr):
#   bash docs/demo-env.sh && vhs docs/demo/01-install.tape
# Everything runs in the throwaway, isolated /tmp/tldemo made by docs/demo-env.sh.
Output docs/demo/01-install.gif

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

# 1. Install (the download wait is cut)
Type "pipx install terminal-layouts"
Sleep 400ms
Enter
Sleep 2s
Hide
Wait+Screen@180s /globally available/
Show
Sleep 2500ms

# 2. One line in ~/.zshrc: every command + tab completion
Type `echo 'eval "$(command tl init zsh)"' >> ~/.zshrc && exec zsh`
Sleep 400ms
Enter
Sleep 1200ms
Ctrl+L

# 3. `layouts`: every workflow, option and command on one screen
Type "layouts"
Sleep 300ms
Enter
Sleep 7s
Ctrl+L

# 4. Tab completion: <backend>- then Tab
Type "tmux-"
Sleep 300ms
Tab
Sleep 2500ms
Ctrl+U
Ctrl+L
Type "zellij-"
Sleep 300ms
Tab
Sleep 2500ms
Ctrl+U
Ctrl+L
Type "herdr-"
Sleep 300ms
Tab
Sleep 3s

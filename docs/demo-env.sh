#!/usr/bin/env bash
# demo-env.sh — fresh, isolated environment for the demo tapes under /tmp/tldemo:
# its own HOME (pipx, ~/.zshrc, ~/ops/*), tmux socket dir, Zellij and Herdr
# config/sockets, XDG dirs and a demo copy of the manifest. Nothing here ever
# talks to your own tmux, Zellij or Herdr servers.
#
#   bash docs/demo-env.sh            fresh env, tl NOT installed (docs/demo/01-install.tape)
#   bash docs/demo-env.sh --install  fresh env + tl installed with pipx + shell commands enabled (02..05)
#   bash docs/demo-env.sh --stop     stop the demo's tmux, Zellij and Herdr servers
#
# Tapes enter it with:  exec /tmp/tldemo/env zsh -i
# TL_SRC=<pip spec> picks what --install installs (default: the GitHub repo);
# ZELLIJ_BIN= / HERDR_BIN= pick specific builds for the recording.
set -euo pipefail
D=/tmp/tldemo
H="$D/home"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
# The demo shell starts from `env -i`: only these variables exist in it. No
# HERDR_* from the shell running this script can leak in; HERDR_SOCKET_PATH is
# the demo's own socket, so neither the server nor any client reaches yours.
ENVV=(HOME="$H" PATH="$H/.local/bin:$D/sysbin:/usr/bin:/bin" TERM=xterm-256color
      LANG=C.UTF-8 SHELL=/usr/bin/zsh TMUX_TMPDIR="$D"
      XDG_CONFIG_HOME="$H/.config" XDG_DATA_HOME="$H/.local/share" XDG_STATE_HOME="$H/.local/state"
      XDG_CACHE_HOME="$H/.cache" XDG_RUNTIME_DIR="$D/run"
      HERDR_SOCKET_PATH="$D/herdr.sock" TL_MANIFEST_DIR="$D/manifest")
denv() { env -i "${ENVV[@]}" "$@"; }

# The path is fixed (the tapes use it), so never trust what is already there:
# only ever touch our own real directory.
if [ -e "$D" ] || [ -L "$D" ]; then
  if [ -L "$D" ] || [ ! -O "$D" ]; then
    echo "refusing: $D exists and is not a directory you own" >&2
    exit 1
  fi
  # Stop only the servers of this demo: its tmux socket dir, its Zellij
  # runtime dir, its Herdr socket.
  denv tmux kill-server 2>/dev/null || true
  [ -x "$D/sysbin/zellij" ] && { denv zellij kill-all-sessions -y >/dev/null 2>&1 || true; }
  [ -x "$D/sysbin/herdr" ] && [ -S "$D/herdr.sock" ] && { denv herdr server stop >/dev/null 2>&1 || true; }
  [ "${1:-}" = --stop ] && { echo "demo servers stopped"; exit 0; }
  rm -rf -- "$D"
fi
[ "${1:-}" = --stop ] && exit 0
mkdir -m 700 "$D"   # no -p: fails if someone else recreated it meanwhile
mkdir -m 700 "$D/run"
mkdir -p "$H"/{projects/demo,projects/my-app,docker,case,ops/pentest,ops/malware,ops/osint,ops/ctf} \
         "$H"/.config/{zellij,herdr} "$H"/.local/{bin,share,state} "$H/.cache" "$D/sysbin"
ln -s "$(command -v pipx)" "$D/sysbin/pipx"
ln -s "$(command -v tmuxp)" "$D/sysbin/tmuxp"
ln -s "${ZELLIJ_BIN:-$(command -v zellij)}" "$D/sysbin/zellij"
if [ -n "${HERDR_BIN:-}" ] || command -v herdr >/dev/null; then
  ln -s "${HERDR_BIN:-$(command -v herdr)}" "$D/sysbin/herdr"
fi
printf '#!/bin/sh\nexec env -i %s "$@"\n' "${ENVV[*]}" > "$D/env"
chmod 700 "$D/env"

# Demo copy of the manifest: claude-projects tabs have absolute project
# directories; point them inside the demo HOME so no real path is shown.
command cp -R "$REPO/terminal_layouts/manifest" "$D/manifest"
sed -i "s#^\( *cwd: \)/home/[^/]*/projects/#\1$H/projects/#" "$D/manifest/workflows/"*.yaml
if grep -rnE "(^|[ \"'=])/home/" "$D/manifest"; then echo "error: real path left in demo manifest" >&2; exit 1; fi
for dir in $(sed -n "s#^ *cwd: \($H/.*\)#\1#p" "$D/manifest/workflows/"*.yaml); do
  mkdir -p "$dir/logs" "$dir/log"
  printf '%s\n' '[14:02:11] GET  /api/health 200 3ms' '[14:02:14] POST /api/search 200 41ms' \
    '[14:02:20] GET  /api/items?page=2 200 12ms' > "$dir/logs/dev.log"
  command cp -f "$dir/logs/dev.log" "$dir/log/dev.log"
done

printf 'show_startup_tips false\nshow_release_notes false\n' > "$H/.config/zellij/config.kdl"
printf '%s\n' 'onboarding = false' '[update]' 'version_check = false' 'manifest_check = false' \
  > "$H/.config/herdr/config.toml"
# No hostname in the tmux status bar (the GIF is public); room for long session names.
printf "set -g status-right ' %%H:%%M '\nset -g status-left-length 24\n" > "$H/.tmux.conf"

# Stand-ins for commands the layouts run that would put this machine's real
# ports, processes, files, containers or usage into a public GIF. Canned output only.
cat > "$D/sysbin/watch" <<'WATCH'
#!/bin/sh
interval=2 title=1
while [ $# -gt 0 ]; do
  case "$1" in -n) interval=$2; shift 2 ;; -t) title=; shift ;; -c|--color) shift ;; *) break ;; esac
done
cmd="$*"
while :; do
  printf '\033[H\033[2J'
  [ -n "$title" ] && printf 'Every %ss: %s        demo-box\n\n' "$interval" "$cmd"
  case "$cmd" in
    ss*) printf '%s\n' \
      'Netid State  Recv-Q Send-Q  Local Address:Port   Peer Address:Port  Process' \
      'tcp   LISTEN 0      128           0.0.0.0:22          0.0.0.0:*      sshd' \
      'tcp   LISTEN 0      511         127.0.0.1:8080        0.0.0.0:*      python3' \
      'tcp   ESTAB  0      0          10.10.14.7:44312   10.10.11.42:445    smbclient' \
      'udp   UNCONN 0      0             0.0.0.0:68          0.0.0.0:*      dhclient' ;;
    ps*) printf '%s\n' \
      'USER   PID %CPU %MEM COMMAND' \
      'demo  4242 12.0  1.1 nmap -sV -p- 10.10.11.42' \
      'demo  4310  3.4  0.6 python3 -m http.server 8080' \
      'demo  4377  0.7  0.2 tcpdump -i tun0 -w capture.pcap' \
      'demo  1001  0.1  0.1 zsh' ;;
    ls*) printf '%s\n' 'total 12' \
      '-rw-r--r-- 1 demo demo 4096 Nov 10 14:02 sample.bin' \
      '-rw-r--r-- 1 demo demo  812 Nov 10 14:01 dropper.log' \
      'drwx------ 2 demo demo 4096 Nov 10 13:58 sandbox' ;;
    git\ status*) printf '%s\n' '## main...origin/main [ahead 1]' ' M src/app.py' '?? notes.md' ;;
    git\ diff*) printf '%s\n' ' src/app.py | 12 ++++++++----' ' 1 file changed, 8 insertions(+), 4 deletions(-)' ;;
    docker*) docker ps ;;
    *) echo "(demo stand-in for: $cmd)" ;;
  esac
  sleep "$interval"
done
WATCH
cat > "$D/sysbin/docker" <<'DOCKER'
#!/bin/sh
case "$1" in
  ps) printf '%s\n' 'NAMES       STATUS          PORTS' \
        'web         Up 2 hours      0.0.0.0:8080->80/tcp' \
        'api         Up 2 hours      0.0.0.0:3000->3000/tcp' \
        'db          Up 2 hours      5432/tcp' ;;
  stats) printf '%s\n' 'NAME   CPU %   MEM USAGE / LIMIT' 'web    0.41%   38MiB / 1GiB' \
        'api    1.73%   112MiB / 1GiB' 'db     0.22%   61MiB / 1GiB' ;;
  *) echo "(demo stand-in for: docker $*)" ;;
esac
DOCKER
cat > "$D/sysbin/btop" <<'BTOP'
#!/bin/sh
printf '\033[H\033[2J'
printf '%s\n' ' cpu  ▁▂▃▅▃▂▁▂▃▂  18%     mem  ▃▃▃▃▄▄▄▃▃▃  3.1G / 16G' '' \
  '  PID  Program        Cpu%  Mem' ' 4242  node           12.0  410M' ' 4310  claude          6.1  220M' \
  ' 4377  bun             2.4   96M' ' 1001  zsh             0.1    6M'
exec sleep 86400
BTOP
cat > "$D/sysbin/bunx" <<'BUNX'
#!/bin/sh
case "$1" in
  ccusage) printf '%s\n' ' Date        Instance        Tokens     Cost' \
    ' 2026-11-09  brand-search    1.2M       $3.10' ' 2026-11-10  x-bot           0.8M       $2.05' ;;
  *) echo "(demo stand-in for: bunx $*)" ;;
esac
BUNX
chmod +x "$D/sysbin/watch" "$D/sysbin/docker" "$D/sysbin/btop" "$D/sysbin/bunx"

cat > "$H/.zshrc" <<'ZRC'
PROMPT='%F{blue}%~%f %F{magenta}❯%f '
setopt interactive_comments
autoload -Uz compinit && compinit -d "$HOME/.zcompdump"
zstyle ':completion:*:descriptions' format '%F{yellow}-- %d --%f'
ZRC

if [ "${1:-}" = --install ]; then
  denv pipx install "${TL_SRC:-git+https://github.com/gl0bal01/terminal-layouts}" >"$D/pipx.log" 2>&1 \
    || { echo "pipx install failed; see $D/pipx.log" >&2; exit 1; }
  echo 'eval "$(command tl init zsh)"' >> "$H/.zshrc"
fi
echo "demo environment ready in $D"

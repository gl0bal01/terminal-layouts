"""Shell helpers (shell/herdr-layouts.zsh) and tab completion, under bash AND zsh.

`tl` and `herdr` are stubbed: these tests check what each helper runs and
that completion is wired. tests/herdr_live.py runs the helpers for real.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPERS = REPO / "shell" / "herdr-layouts.zsh"
WORKFLOWS = sorted(p.stem for p in (REPO / "terminal_layouts/manifest/workflows").glob("*.yaml"))
SHELLS = ["bash", "zsh"]

STUB = """#!/bin/sh
name="$(basename "$0")"
if [ "$name" = tl ] && [ "$1" = list ]; then printf '%s\\n' {workflows}; exit 0; fi
if [ "$name" = herdr ] && [ "$1 $2" = "workspace list" ]; then
  echo '{{"result":{{"workspaces":[{{"workspace_id":"w1","label":"pt-acme","tab_count":4,"pane_count":15,"focused":true}},{{"workspace_id":"w2","label":"a:b","tab_count":1,"pane_count":1,"focused":false}}]}}}}'
  exit 0
fi
printf '%s' "$name" >> "$LOG"; for a in "$@"; do printf ' [%s]' "$a" >> "$LOG"; done; echo >> "$LOG"
"""


class ShellHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [s for s in SHELLS if shutil.which(s) is None]
        if missing:
            raise RuntimeError(f"shell tests need {missing} installed")
        cls.root = Path(tempfile.mkdtemp(prefix="tl-shell-"))
        (cls.root / "bin").mkdir()
        for name in ("tl", "herdr"):
            stub = cls.root / "bin" / name
            stub.write_text(STUB.format(workflows=" ".join(WORKFLOWS)))
            stub.chmod(0o755)
        cls.work = cls.root / "My Project"
        cls.work.mkdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def run_sh(self, shell: str, script: str, cwd: Path | None = None):
        log = self.root / f"{shell}.log"
        log.write_text("")
        env = {"PATH": f"{self.root / 'bin'}{os.pathsep}{os.environ['PATH']}",
               "HOME": str(self.root), "LOG": str(log), "TERM": "dumb"}
        if shell == "zsh":
            # -f: no user rc. compinit first, like oh-my-zsh does.
            argv = ["zsh", "-f", "-c", f"autoload -Uz compinit; compinit -u -D\n"
                                       f"source {HELPERS}\n{script}"]
        else:
            argv = ["bash", "--norc", "--noprofile", "-c", f"source {HELPERS}\n{script}"]
        out = subprocess.run(argv, cwd=cwd or self.work, env=env, capture_output=True, text=True)
        return out, log.read_text().splitlines()

    def test_helpers_run_the_right_tl_launch(self):
        cases = {
            "hag": f"tl [launch] [herdr] [ai-agents] [--cwd] [{self.work}]",
            "hag /srv/app --run-commands": "tl [launch] [herdr] [ai-agents] [--cwd] [/srv/app] [--run-commands]",
            "hag --run-commands": f"tl [launch] [herdr] [ai-agents] [--cwd] [{self.work}] [--run-commands]",
            "hproject": f"tl [launch] [herdr] [project] [--cwd] [{self.work}] [--label] [My Project]",
            "hproject api": f"tl [launch] [herdr] [project] [--cwd] [{self.work}] [--label] [api]",
            "hai": "tl [launch] [herdr] [claude-projects]",
            "hdk": "tl [launch] [herdr] [docker]",
            "hpt": "tl [launch] [herdr] [pentest]",
            "hma .": f"tl [launch] [herdr] [malware-analysis] [--cwd] [{self.work}]",
            "hos . --run-commands": f"tl [launch] [herdr] [osint] [--cwd] [{self.work}] [--run-commands]",
            "hctf --label x": "tl [launch] [herdr] [ctf] [--label] [x]",
            "hpt-new acme": "tl [launch] [herdr] [pentest] [--new] [acme]",
            "hai-new site --run-commands": "tl [launch] [herdr] [project] [--new] [site] [--run-commands]",
            "hks w1 w2": "herdr [workspace] [close] [w1]\nherdr [workspace] [close] [w2]",
        }
        for shell in SHELLS:
            for command, expected in cases.items():
                with self.subTest(shell=shell, command=command):
                    out, log = self.run_sh(shell, command)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log, expected.splitlines())

    def test_usage_errors_run_nothing(self):
        for shell in SHELLS:
            for command in ("hpt-new", "hdk-new --run-commands", "hks"):
                with self.subTest(shell=shell, command=command):
                    out, log = self.run_sh(shell, command)
                    self.assertEqual(out.returncode, 2)
                    self.assertIn("Usage:", out.stdout)
                    self.assertEqual(log, [])

    def test_hls_and_help(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, _ = self.run_sh(shell, "hls; hh | head -1; alias h")
                self.assertEqual(out.returncode, 0, out.stderr)
                lines = out.stdout.splitlines()
                self.assertEqual(lines[0], "* w1     pt-acme  (4 tabs, 15 panes)")
                self.assertEqual(lines[1], "  w2     a:b  (1 tabs, 1 panes)")
                self.assertIn("Herdr workspaces", lines[2])
                self.assertIn("herdr", lines[3])

    def test_missing_tl_is_reported(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, _ = self.run_sh(shell, "PATH=/usr/bin:/bin; hpt")
                self.assertEqual(out.returncode, 127)
                self.assertIn("`tl` not found", out.stderr)

    def test_completion_is_registered_in_both_shells(self):
        zsh = "print -l $_comps[tl] $_comps[hks] $_comps[hpt] $_comps[hpt-new] $_comps[hag] $_comps[hproject]"
        out, _ = self.run_sh("zsh", zsh)
        self.assertEqual(out.stdout.split(),
                         ["_tl", "_tlc_hks", "_tlc_here", "_tlc_new", "_tlc_hag", "_tlc_hproject"])
        self.assertEqual(out.stderr, "")
        out, _ = self.run_sh("bash", "complete -p tl hks hpt hag hproject hpt-new")
        for line in ("complete -F _tl_complete tl", "complete -F _tlc_hks hks",
                     "complete -F _tlc_here hpt", "complete -F _tlc_hag hag",
                     "complete -F _tlc_named hproject", "complete -F _tlc_named hpt-new"):
            self.assertIn(line, out.stdout)

    def test_zsh_completion_waits_for_compinit_silently(self):
        script = (f"source {HELPERS}\nprint -r -- before=${{_comps[tl]:-none}}\n"
                  "autoload -Uz compinit; compinit -u -D\n"
                  "for f in $precmd_functions; do $f; done\n"  # what the next prompt runs
                  "print -r -- after=$_comps[tl] hooked=${precmd_functions[(I)_tlc_register_deferred]:-0}")
        out = subprocess.run(["zsh", "-f", "-c", script], capture_output=True, text=True)
        self.assertEqual(out.stdout.split(), ["before=none", "after=_tl", "hooked=0"])
        self.assertEqual(out.stderr, "")

    def test_existing_aliases_and_commands_do_not_break_loading(self):
        # oh-my-zsh plugins define e.g. `alias hai=...`; h is often `history`.
        hh = self.root / "bin" / "hh"
        hh.write_text("#!/bin/sh\necho real-hh\n")
        hh.chmod(0o755)
        try:
            for shell in SHELLS:
                with self.subTest(shell=shell):
                    pre = "shopt -s expand_aliases\n" if shell == "bash" else ""
                    script = (f"{pre}alias hai='echo alias-hai'; alias hks='echo alias-hks'; "
                              f"alias h='echo history'\nsource {HELPERS}\n"
                              "hai; hks w1; hh; eval h; hhelp | head -2")  # eval: zsh -c parses up front
                    if shell == "zsh":
                        argv = ["zsh", "-f", "-c", "autoload -Uz compinit; compinit -u -D\n" + script]
                    else:
                        argv = ["bash", "--norc", "--noprofile", "-c", script]
                    log = self.root / f"{shell}.log"
                    log.write_text("")
                    env = {"PATH": f"{self.root / 'bin'}{os.pathsep}{os.environ['PATH']}",
                           "HOME": str(self.root), "LOG": str(log)}
                    out = subprocess.run(argv, cwd=self.work, env=env, capture_output=True, text=True)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log.read_text().splitlines(),
                                     ["tl [launch] [herdr] [claude-projects]",
                                      "herdr [workspace] [close] [w1]"])
                    lines = out.stdout.splitlines()
                    self.assertEqual(lines[:3], ["closed w1", "real-hh", "history"])
                    self.assertIn("Start Herdr first:  herdr ", lines[4])
                    self.assertNotIn("(or: h)", lines[4])
        finally:
            hh.unlink()

    def test_tmux_and_zellij_regen_helpers_do_not_collide(self):
        files = " ".join(str(REPO / "shell" / f) for f in ("tmux-layouts.zsh", "zellij-layouts.zsh"))
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(shell, f"for f in {files}; do source $f; done\n"
                                              "TL_ALWAYS_REGEN=1; _tl_maybe_regen_tmux docker; "
                                              "_tl_maybe_regen_zellij docker")
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(log, ["tl [gen] [tmux] [docker]", "tl [gen] [zellij] [docker]"])

    def test_bash_completion_candidates(self):
        def complete(line: str, fn: str = "_tl_complete", cwd: Path | None = None) -> list[str]:
            words = line.split(" ")
            script = textwrap.dedent(f"""
                COMP_WORDS=({' '.join(repr(w) for w in words)}); COMP_CWORD={len(words) - 1}
                {fn}; printf '%s\\n' "${{COMPREPLY[@]}}"
            """)
            out, _ = self.run_sh("bash", script, cwd=cwd)
            self.assertEqual(out.returncode, 0, out.stderr)
            return [w for w in out.stdout.splitlines() if w]

        self.assertEqual(complete("tl "), ["gen", "launch", "list", "validate", "install", "--help", "--version"])
        self.assertEqual(complete("tl g"), ["gen"])
        self.assertEqual(complete("tl gen "), ["tmux", "zellij", "herdr"])
        self.assertEqual(complete("tl gen herdr "), WORKFLOWS)
        self.assertEqual(complete("tl launch "), ["herdr"])
        self.assertEqual(complete("tl launch herdr p"), ["pentest", "project"])
        self.assertEqual(complete("tl launch herdr pentest --"),
                         ["--run-commands", "--cwd", "--new", "--label", "--help"])
        # Directory names with spaces stay one candidate, inserted as a filename (quoted).
        self.assertEqual(complete("tl launch herdr --cwd My", cwd=self.root), ["My Project"])
        self.assertEqual(complete("tl launch herdr --cwd My", "compopt() { echo \"compopt $1 $2\"; }; _tl_complete",
                                  cwd=self.root), ["compopt -o filenames", "My Project"])
        self.assertEqual(complete("tl launch --label x herdr "), WORKFLOWS)
        self.assertEqual(complete("hks w", "_tlc_hks"), ["w1", "w2"])
        self.assertEqual(complete("hpt ", "_tlc_here"), [".", "--run-commands", "--label"])
        self.assertEqual(complete("hag My", "_tlc_hag", cwd=self.root), ["My Project"])
        self.assertEqual(complete("hag . --", "_tlc_hag"), ["--run-commands", "--label"])
        self.assertEqual(complete("hpt-new ", "_tlc_named"), [])
        self.assertEqual(complete("hpt-new acme --", "_tlc_named"), ["--run-commands", "--label"])


if __name__ == "__main__":
    unittest.main()

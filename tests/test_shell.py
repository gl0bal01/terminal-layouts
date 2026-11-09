"""`tl init zsh|bash` shortcuts and tab completion, evaluated in real bash AND zsh.

`tl launch`, tmux, zellij and herdr are stubbed (they only record their
arguments); `tl init` and `tl list` run for real. tests/herdr_live.py and
tests/mux_live.py run the shortcuts against real servers.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHELLS = ["bash", "zsh"]
SHORTCUTS = {"ai-agents": "ag", "claude-projects": "ai", "ctf": "ctf", "docker": "dk",
             "malware-analysis": "ma", "osint": "os", "pentest": "pt", "project": "project"}
PREFIX = {"tmux": "t", "zellij": "z", "herdr": "h"}

TL_STUB = f"""#!/bin/sh
case "$1" in
  init|list) PYTHONPATH="{REPO}" exec "{sys.executable}" -m terminal_layouts.cli "$@" ;;
esac
printf 'tl' >> "$LOG"; for a in "$@"; do printf ' [%s]' "$a" >> "$LOG"; done; echo >> "$LOG"
"""
TOOL_STUB = """#!/bin/sh
name="$(basename "$0")"
if [ "$name" = herdr ] && [ "$1 $2" = "workspace list" ]; then
  echo '{"result":{"workspaces":[{"workspace_id":"w1","label":"pt-acme","tab_count":4,"pane_count":15,"focused":true},{"workspace_id":"w2","label":"a:b","tab_count":1,"pane_count":1,"focused":false}]}}'
  exit 0
fi
if [ "$name" = tmux ] && [ "$1" = list-sessions ] && [ "$2" = -F ]; then printf 'dev\\nops\\n'; exit 0; fi
if [ "$name" = zellij ] && [ "$1" = list-sessions ] && [ "$2" = --short ]; then printf 'zdev\\n'; exit 0; fi
printf '%s' "$name" >> "$LOG"; for a in "$@"; do printf ' [%s]' "$a" >> "$LOG"; done; echo >> "$LOG"
"""


class ShellInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [s for s in SHELLS if shutil.which(s) is None]
        if missing:
            raise RuntimeError(f"shell tests need {missing} installed")
        cls.root = Path(tempfile.mkdtemp(prefix="tl-shell-"))
        cls.bin = cls.root / "bin"
        cls.bin.mkdir()
        (cls.bin / "tl").write_text(TL_STUB)
        for tool in ("tmux", "zellij", "herdr"):
            (cls.bin / tool).write_text(TOOL_STUB)
        for stub in cls.bin.iterdir():
            stub.chmod(0o755)
        cls.work = cls.root / "My Project"
        cls.work.mkdir()
        # Generate each init script once; tests that exercise `tl init` flags call tl.
        for shell in SHELLS:
            script = subprocess.run([sys.executable, "-m", "terminal_layouts.cli", "init", shell],
                                    cwd=REPO, capture_output=True, text=True, check=True).stdout
            (cls.root / f"init.{shell}").write_text(script)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def run_sh(self, shell: str, script: str, *, setup: str = "", init: str = "source {init}",
               cwd: Path | None = None, env: dict | None = None):
        """Run `setup`, then the init line, then `script`; return (process, recorded calls)."""
        log = self.root / f"{shell}.log"
        log.write_text("")
        full = "\n".join([setup, init.format(shell=shell, init=self.root / f"init.{shell}"), script])
        if shell == "zsh":
            # -f: no user rc; compinit first, like oh-my-zsh.
            argv = ["zsh", "-f", "-c", "autoload -Uz compinit; compinit -u -D\n" + full]
        else:
            argv = ["bash", "--norc", "--noprofile", "-c", "shopt -s expand_aliases\n" + full]
        base = {"PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin", "HOME": str(self.root),
                "LOG": str(log), "TERM": "dumb"}
        out = subprocess.run(argv, cwd=cwd or self.work, env={**base, **(env or {})},
                             capture_output=True, text=True)
        return out, log.read_text().splitlines()

    def test_every_workflow_gets_launch_and_new_shortcuts_per_backend(self):
        for shell in SHELLS:
            for backend, p in PREFIX.items():
                for wf, sc in SHORTCUTS.items():
                    with self.subTest(shell=shell, name=p + sc):
                        out, log = self.run_sh(shell, f"{p}{sc} . --label x; {p}{sc}-new acme")
                        self.assertEqual(out.returncode, 0, out.stderr)
                        self.assertEqual(log, [f"tl [launch] [{backend}] [{wf}] [.] [--label] [x]",
                                               f"tl [launch] [{backend}] [{wf}] [--new] [acme]"])

    def test_session_helpers_legacy_names_and_core_aliases(self):
        cases = {
            "tls": ["tmux [list-sessions]"], "ta dev": ["tmux [attach] [-t] [dev]"],
            "tks dev": ["tmux [kill-session] [-t] [dev]"], "tka": ["tmux [kill-server]"],
            "zls": ["zellij [list-sessions]"], "za s": ["zellij [attach] [s]"],
            "zks s": ["zellij [kill-session] [s]"], "zka": ["zellij [kill-all-sessions]"],
            "zds s": ["zellij [delete-session] [s]"], "zda": ["zellij [delete-all-sessions]"],
            "hks w1 w2": ["herdr [workspace] [close] [w1]", "herdr [workspace] [close] [w2]"],
            "zp": ["tl [launch] [zellij] [claude-projects]"],
            "zo /srv": ["tl [launch] [zellij] [project] [/srv]"],
            "eval t new -d": ["tmux [new] [-d]"], "eval z ls": ["zellij [ls]"],
            "eval h status": ["herdr [status]"],
        }
        for shell in SHELLS:
            for command, expected in cases.items():
                with self.subTest(shell=shell, command=command):
                    out, log = self.run_sh(shell, command)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log, expected)

    def test_usage_errors_run_nothing(self):
        for shell in SHELLS:
            for command in ("tpt-new", "zma-new", "hag-new", "hks"):
                with self.subTest(shell=shell, command=command):
                    out, log = self.run_sh(shell, command)
                    self.assertEqual(out.returncode, 2)
                    self.assertIn("Usage:", out.stderr)
                    self.assertEqual(log, [])

    def test_hls_and_generated_help(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, _ = self.run_sh(shell, "hls; echo ---; th; echo ---; zhelp; echo ---; hh")
                self.assertEqual(out.returncode, 0, out.stderr)
                hls, tmux, zellij, herdr = out.stdout.split("---\n")
                self.assertEqual(hls.splitlines(), ["* w1     pt-acme  (4 tabs, 15 panes)",
                                                    "  w2     a:b  (1 tabs, 1 panes)"])
                self.assertIn("tpt [DIR|.]", tmux)
                self.assertIn("pentest in ~/ops/pentest", tmux)
                self.assertIn("tpt-new <name>", tmux)
                self.assertIn("~/ops/pentest/<name>, named pt-<name>", tmux)
                self.assertIn("tproject [DIR|.]", tmux)
                self.assertIn("project in the current directory", tmux)
                self.assertIn("zo [DIR|.]", zellij)
                self.assertIn("hks", herdr)
                self.assertIn("--run-commands", herdr)

    def test_existing_names_are_kept_and_reported(self):
        hh = self.bin / "hh"
        hh.write_text("#!/bin/sh\necho real-hh\n")
        hh.chmod(0o755)
        setup = "alias z='echo zoxide'\nfunction tpt { echo mine; }"
        try:
            for shell in SHELLS:
                with self.subTest(shell=shell):
                    out, log = self.run_sh(shell, "eval z; tpt; hh; zpt", setup=setup)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(out.stdout.splitlines(), ["zoxide", "mine", "real-hh"])
                    self.assertEqual(log, ["tl [launch] [zellij] [pentest]"])
                    self.assertIn("kept your existing tpt z hh", out.stderr)
                with self.subTest(shell=shell, mode="quiet"):
                    out, _ = self.run_sh(shell, "true", setup=setup, env={"TL_INIT_QUIET": "1"})
                    self.assertEqual(out.stderr, "")
                with self.subTest(shell=shell, mode="force"):
                    out, log = self.run_sh(shell, "eval z ls; tpt; hh | head -1", setup=setup,
                                           init='eval "$(tl init {shell} --force)"')
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log, ["zellij [ls]", "tl [launch] [tmux] [pentest]"])
                    self.assertIn("Herdr shortcuts", out.stdout)
                    self.assertEqual(out.stderr, "")
        finally:
            hh.unlink()

    def test_backends_subset_and_re_eval_are_clean(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(
                    shell, f'eval "$(tl init {shell} --backends tmux)"; tpt; '
                           "type zpt >/dev/null 2>&1 || echo no-zpt",
                    init='eval "$(tl init {shell} --backends tmux)"')
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(out.stdout.split(), ["no-zpt"])
                self.assertEqual(out.stderr, "")  # second eval: our own names, no warning
                self.assertEqual(log, ["tl [launch] [tmux] [pentest]"])

    def test_old_shell_files_still_work(self):
        sources = "; ".join(f"source {REPO}/shell/{b}-layouts.zsh" for b in PREFIX)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(shell, "tpt; zpt; hpt; type tag >/dev/null && echo ok", init=sources)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(out.stderr, "")
                self.assertEqual(log, ["tl [launch] [tmux] [pentest]", "tl [launch] [zellij] [pentest]",
                                       "tl [launch] [herdr] [pentest]"])
            with self.subTest(shell=shell, tl="missing"):
                out, _ = self.run_sh(shell, "true", init=f"source {REPO}/shell/tmux-layouts.zsh",
                                     env={"PATH": "/usr/bin:/bin"})
                self.assertIn("need a tl that has `tl init`", out.stderr)

    def test_zsh_completion_is_registered_for_owned_names_only(self):
        script = ("print -r -- ${_comps[tl]} ${_comps[tpt]} ${_comps[tpt-new]} ${_comps[ta]} "
                  "${_comps[zo]} ${_comps[hks]} ${_comps[hag]} z=${_comps[z]:-none}")
        out, _ = self.run_sh("zsh", script, setup="alias z='echo zoxide'", env={"TL_INIT_QUIET": "1"})
        self.assertEqual(out.stdout.split(), ["_tl", "_tlc_launch_tmux", "_tlc_new_tmux", "_tlc_tmux_sessions",
                                              "_tlc_launch_zellij", "_tlc_hks", "_tlc_launch_herdr", "z=none"])

    def test_zsh_completion_waits_for_compinit_silently(self):
        script = ('eval "$(tl init zsh)"\nprint -r -- before=${_comps[tl]:-none}\n'
                  "autoload -Uz compinit; compinit -u -D\n"
                  "for f in $precmd_functions; do $f; done\n"  # what the next prompt runs
                  "print -r -- after=$_comps[tpt] hooked=${precmd_functions[(I)_tlc_register_deferred]:-0}")
        env = {"PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin", "HOME": str(self.root)}
        out = subprocess.run(["zsh", "-f", "-c", script], capture_output=True, text=True, env=env)
        self.assertEqual(out.stdout.split(), ["before=none", "after=_tlc_launch_tmux", "hooked=0"])
        self.assertEqual(out.stderr, "")

    def test_bash_completion_is_registered_for_owned_names_only(self):
        out, _ = self.run_sh("bash", "complete -p tl tpt tpt-new ta hks zo; complete -p z || echo z-none",
                             setup="alias z='echo zoxide'", env={"TL_INIT_QUIET": "1"})
        for line in ("complete -F _tl_complete tl", "complete -F _tlc_launch_tmux tpt",
                     "complete -F _tlc_new_tmux tpt-new", "complete -F _tlc_tmux_sessions ta",
                     "complete -F _tlc_hks hks", "complete -F _tlc_launch_zellij zo", "z-none"):
            self.assertIn(line, out.stdout + out.stderr)

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

        self.assertEqual(complete("tl "),
                         ["gen", "launch", "init", "list", "validate", "install", "--help", "--version"])
        self.assertEqual(complete("tl launch "), ["herdr", "tmux", "zellij"])
        self.assertEqual(complete("tl launch tmux p"), ["pentest", "project"])
        self.assertEqual(complete("tl launch tmux pentest My", cwd=self.root), ["My Project"])
        self.assertEqual(complete("tl launch tmux pentest --"),
                         ["--cwd", "--new", "--help", "--label", "--detach"])
        self.assertEqual(complete("tl launch herdr pentest --r"), ["--run-commands"])
        self.assertEqual(complete("tl init "), ["zsh", "bash"])
        self.assertEqual(complete("tl init zsh --backends t"), ["tmux"])
        # Directories with spaces stay one candidate, inserted as a filename (quoted).
        self.assertEqual(complete("tl launch tmux pentest --cwd My",
                                  'compopt() { echo "compopt $1 $2"; }; _tl_complete', cwd=self.root),
                         ["compopt -o filenames", "My Project"])
        self.assertEqual(complete("tpt My", "_tlc_launch_tmux", cwd=self.root), ["My Project"])
        self.assertEqual(complete("tpt . --", "_tlc_launch_tmux"), ["--label", "--detach"])
        self.assertEqual(complete("hpt . --", "_tlc_launch_herdr"), ["--label", "--run-commands"])
        self.assertEqual(complete("hpt-new ", "_tlc_new_herdr"), [])
        self.assertEqual(complete("hks w", "_tlc_hks"), ["w1", "w2"])
        self.assertEqual(complete("ta ", "_tlc_tmux_sessions"), ["dev", "ops"])
        self.assertEqual(complete("za ", "_tlc_zellij_sessions"), ["zdev"])


if __name__ == "__main__":
    unittest.main()

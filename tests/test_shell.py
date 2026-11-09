"""`tl init zsh|bash` commands and tab completion, evaluated in real bash AND zsh.

`tl launch`, tmux, zellij and herdr are stubbed (they only record their
arguments); `tl init` and `tl list` run for real. tests/herdr_live.py and
tests/mux_live.py run the commands against real servers.
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
BACKENDS = ["tmux", "zellij", "herdr"]
WORKFLOWS = sorted(p.stem for p in (REPO / "terminal_layouts/manifest/workflows").glob("*.yaml"))

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
        for tool in BACKENDS:
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

    def test_every_workflow_gets_a_backend_workflow_command(self):
        for shell in SHELLS:
            for backend in BACKENDS:
                for wf in WORKFLOWS:
                    with self.subTest(shell=shell, name=f"{backend}-{wf}"):
                        out, log = self.run_sh(shell, f"{backend}-{wf} . --label x; {backend}-{wf} --new acme")
                        self.assertEqual(out.returncode, 0, out.stderr)
                        self.assertEqual(log, [f"tl [launch] [{backend}] [{wf}] [.] [--label] [x]",
                                               f"tl [launch] [{backend}] [{wf}] [--new] [acme]"])

    def test_session_commands_and_core_aliases(self):
        cases = {
            "tmux-ls": ["tmux [list-sessions]"], "tmux-attach dev": ["tmux [attach] [-t] [dev]"],
            "tmux-kill dev": ["tmux [kill-session] [-t] [dev]"], "tmux-kill-all": ["tmux [kill-server]"],
            "zellij-ls": ["zellij [list-sessions]"], "zellij-attach s": ["zellij [attach] [s]"],
            "zellij-kill s": ["zellij [kill-session] [s]"], "zellij-kill-all": ["zellij [kill-all-sessions]"],
            "zellij-delete s": ["zellij [delete-session] [s]"],
            "zellij-delete-all": ["zellij [delete-all-sessions]"],
            "herdr-close w1 w2": ["herdr [workspace] [close] [w1]", "herdr [workspace] [close] [w2]"],
            "eval t new -d": ["tmux [new] [-d]"], "eval z ls": ["zellij [ls]"],
            "eval h status": ["herdr [status]"],
        }
        for shell in SHELLS:
            for command, expected in cases.items():
                with self.subTest(shell=shell, command=command):
                    out, log = self.run_sh(shell, command)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log, expected)

    def test_old_short_names_are_gone(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, _ = self.run_sh(shell, "for n in tpt zma hag hks th zp zo tpt-new; do "
                                            "type $n >/dev/null 2>&1 && echo $n; done; true")
                self.assertEqual(out.stdout.split(), [])

    def test_herdr_close_without_ids_is_a_usage_error(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(shell, "herdr-close")
                self.assertEqual(out.returncode, 2)
                self.assertIn("Usage: herdr-close", out.stderr)
                self.assertEqual(log, [])

    def test_herdr_ls_and_layouts_help(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, _ = self.run_sh(shell, "herdr-ls; echo ---; layouts")
                self.assertEqual(out.returncode, 0, out.stderr)
                ls, help_text = out.stdout.split("---\n")
                self.assertEqual(ls.splitlines(), ["* w1     pt-acme  (4 tabs, 15 panes)",
                                                   "  w2     a:b  (1 tabs, 1 panes)"])
                for needle in ("<backend>-<workflow> [DIR|.] [--new NAME] [--label NAME]",
                               "pentest           ~/ops/pentest      pt-",
                               "project           current directory  -",
                               "tmux-pentest", "zellij-malware-analysis", "herdr-ai-agents",
                               "tmux-attach", "zellij-delete-all", "herdr-close",
                               "options: [--run-commands]", "type tmux- / zellij- / herdr- then Tab"):
                    self.assertIn(needle, help_text)

    def test_existing_names_are_kept_and_reported(self):
        external = self.bin / "herdr-ls"
        external.write_text("#!/bin/sh\necho real-herdr-ls\n")
        external.chmod(0o755)
        setup = "alias z='echo zoxide'\nfunction tmux-pentest { echo mine; }"
        try:
            for shell in SHELLS:
                with self.subTest(shell=shell):
                    out, log = self.run_sh(shell, "eval z; tmux-pentest; herdr-ls; zellij-pentest", setup=setup)
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(out.stdout.splitlines(), ["zoxide", "mine", "real-herdr-ls"])
                    self.assertEqual(log, ["tl [launch] [zellij] [pentest]"])
                    self.assertIn("kept your existing tmux-pentest z herdr-ls", out.stderr)
                with self.subTest(shell=shell, mode="quiet"):
                    out, _ = self.run_sh(shell, "true", setup=setup, env={"TL_INIT_QUIET": "1"})
                    self.assertEqual(out.stderr, "")
                with self.subTest(shell=shell, mode="force"):
                    out, log = self.run_sh(shell, "eval z ls; tmux-pentest; herdr-ls | head -1", setup=setup,
                                           init='eval "$(tl init {shell} --force)"')
                    self.assertEqual(out.returncode, 0, out.stderr)
                    self.assertEqual(log, ["zellij [ls]", "tl [launch] [tmux] [pentest]"])
                    self.assertEqual(out.stdout.splitlines(), ["* w1     pt-acme  (4 tabs, 15 panes)"])
                    self.assertEqual(out.stderr, "")
        finally:
            external.unlink()

    def test_aliased_tl_and_cat_do_not_break_anything(self):
        # oh-my-zsh's tmux plugin: alias tl='tmux list-sessions'; bat users: alias cat=bat.
        setup = "alias tl='echo ALIASED'; alias cat='echo CAT'"
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(shell, "tmux-pentest --new acme; layouts | head -1", setup=setup,
                                       init='eval "$(command tl init {shell})"')
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(log, ["tl [launch] [tmux] [pentest] [--new] [acme]"])
                self.assertEqual(out.stdout.splitlines(), ["Terminal layouts  (terminal-layouts)"])

    def test_completion_registry_does_not_grow_on_re_eval(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                init = self.root / f"init.{shell}"
                script = ('a="$_TLC_REGS_tmux"; source ' + str(init) + "; source " + str(init)
                          + '; [ "$a" = "$_TLC_REGS_tmux" ] && [ -n "$a" ] && echo same')
                out, _ = self.run_sh(shell, script)
                self.assertEqual(out.stdout.split(), ["same"], out.stderr)

    def test_backends_subset_and_re_eval_are_clean(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(
                    shell, f'eval "$(tl init {shell} --backends tmux)"; tmux-pentest; '
                           "type zellij-pentest >/dev/null 2>&1 || echo no-zellij; layouts | grep -c '^zellij'",
                    init='eval "$(tl init {shell} --backends tmux)"')
                self.assertEqual(out.stdout.split(), ["no-zellij", "0"])
                self.assertEqual(out.stderr, "")  # second eval: our own names, no warning
                self.assertEqual(log, ["tl [launch] [tmux] [pentest]"])

    def test_old_shell_files_still_work(self):
        sources = "; ".join(f"source {REPO}/shell/{b}-layouts.zsh" for b in BACKENDS)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out, log = self.run_sh(shell, "tmux-pentest; zellij-pentest; herdr-pentest; "
                                              "layouts | grep -cE '^(tmux|zellij|herdr)'", init=sources)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(out.stderr, "")
                self.assertEqual(out.stdout.split(), ["3"])  # help covers every sourced backend
                self.assertEqual(log, ["tl [launch] [tmux] [pentest]", "tl [launch] [zellij] [pentest]",
                                       "tl [launch] [herdr] [pentest]"])
            with self.subTest(shell=shell, tl="missing"):
                out, _ = self.run_sh(shell, "true", init=f"source {REPO}/shell/tmux-layouts.zsh",
                                     env={"PATH": "/usr/bin:/bin"})
                self.assertIn("tl not found", out.stderr)
            with self.subTest(shell=shell, tl="broken"):
                broken = self.root / "broken"
                broken.mkdir(exist_ok=True)
                (broken / "tl").write_text("#!/bin/sh\necho 'error: manifest is broken' >&2; exit 1\n")
                (broken / "tl").chmod(0o755)
                out, _ = self.run_sh(shell, "true", init=f"source {REPO}/shell/tmux-layouts.zsh",
                                     env={"PATH": f"{broken}:/usr/bin:/bin"})
                self.assertIn("error: manifest is broken", out.stderr)  # the real cause is shown
                self.assertIn("`tl init` failed", out.stderr)

    def test_zsh_completion_is_registered_for_owned_names_only(self):
        script = ("print -r -- ${_comps[tl]} ${_comps[tmux-pentest]} ${_comps[tmux-attach]} "
                  "${_comps[zellij-kill]} ${_comps[herdr-close]} ${_comps[herdr-ai-agents]} z=${_comps[z]:-none}")
        out, _ = self.run_sh("zsh", script, setup="alias z='echo zoxide'", env={"TL_INIT_QUIET": "1"})
        self.assertEqual(out.stdout.split(), ["_tl", "_tlc_launch_tmux", "_tlc_tmux_sessions",
                                              "_tlc_zellij_sessions", "_tlc_herdr_workspaces",
                                              "_tlc_launch_herdr", "z=none"])

    def test_zsh_completion_waits_for_compinit_silently(self):
        script = ('eval "$(tl init zsh)"\nprint -r -- before=${_comps[tl]:-none}\n'
                  "autoload -Uz compinit; compinit -u -D\n"
                  "for f in $precmd_functions; do $f; done\n"  # what the next prompt runs
                  "print -r -- after=${_comps[tmux-pentest]} "
                  "hooked=${precmd_functions[(I)_tlc_register_deferred]:-0}")
        env = {"PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin", "HOME": str(self.root)}
        out = subprocess.run(["zsh", "-f", "-c", script], capture_output=True, text=True, env=env)
        self.assertEqual(out.stdout.split(), ["before=none", "after=_tlc_launch_tmux", "hooked=0"])
        self.assertEqual(out.stderr, "")

    def test_bash_completion_is_registered_for_owned_names_only(self):
        out, _ = self.run_sh("bash", "complete -p tl tmux-pentest tmux-attach herdr-close zellij-kill; "
                                     "complete -p z || echo z-none",
                             setup="alias z='echo zoxide'", env={"TL_INIT_QUIET": "1"})
        for line in ("complete -F _tl_complete tl", "complete -F _tlc_launch_tmux tmux-pentest",
                     "complete -F _tlc_tmux_sessions tmux-attach",
                     "complete -F _tlc_herdr_workspaces herdr-close",
                     "complete -F _tlc_zellij_sessions zellij-kill", "z-none"):
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
        self.assertEqual(complete("tmux-pentest My", "_tlc_launch_tmux", cwd=self.root), ["My Project"])
        self.assertEqual(complete("tmux-pentest . --", "_tlc_launch_tmux"), ["--new", "--label", "--detach"])
        self.assertEqual(complete("herdr-pentest --", "_tlc_launch_herdr"),
                         ["--new", "--label", "--run-commands"])
        self.assertEqual(complete("herdr-pentest --new ", "_tlc_launch_herdr"), [])
        self.assertEqual(complete("herdr-close w", "_tlc_herdr_workspaces"), ["w1", "w2"])
        self.assertEqual(complete("tmux-attach ", "_tlc_tmux_sessions"), ["dev", "ops"])
        self.assertEqual(complete("zellij-attach ", "_tlc_zellij_sessions"), ["zdev"])


if __name__ == "__main__":
    unittest.main()

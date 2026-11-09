"""tl launch tmux|zellij and tl init (multiplexers are not started here; see mux_live.py)."""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from terminal_layouts import cli, common, launch_mux, shell_init


class FakeRun:
    """Stands in for subprocess.run: records argv and the layout file content."""

    def __init__(self, rc: int = 0):
        self.rc, self.argv, self.layout = rc, None, None

    def __call__(self, argv):
        self.argv = argv
        layout = next(a for a in argv if a.endswith((".yaml", ".kdl")))
        self.path = layout
        self.layout = Path(layout).read_text()
        return SimpleNamespace(returncode=self.rc)


class LaunchMux(unittest.TestCase):
    def setUp(self):
        self.wf = common.load_workflow("pentest")
        which = patch("terminal_layouts.launch_mux.shutil.which", return_value="/usr/bin/x")
        which.start()
        self.addCleanup(which.stop)

    def test_tmux_generates_fresh_layout_in_the_requested_directory(self):
        run = FakeRun()
        self.assertEqual(launch_mux.launch_tmux(self.wf, "/srv/eng", "pt-acme", run=run), 0)
        self.assertEqual(run.argv[:-1], ["tmuxp", "--color", "never", "load", "--no-progress",
                                         "-y", "-s", "pt-acme"])
        self.assertIn('start_directory: "/srv/eng"', run.layout)
        self.assertIn("session_name: pentest", run.layout)
        self.assertFalse(os.path.exists(run.path), "temporary layout must be removed")

    def test_tmux_detach_and_exit_code(self):
        run = FakeRun(rc=3)
        self.assertEqual(launch_mux.launch_tmux(self.wf, "/srv", "s", detach=True, run=run), 3)
        self.assertEqual(run.argv[-2], "-d")

    def test_zellij_uses_layout_file_session_and_default_cwd(self):
        run = FakeRun()
        launch_mux.launch_zellij(self.wf, "/srv/eng", "pt-acme", run=run)
        self.assertEqual(run.argv[0:2], ["zellij", "-n"])
        self.assertEqual(run.argv[3:], ["-s", "pt-acme", "options", "--default-cwd", "/srv/eng"])
        self.assertTrue(run.layout.lstrip().startswith("// dist/zellij/pentest.kdl"))
        self.assertFalse(os.path.exists(run.path))

    def test_missing_tools_are_clean_errors(self):
        with patch("terminal_layouts.launch_mux.shutil.which", return_value=None):
            with self.assertRaisesRegex(launch_mux.MuxError, "tmux not found"):
                launch_mux.launch_tmux(self.wf, "/srv", "s", run=FakeRun())
            with self.assertRaisesRegex(launch_mux.MuxError, "zellij not found"):
                launch_mux.launch_zellij(self.wf, "/srv", "s", run=FakeRun())


class CliLaunchMux(unittest.TestCase):
    def launch(self, *argv, rc: int = 0):
        seen = {}

        def fake(workflow, cwd, session, **kw):
            seen.update(workflow=workflow["id"], cwd=cwd, session=session, **kw)
            return rc

        out, err = io.StringIO(), io.StringIO()
        with patch.object(launch_mux, "launch_tmux", fake), patch.object(launch_mux, "launch_zellij", fake), \
                redirect_stdout(out), redirect_stderr(err):
            code = cli.main(["launch", *argv])
        return code, seen, err.getvalue()

    def test_manifest_directory_dir_dot_new_and_label(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            base = Path(home, "ops", "pentest")
            base.mkdir(parents=True)
            code, seen, _ = self.launch("tmux", "pentest")
            self.assertEqual((code, seen["cwd"], seen["session"], seen["detach"]),
                             (0, str(base), "pentest", False))
            code, seen, _ = self.launch("zellij", "pentest", home, "--label", "x")
            self.assertEqual((seen["cwd"], seen["session"]), (home, "x"))
            code, seen, _ = self.launch("tmux", "pentest", ".", "-d")
            self.assertEqual((seen["cwd"], seen["session"], seen["detach"]),
                             (os.getcwd(), "pt-" + os.path.basename(os.getcwd()), True))
            code, seen, _ = self.launch("tmux", "pentest", "--new", "acme")
            self.assertEqual((seen["cwd"], seen["session"]), (str(base / "acme"), "pt-acme"))
            self.assertTrue((base / "acme").is_dir())

    def test_dir_may_follow_options(self):
        code, seen, _ = self.launch("tmux", "project", "-d", "/tmp")
        self.assertEqual((code, seen["cwd"], seen["detach"]), (0, "/tmp", True))
        code, seen, _ = self.launch("zellij", "project", "--label", "x", "/tmp")
        self.assertEqual((seen["cwd"], seen["session"]), ("/tmp", "x"))
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            cli.main(["launch", "tmux", "project", "/tmp", "/srv"])

    def test_tmux_session_names_avoid_dot_and_colon(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            Path(home, "ops", "pentest").mkdir(parents=True)
            code, seen, _ = self.launch("tmux", "pentest", "--new", "acme.com")
            self.assertEqual((code, seen["session"]), (0, "pt-acme_com"))
            self.assertTrue(Path(home, "ops", "pentest", "acme.com").is_dir())
            code, seen, _ = self.launch("zellij", "pentest", "--new", "acme.com")
            self.assertEqual(seen["session"], "pt-acme.com")  # Zellij keeps it

    def test_project_runs_in_the_current_directory(self):
        here = os.path.basename(os.getcwd())
        code, seen, _ = self.launch("tmux", "project")
        self.assertEqual((code, seen["cwd"], seen["session"]), (0, os.getcwd(), here))
        # Prefixed, so two workflows launched from one directory never share a session.
        code, seen, _ = self.launch("zellij", "ai-agents")
        self.assertEqual((code, seen["session"]), (0, "ai-" + here))
        code, seen, _ = self.launch("tmux", "claude-projects", ".")
        self.assertEqual(seen["session"], "cp-" + here)
        prefixes = [common.load_workflow(w)["prefix"] for w in common.list_workflows()]
        self.assertEqual(len(prefixes), len(set(prefixes)), "prefixes must be unique")

    def test_errors(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            cases = {
                ("tmux", "pentest"): (1, "does not exist"),           # ~/ops/pentest missing
                ("tmux", "project", "--run-commands"): (2, "Herdr-only"),
                ("zellij", "project", "-d"): (2, "tmux-only"),
                ("tmux", "project", ".", "--new", "x"): (2, "only one of"),
                ("tmux", "project", "/nonexistent/x"): (2, "not a directory"),
            }
            for argv, (expected, message) in cases.items():
                with self.subTest(argv=argv):
                    code, seen, err = self.launch(*argv)
                    self.assertEqual((code, seen), (expected, {}))
                    self.assertIn(message, err)

    def test_failed_new_launch_removes_its_directory(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            code, _, _ = self.launch("tmux", "pentest", "--new", "acme", rc=1)
            self.assertEqual(code, 1)
            self.assertFalse(Path(home, "ops", "pentest", "acme").exists())

    def test_mux_error_is_reported(self):
        def boom(*a, **k):
            raise launch_mux.MuxError("tmuxp not found — pipx install tmuxp")

        err = io.StringIO()
        with patch.object(launch_mux, "launch_tmux", boom), redirect_stderr(err):
            self.assertEqual(cli.main(["launch", "tmux", "project"]), 1)
        self.assertIn("error: tmuxp not found", err.getvalue())


class ShellInitRender(unittest.TestCase):
    def test_every_shortcut_for_every_backend(self):
        script = shell_init.render("zsh")
        for wf_id in common.list_workflows():
            sc = common.load_workflow(wf_id)["shortcut"]
            for p in "tzh":
                with self.subTest(name=p + sc):
                    self.assertIn(f"function {p}{sc} {{", script)
                    self.assertIn(f"function {p}{sc}-new {{", script)

    def test_backend_subset_and_force(self):
        script = shell_init.render("bash", ["herdr"], force=True)
        self.assertIn("function hpt {", script)
        self.assertNotIn("function tpt {", script)
        self.assertIn('_TL_FORCE="1"', script)

    def test_reserved_shortcuts_and_bad_shell_are_rejected(self):
        real = common.load_workflow

        def with_reserved(wf_id):
            wf = real(wf_id)
            return dict(wf, shortcut="ls") if wf_id == "pentest" else wf

        with patch.object(common, "load_workflow", with_reserved):
            with self.assertRaisesRegex(ValueError, "reserved"):
                shell_init.render("zsh")
        with self.assertRaisesRegex(ValueError, "unsupported shell"):
            shell_init.render("fish")

    def test_unsafe_or_conflicting_shortcuts_are_clean_errors(self):
        real = common.load_workflow
        for bad in ("Pt", "p t", "a;rm", "p", "o"):  # p/o: Zellij keeps zp/zo
            with self.subTest(shortcut=bad):
                with patch.object(common, "load_workflow",
                                  lambda w, bad=bad: dict(real(w), shortcut=bad) if w == "pentest" else real(w)):
                    err = io.StringIO()
                    with redirect_stderr(err), redirect_stdout(io.StringIO()):
                        self.assertEqual(cli.main(["init", "zsh"]), 1)
                    self.assertIn("error: pentest:", err.getvalue())
                    self.assertNotIn("Traceback", err.getvalue())

    def test_registry_is_per_backend_so_re_eval_does_not_grow(self):
        script = shell_init.render("bash")
        self.assertNotIn("_TLC_REGS=", script)
        for backend in ("tmux", "zellij", "herdr"):
            self.assertIn(f'_TLC_REGS_{backend}="', script)

    def test_generated_bodies_bypass_aliases(self):
        script = shell_init.render("zsh")
        self.assertIn("command tl launch tmux pentest", script)
        self.assertIn("command cat <<'__TL_HELP__'", script)
        self.assertNotIn("\n  tl launch", script)

    def test_cli_rejects_unknown_backend(self):
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["init", "zsh", "--backends", "tmux,screen"]), 2)
        self.assertIn("unknown backend(s) screen", err.getvalue())


if __name__ == "__main__":
    unittest.main()

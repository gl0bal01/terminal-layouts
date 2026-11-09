"""End-to-end tests against REAL tmux (tmuxp) and Zellij — no mocks.

Run with `make e2e-mux` (downloads the pinned Zellij release) or
`ZELLIJ_BIN=/path/to/zellij python3 -m unittest discover -s tests -p mux_live.py`.

Everything runs with a throwaway HOME, XDG dirs and tmux socket dir, so your
own tmux and Zellij sessions are never touched. A missing tool is a failure,
not a skip: this file only runs when a live check was asked for.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from terminal_layouts import common, gen_herdr  # noqa: E402


def wait_for(predicate, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    return predicate()


def expected_tabs(workflow_id: str, backend: str) -> list[dict]:
    skip = "zellij_only" if backend == "tmux" else "tmux_only"
    tabs = [t for t in common.load_workflow(workflow_id)["tabs"] if not t.get(skip)]

    def leaves(node):
        return [node] if "id" in node else [x for c in node["children"] for x in leaves(c)]

    return [{"label": (t.get("emoji", "") + " " + t["name"]).strip(), "cwd": t.get("cwd"),
             "panes": len([x for p in t["panes"] for x in leaves(p)])} for t in tabs]


class LiveMux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        zellij = os.environ.get("ZELLIJ_BIN") or shutil.which("zellij")
        missing = [t for t in ("tmux", "tmuxp") if not shutil.which(t)] + ([] if zellij else ["zellij"])
        if missing:
            raise RuntimeError(f"live mux test needs {missing} (try `make e2e-mux`)")
        # /tmp keeps socket paths below the 108-byte AF_UNIX limit.
        cls.root = Path(tempfile.mkdtemp(prefix="tlm-", dir="/tmp" if os.path.isdir("/tmp") else None))
        cls.saved_env = dict(os.environ)
        for key in [k for k in os.environ if k.startswith(("TMUX", "ZELLIJ", "HERDR_"))]:
            del os.environ[key]
        home = cls.root / "home"
        (cls.root / "bin").mkdir()
        (cls.root / "bin" / "zellij").symlink_to(Path(zellij).resolve())
        tl = cls.root / "bin" / "tl"
        tl.write_text(f'#!/bin/sh\nPYTHONPATH="{REPO}" exec "{sys.executable}" -m terminal_layouts.cli "$@"\n')
        tl.chmod(0o755)
        xdg = {name: cls.root / "xdg" / name for name in ("config", "state", "cache", "data", "run")}
        for path in xdg.values():
            path.mkdir(parents=True, mode=0o700)
        os.environ.update({
            "HOME": str(home), "XDG_CONFIG_HOME": str(xdg["config"]), "XDG_STATE_HOME": str(xdg["state"]),
            "XDG_CACHE_HOME": str(xdg["cache"]), "XDG_DATA_HOME": str(xdg["data"]),
            "XDG_RUNTIME_DIR": str(xdg["run"]), "TMUX_TMPDIR": str(cls.root),
            "SHELL": shutil.which("bash") or "/bin/sh", "TERM": "xterm-256color", "LANG": "C.UTF-8",
            "PATH": f"{cls.root / 'bin'}{os.pathsep}{os.environ['PATH']}",
        })
        for value in common.load_defaults().get("paths", {}).values():
            Path(common.resolve_path(value, {})).mkdir(parents=True, exist_ok=True)
        cls.project = home / "projects" / "demo"
        cls.project.mkdir(parents=True, exist_ok=True)
        version = subprocess.run(["zellij", "--version"], capture_output=True, text=True).stdout.strip()
        tmux = subprocess.run(["tmux", "-V"], capture_output=True, text=True).stdout.strip()
        print(f"\nlive {tmux}, {version}", file=sys.stderr)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["tmux", "kill-server"], capture_output=True)
        subprocess.run(["zellij", "kill-all-sessions", "-y"], capture_output=True)
        os.environ.clear()
        os.environ.update(cls.saved_env)
        shutil.rmtree(cls.root, ignore_errors=True)

    def tearDown(self):
        subprocess.run(["tmux", "kill-server"], capture_output=True)
        subprocess.run(["tmux", "-L", "zellij-pty", "kill-server"], capture_output=True)
        subprocess.run(["zellij", "kill-all-sessions", "-y"], capture_output=True)
        subprocess.run(["zellij", "delete-all-sessions", "-y", "-f"], capture_output=True)

    def tl(self, *argv, cwd=None):
        return subprocess.run(["tl", *argv], cwd=cwd or self.project, capture_output=True, text=True)

    def tmux(self, *argv) -> list[str]:
        return subprocess.run(["tmux", *argv], capture_output=True, text=True).stdout.splitlines()

    def assert_tmux_session(self, session: str, workflow_id: str, cwd: Path) -> None:
        tabs = expected_tabs(workflow_id, "tmux")
        windows = [w.split("\t") for w in self.tmux(
            "list-windows", "-t", session, "-F", "#{window_id}\t#{window_name}\t#{window_panes}")]
        self.assertEqual([w[1] for w in windows], [t["label"] for t in tabs])
        self.assertEqual([int(w[2]) for w in windows], [t["panes"] for t in tabs])
        for (window_id, _, _), tab in zip(windows, tabs):
            want = tab["cwd"] if tab["cwd"] and os.path.isdir(tab["cwd"]) else (
                os.environ["HOME"] if tab["cwd"] else str(cwd))
            paths = set(self.tmux("list-panes", "-t", window_id, "-F", "#{pane_current_path}"))
            self.assertEqual(paths, {want}, tab["label"])

    def test_tmux_every_workflow_and_options(self):
        for workflow in common.list_workflows():
            with self.subTest(workflow=workflow):
                out = self.tl("launch", "tmux", workflow, "-d")
                self.assertEqual(out.returncode, 0, out.stderr)
                plan = gen_herdr.compile_plan(common.load_workflow(workflow), common.load_defaults())
                base = plan["cwd"].replace("$PWD", str(self.project))
                self.assert_tmux_session(workflow, workflow, Path(base))
        with self.subTest(option="--new"):
            out = self.tl("launch", "tmux", "pentest", "--new", "acme", "-d")
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assert_tmux_session("pt-acme", "pentest", Path(os.environ["HOME"], "ops/pentest/acme"))
        with self.subTest(option="."):
            out = self.tl("launch", "tmux", "malware-analysis", ".", "-d")
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assert_tmux_session("demo", "malware-analysis", self.project)

    def test_tmux_shortcuts_in_bash_and_zsh(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                script = f'eval "$(tl init {shell})"\ntpt-new eng-{shell} -d && tdk . -d --label dk-{shell} && tls'
                argv = (["zsh", "-f", "-c", "autoload -Uz compinit; compinit -u -D\n" + script]
                        if shell == "zsh" else ["bash", "--norc", "--noprofile", "-c", script])
                out = subprocess.run(argv, cwd=self.project, capture_output=True, text=True)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assert_tmux_session(f"pt-eng-{shell}", "pentest",
                                         Path(os.environ["HOME"], f"ops/pentest/eng-{shell}"))
                self.assert_tmux_session(f"dk-{shell}", "docker", self.project)
                self.assertIn(f"pt-eng-{shell}:", out.stdout)  # tls listed it
                killed = subprocess.run(argv[:-1] + [argv[-1].replace(
                    script, f'eval "$(tl init {shell})"\ntks pt-eng-{shell}')], capture_output=True, text=True)
                self.assertEqual(killed.returncode, 0, killed.stderr)
                self.assertNotIn(f"pt-eng-{shell}", "\n".join(self.tmux("list-sessions", "-F", "#S")))

    def zellij_in_pty(self, command: str) -> None:
        """Zellij needs a terminal: run it inside a pane of the isolated tmux server."""
        # Own socket (-L), so it never races with the tmux server under test.
        subprocess.run(["tmux", "-L", "zellij-pty", "-f", "/dev/null", "new-session", "-d",
                        "-x", "200", "-y", "50", f"{command}; sleep 60"], cwd=self.project, check=True)

    def zellij_sessions(self) -> list[str]:
        return subprocess.run(["zellij", "list-sessions", "--short", "--no-formatting"],
                              capture_output=True, text=True).stdout.split()

    def assert_zellij_session(self, session: str, workflow_id: str, cwd: Path) -> None:
        self.assertTrue(wait_for(lambda: session in self.zellij_sessions()), self.zellij_sessions())
        tabs = expected_tabs(workflow_id, "zellij")
        names = subprocess.run(["zellij", "-s", session, "action", "query-tab-names"],
                               capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(names, [t["label"] for t in tabs])
        layout = subprocess.run(["zellij", "-s", session, "action", "dump-layout"],
                                capture_output=True, text=True).stdout
        self.assertIn(f'cwd "{cwd}"', layout)

    def test_zellij_cli_and_shortcut(self):
        self.zellij_in_pty("tl launch zellij pentest --new acme")
        self.assert_zellij_session("pt-acme", "pentest", Path(os.environ["HOME"], "ops/pentest/acme"))
        self.zellij_in_pty("zsh -f -c 'autoload -Uz compinit; compinit -u -D; "
                           "eval \"$(tl init zsh)\"; zma . --label ma-here'")
        self.assert_zellij_session("ma-here", "malware-analysis", self.project)


if __name__ == "__main__":
    unittest.main()

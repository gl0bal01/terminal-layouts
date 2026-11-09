"""End-to-end tests against a REAL Herdr server (no mocks).

Run with `make e2e-herdr` (downloads the pinned Herdr release) or
`HERDR_BIN=/path/to/herdr python3 -m unittest discover -s tests -p herdr_live.py`.

A throwaway server is started with its own HOME, config and socket, so a Herdr
session you are working in is never touched. A missing binary is a failure,
not a skip: this file is only run when a live check was asked for.
"""
from __future__ import annotations

import json
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

from terminal_layouts import common, gen_herdr, launch_herdr  # noqa: E402

SHELL = shutil.which("bash") or "/bin/sh"


def herdr(*argv: str) -> dict:
    return launch_herdr._invoke_cli(list(argv)).get("result", {})


def leaves(node: dict) -> list[dict]:
    if "children" not in node:
        return [node]
    return [leaf for child in node["children"] for leaf in leaves(child)]


def containers(node: dict) -> list[dict]:
    if "children" not in node:
        return []
    return [node] + [c for child in node["children"] for c in containers(child)]


def wait_for(predicate, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


def foreground(pane_id: str) -> list[str]:
    info = herdr("pane", "process-info", "--pane", pane_id)["process_info"]
    return [p["cmdline"] for p in info["foreground_processes"]]


class LiveHerdr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary = os.environ.get("HERDR_BIN") or shutil.which("herdr")
        if not binary or not os.access(binary, os.X_OK):
            raise RuntimeError("live Herdr test needs HERDR_BIN or herdr on PATH (try `make e2e-herdr`)")
        # /tmp keeps the socket path below the 108-byte AF_UNIX sun_path limit.
        cls.root = Path(tempfile.mkdtemp(prefix="tlh-", dir="/tmp" if os.path.isdir("/tmp") else None))
        cls.saved_env = dict(os.environ)
        for key in [k for k in os.environ if k.startswith("HERDR_")]:
            del os.environ[key]
        home = cls.root / "home"
        # Expose exactly the requested binary as `herdr`, whatever its file name.
        (cls.root / "bin").mkdir()
        (cls.root / "bin" / "herdr").symlink_to(Path(binary).resolve())
        # The shell helpers call `tl`: point it at this checkout.
        tl = cls.root / "bin" / "tl"
        tl.write_text(f'#!/bin/sh\nPYTHONPATH="{REPO}" exec "{sys.executable}" -m terminal_layouts.cli "$@"\n')
        tl.chmod(0o755)
        xdg = {name: cls.root / "xdg" / name for name in ("config", "state", "cache", "data", "run")}
        for path in xdg.values():
            path.mkdir(parents=True, mode=0o700)
        os.environ.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(xdg["config"]),
            "XDG_STATE_HOME": str(xdg["state"]),
            "XDG_CACHE_HOME": str(xdg["cache"]),
            "XDG_DATA_HOME": str(xdg["data"]),
            "XDG_RUNTIME_DIR": str(xdg["run"]),
            "HERDR_SOCKET_PATH": str(cls.root / "h.sock"),
            "SHELL": SHELL,
            "PATH": f"{cls.root / 'bin'}{os.pathsep}{os.environ['PATH']}",
        })
        # Give every ~/... workflow directory a real target inside the fake HOME.
        for value in common.load_defaults().get("paths", {}).values():
            Path(common.resolve_path(value, {})).mkdir(parents=True, exist_ok=True)
        cls.log = open(cls.root / "server.log", "w")
        cls.server = subprocess.Popen(["herdr", "server"], stdout=cls.log, stderr=cls.log)
        def running() -> bool:
            out = subprocess.run(["herdr", "status", "server", "--json"],
                                 capture_output=True, text=True, timeout=10).stdout
            try:
                return json.loads(out).get("running") is True
            except ValueError:
                return False

        ok = wait_for(running)
        if not ok:
            cls.tearDownClass()
            raise RuntimeError(f"herdr server did not start; see {cls.root}/server.log")
        version = subprocess.run(["herdr", "--version"], capture_output=True, text=True)
        print(f"\nlive {version.stdout.strip()} at {binary}", file=sys.stderr)

    @classmethod
    def tearDownClass(cls):
        try:
            subprocess.run(["herdr", "server", "stop"], capture_output=True, timeout=10)
            cls.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait()
        cls.log.close()
        os.environ.clear()
        os.environ.update(cls.saved_env)
        shutil.rmtree(cls.root, ignore_errors=True)

    def tearDown(self):
        for ws in herdr("workspace", "list")["workspaces"]:
            herdr("workspace", "close", ws["workspace_id"])

    def assert_workspace_matches(self, plan: dict, ws: str, pane_ids: dict) -> None:
        tabs = herdr("tab", "list", "--workspace", ws)["tabs"]
        panes = herdr("pane", "list", "--workspace", ws)["panes"]
        self.assertEqual([t["label"] for t in tabs], [t["label"] for t in plan["tabs"]])
        focus = next((i for i, t in enumerate(plan["tabs"]) if t["focus"]), 0)
        self.assertEqual(herdr("workspace", "get", ws)["workspace"]["active_tab_id"],
                         tabs[focus]["tab_id"])
        for live, want in zip(tabs, plan["tabs"]):
            with self.subTest(tab=want["id"]):
                root = launch_herdr._tab_root(plan, want)
                mine = {p["pane_id"]: p for p in panes if p["tab_id"] == live["tab_id"]}
                ids = pane_ids[want["id"]]
                self.assertEqual(sorted(ids.values()), sorted(mine))
                # Leaf id -> live pane; names may repeat inside a tab, ids don't.
                pane = {leaf["id"]: mine[ids[leaf["id"]]] for leaf in leaves(root)}
                for leaf in leaves(root):
                    self.assertEqual(pane[leaf["id"]]["label"], leaf["name"])

                layout = herdr("pane", "layout", "--pane", next(iter(mine)))["layout"]
                rect = {p["pane_id"]: p["rect"] for p in layout["panes"]}
                # Real split directions and ratios equal what the manifest asks for.
                expected = sorted(
                    ({"row": "right", "column": "down"}[c["direction"]], round(r, 3))
                    for c in containers(root) for r in launch_herdr._ratios(c["children"]))
                self.assertEqual(sorted((s["direction"], round(s["ratio"], 3))
                                        for s in layout["splits"]), expected)
                # Sibling order on screen follows manifest order.
                for c in containers(root):
                    axis = "x" if c["direction"] == "row" else "y"
                    firsts = [rect[ids[launch_herdr._first_leaf(ch)["id"]]][axis]
                              for ch in c["children"]]
                    self.assertEqual(firsts, sorted(set(firsts)), f"{c['direction']} order")
                focus_id = launch_herdr._focus_leaf(root) or launch_herdr._first_leaf(root)["id"]
                self.assertEqual(layout["focused_pane_id"], ids[focus_id])

                tab_cwd = launch_herdr._tab_cwd(plan, want)
                for leaf in leaves(root):
                    cwd = launch_herdr._leaf_cwd(leaf, tab_cwd)
                    real = cwd if os.path.isdir(cwd) else os.environ["HOME"]
                    self.assertEqual(pane[leaf["id"]]["cwd"], real, leaf["id"])

    def test_every_workflow_materializes_exactly(self):
        for workflow in common.list_workflows():
            with self.subTest(workflow=workflow):
                plan = gen_herdr.compile_plan(common.load_workflow(workflow), common.load_defaults())
                pane_ids: dict = {}
                ws = launch_herdr.launch(plan, pane_ids=pane_ids)
                self.assert_workspace_matches(plan, ws, pane_ids)
                # Without --run-commands every pane is an idle shell.
                def only_shell(pane_id: str) -> bool:
                    names = [Path(p.split()[0].lstrip("-")).name for p in foreground(pane_id)]
                    return names == [Path(SHELL).name]

                for pane in herdr("pane", "list", "--workspace", ws)["panes"]:
                    self.assertTrue(wait_for(lambda: only_shell(pane["pane_id"])),
                                    f"{pane['label']}: {foreground(pane['pane_id'])}")
                herdr("workspace", "close", ws)

    def test_sizes_focus_and_pane_cwd_beyond_shipped_manifests(self):
        # Shipped manifests always focus a tab's first pane and set no pane
        # cwd; cover focus on a split-created pane, partial sizes and pane cwd
        # (absolute, $paths and relative).
        wf = {"id": "synthetic", "name": "Synthetic", "cwd": "$paths.projects", "tabs": [
            {"id": "a", "name": "a", "panes": [{"direction": "row", "children": [
                {"id": "main", "size": "70%"},
                {"direction": "column", "children": [
                    {"id": "x", "cwd": "$paths.ops"},
                    {"id": "y", "focus": True},
                    {"id": "z", "size": "20%", "cwd": "../ops"},  # relative to tab cwd
                ]},
            ]}]},
            {"id": "b", "name": "b", "focus": True, "panes": [{"id": "solo"}]},
        ]}
        plan = gen_herdr.compile_plan(wf, common.load_defaults())
        pane_ids: dict = {}
        ws = launch_herdr.launch(plan, pane_ids=pane_ids)
        self.assert_workspace_matches(plan, ws, pane_ids)

    def test_shell_helpers_against_real_server(self):
        helpers = REPO / "shell" / "herdr-layouts.zsh"
        project = Path(os.environ["HOME"]) / "projects" / "demo"
        project.mkdir(parents=True, exist_ok=True)
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                script = f"source {helpers}\nhag && hpt-new acme-{shell} && hls"
                argv = (["zsh", "-f", "-c", "autoload -Uz compinit; compinit -u -D\n" + script]
                        if shell == "zsh" else ["bash", "--norc", "--noprofile", "-c", script])
                out = subprocess.run(argv, cwd=project, capture_output=True, text=True)
                self.assertEqual(out.returncode, 0, out.stderr)
                live = {w["label"]: w["workspace_id"] for w in herdr("workspace", "list")["workspaces"]}
                self.assertEqual(sorted(live), sorted(["ai-demo", f"pt-acme-{shell}"]))
                for label, ws in live.items():
                    self.assertRegex(out.stdout, rf"{ws}\s+{label}\s+\(\d+ tabs, \d+ panes\)")
                engagement = Path(os.environ["HOME"]) / "ops" / "pentest" / f"acme-{shell}"
                cwds = {p["cwd"] for p in herdr("pane", "list", "--workspace", live[f"pt-acme-{shell}"])["panes"]}
                self.assertEqual(cwds, {str(engagement)})
                cwds = {p["cwd"] for p in herdr("pane", "list", "--workspace", live["ai-demo"])["panes"]}
                self.assertEqual(cwds, {str(project)})
                closed = subprocess.run(
                    argv[:-1] + [argv[-1].replace(script, f"source {helpers}\nhks {' '.join(live.values())}")],
                    capture_output=True, text=True)
                self.assertEqual(closed.returncode, 0, closed.stderr)
                self.assertEqual(herdr("workspace", "list")["workspaces"], [])

    def test_cli_run_commands_starts_only_manifest_commands(self):
        out = subprocess.run([sys.executable, "-m", "terminal_layouts.cli", "launch", "herdr",
                              "ai-agents", "--run-commands"], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        ws = out.stdout.strip().rsplit(" ", 1)[-1]
        panes = {p["label"]: p["pane_id"] for p in herdr("pane", "list", "--workspace", ws)["panes"]}
        want = {"git": "watch -n 5 -c git status -sb", "diff": "watch -n 5 -c git diff --stat"}
        for label, cmd in want.items():
            self.assertTrue(wait_for(lambda: foreground(panes[label]) == [cmd]),
                            f"{label}: {foreground(panes[label])}")
        for label, pane_id in panes.items():
            if label not in want:
                self.assertEqual(len(foreground(pane_id)), 1)
                self.assertNotIn("watch", foreground(pane_id)[0], label)

    def test_failure_mid_launch_leaves_no_workspace(self):
        plan = gen_herdr.compile_plan(common.load_workflow("ai-agents"), common.load_defaults())

        def flaky(argv):
            if argv[:2] == ["tab", "create"]:
                return launch_herdr._invoke_cli(["tab", "create", "--workspace", "w-missing"])
            return launch_herdr._invoke_cli(argv)

        with self.assertRaisesRegex(launch_herdr.HerdrError, "was closed"):
            launch_herdr.launch(plan, invoke=flaky)
        self.assertEqual(herdr("workspace", "list")["workspaces"], [])

    def test_stopped_server_is_reported_without_side_effects(self):
        dead = self.root / "dead"
        dead.mkdir()
        env = dict(os.environ, HERDR_SOCKET_PATH=str(dead / "h.sock"))
        out = subprocess.run([sys.executable, "-m", "terminal_layouts.cli", "launch", "herdr",
                              "ai-agents"], cwd=REPO, env=env, capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertIn("Herdr server unavailable", out.stderr)
        self.assertEqual(list(dead.iterdir()), [])

    def test_missing_directory_is_warned_and_falls_back_to_home(self):
        ctf = Path(common.resolve_path("$paths.ctf", common.load_defaults()))
        ctf.rmdir()
        try:
            out = subprocess.run([sys.executable, "-m", "terminal_layouts.cli", "launch", "herdr",
                                  "ctf"], cwd=REPO, capture_output=True, text=True)
        finally:
            ctf.mkdir()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(f"warning: directory {ctf} does not exist", out.stderr)
        ws = out.stdout.strip().rsplit(" ", 1)[-1]
        cwds = {p["cwd"] for p in herdr("pane", "list", "--workspace", ws)["panes"]}
        self.assertEqual(cwds, {os.environ["HOME"]})

    def test_pwd_comes_from_the_real_cwd_not_a_stale_env_var(self):
        out = subprocess.run([sys.executable, "-m", "terminal_layouts.cli", "launch", "herdr",
                              "ai-agents"], cwd=REPO, capture_output=True, text=True,
                             env=dict(os.environ, PWD="/nonexistent"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("does not exist", out.stderr)
        ws = out.stdout.strip().rsplit(" ", 1)[-1]
        cwds = {p["cwd"] for p in herdr("pane", "list", "--workspace", ws)["panes"]}
        self.assertEqual(cwds, {str(REPO)})

if __name__ == "__main__":
    unittest.main()

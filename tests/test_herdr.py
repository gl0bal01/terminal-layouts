"""Pure-plan and mocked-Herdr adapter tests (Herdr binary not required)."""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from terminal_layouts import cli, common, gen_herdr, launch_herdr


class FakeHerdr:
    def __init__(self):
        self.calls: list[list[str]] = []
        self.next_tab = 0
        self.next_pane = 0

    def _tab(self):
        self.next_tab += 1
        self.next_pane += 1
        return {"result": {"tab": {"tab_id": f"t{self.next_tab}"},
                           "root_pane": {"pane_id": f"p{self.next_pane}"}}}

    def __call__(self, cmd):
        self.calls.append(cmd)
        if cmd[:2] == ["status", "server"]:
            # Shape of `herdr status server --json` (0.8.2 and 0.9.5).
            return {"status": "running", "running": True, "compatible": True}
        if cmd[:2] == ["workspace", "create"]:
            result = self._tab()
            result["result"]["workspace"] = {"workspace_id": "w1"}
            return result
        if cmd[:2] == ["tab", "create"]:
            return self._tab()
        if cmd[:2] == ["pane", "split"]:
            self.next_pane += 1
            return {"result": {"pane": {"pane_id": f"p{self.next_pane}"}}}
        return {"result": {}}


# Two-level tree: sized row [main | column of three], focus on a split-created
# leaf, and a pane-level cwd using a $paths reference.
SIZED = {"id": "sized", "name": "Sized", "cwd": "/w", "tabs": [
    {"id": "a", "name": "a", "panes": [{"direction": "row", "children": [
        {"id": "main", "size": "60%"},
        {"direction": "column", "size": "40%", "children": [
            {"id": "x", "cwd": "$paths.ops/x"},
            {"id": "y", "focus": True},
            {"id": "z"},
        ]},
    ]}]},
    {"id": "b", "name": "b", "cwd": "/b", "focus": True, "panes": [{"id": "solo"}]},
]}


def _splits(calls):
    return [c for c in calls if c[:2] == ["pane", "split"]]


def _opt(cmd, flag):
    return cmd[cmd.index(flag) + 1]


class HerdrTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(gen_herdr.render("ai-agents"))

    def test_plan_is_deterministic_and_safe(self):
        self.assertEqual(gen_herdr.render("ai-agents"), gen_herdr.render("ai-agents"))
        self.assertEqual(self.plan["version"], 2)
        self.assertEqual([t["id"] for t in self.plan["tabs"]],
                         ["cockpit", "implement", "research", "review"])
        self.assertEqual(self.plan["cwd"], "$PWD")
        self.assertEqual(self.plan["tabs"][1]["panes"][0]["children"][0]["command"], "")

    def test_all_manifests_compile_without_executing_agents(self):
        for workflow in common.list_workflows():
            with self.subTest(workflow=workflow):
                compiled = json.loads(gen_herdr.render(workflow))
                self.assertEqual(compiled["id"], workflow)
                self.assertTrue(compiled["tabs"])

    def test_herdr_matches_manifest_shared_pane_order(self):
        def leaves(nodes):
            result = []
            for node in nodes:
                result.extend([node["id"]] if "id" in node else leaves(node["children"]))
            return result

        for workflow_id in common.list_workflows():
            with self.subTest(workflow=workflow_id):
                manifest = common.load_workflow(workflow_id)
                expected_tabs = [t for t in manifest["tabs"]
                                 if not t.get("tmux_only") and not t.get("zellij_only")]
                generated = gen_herdr.compile_plan(manifest, common.load_defaults())
                self.assertEqual([t["id"] for t in expected_tabs],
                                 [t["id"] for t in generated["tabs"]])
                for original, compiled in zip(expected_tabs, generated["tabs"]):
                    self.assertEqual(leaves(original["panes"]), leaves(compiled["panes"]))

    def test_launch_creates_nested_topology_without_running_commands(self):
        fake = FakeHerdr()
        self.assertEqual(launch_herdr.launch(self.plan, invoke=fake), "w1")
        self.assertEqual(sum(c[:2] == ["tab", "create"] for c in fake.calls), 3)
        self.assertEqual(sum(c[:2] == ["pane", "split"] for c in fake.calls), 5)
        self.assertEqual(sum(c[:2] == ["pane", "run"] for c in fake.calls), 0)
        splits = [c for c in fake.calls if c[:2] == ["pane", "split"]]
        self.assertEqual(splits[0][4], "right")
        self.assertEqual(splits[1][4], "down")

    def test_commands_are_opt_in(self):
        fake = FakeHerdr()
        launch_herdr.launch(self.plan, invoke=fake, run_commands=True)
        runs = [c for c in fake.calls if c[:2] == ["pane", "run"]]
        self.assertEqual(len(runs), 2)
        self.assertTrue(all("watch -n 5" in cmd[-1] for cmd in runs))

    def test_stopped_server_rejected_before_workspace_create(self):
        fake = FakeHerdr()
        stopped = {"status": "not_running", "running": False, "compatible": None}

        def invoke(cmd):
            return stopped if cmd[:2] == ["status", "server"] else fake(cmd)

        with self.assertRaisesRegex(launch_herdr.HerdrError, "unavailable"):
            launch_herdr.launch(self.plan, invoke=invoke)
        self.assertEqual(fake.calls, [])

    def test_sizes_map_to_chained_split_ratios(self):
        self.assertEqual(launch_herdr._ratios([{"size": 60}, {"size": 40}]), [0.6])
        thirds = launch_herdr._ratios([{}, {}, {}])
        self.assertAlmostEqual(thirds[0], 1 / 3)
        self.assertAlmostEqual(thirds[1], 1 / 2)
        # Unsized siblings share what the sized ones leave: 50 / 25 / 25.
        self.assertEqual(launch_herdr._ratios([{"size": 50}, {}, {}]), [0.5, 0.5])
        # Oversubscribed sizes are normalised instead of producing ratios >= 1.
        self.assertEqual(launch_herdr._ratios([{"size": 90}, {"size": 90}]), [0.5])
        fake = FakeHerdr()
        plan = gen_herdr.compile_plan(SIZED, common.load_defaults())
        launch_herdr.launch(plan, invoke=fake)
        self.assertEqual([_opt(c, "--ratio") for c in _splits(fake.calls)],
                         ["0.6", "0.3333", "0.5"])

    def test_pane_focus_maps_to_the_split_creating_that_pane(self):
        fake = FakeHerdr()
        plan = gen_herdr.compile_plan(SIZED, common.load_defaults())
        launch_herdr.launch(plan, invoke=fake)
        flags = ["--focus" if "--focus" in c else "--no-focus" for c in _splits(fake.calls)]
        # splits create: column(x), y, z  -> only y is focused.
        self.assertEqual(flags, ["--no-focus", "--focus", "--no-focus"])
        self.assertEqual(fake.calls[-1], ["tab", "focus", "t2"])

    def test_every_pane_gets_an_explicit_resolved_cwd(self):
        fake = FakeHerdr()
        plan = gen_herdr.compile_plan(SIZED, common.load_defaults())
        ops = common.resolve_path("$paths.ops", common.load_defaults())
        self.assertEqual(plan["tabs"][0]["panes"][0]["children"][1]["children"][0]["cwd"],
                         f"{ops}/x")
        launch_herdr.launch(plan, invoke=fake)
        self.assertEqual(_opt(fake.calls[1], "--cwd"), "/w")
        self.assertEqual([_opt(c, "--cwd") for c in _splits(fake.calls)],
                         [f"{ops}/x", "/w", "/w"])
        tab_b = next(c for c in fake.calls if c[:2] == ["tab", "create"])
        self.assertEqual(_opt(tab_b, "--cwd"), "/b")

    def test_pwd_is_expanded_at_launch_time(self):
        fake = FakeHerdr()
        launch_herdr.launch(self.plan, invoke=fake)
        self.assertEqual(_opt(fake.calls[1], "--cwd"), os.getcwd())
        self.assertEqual(launch_herdr._cwd("$PWD/sub"), os.getcwd() + "/sub")

    def test_failure_closes_the_partial_workspace(self):
        fake = FakeHerdr()

        def invoke(cmd):
            if cmd[:2] == ["tab", "create"]:
                raise launch_herdr.HerdrError("boom")
            return fake(cmd)

        with self.assertRaisesRegex(launch_herdr.HerdrError, "boom.*w1 was closed"):
            launch_herdr.launch(self.plan, invoke=invoke)
        self.assertEqual(fake.calls[-1], ["workspace", "close", "w1"])

    def test_relative_and_braced_cwds_resolve_against_parent(self):
        plan = {"cwd": "/w", "root_direction": "row", "tabs": [
            {"cwd": "app", "panes": [{"id": "a", "cwd": None}, {"id": "b", "cwd": "web"}]},
            {"cwd": None, "panes": [{"id": "c", "cwd": "/abs"}]},
        ]}
        self.assertEqual(launch_herdr._pane_cwds(plan), ["/w/app", "/w/app/web", "/abs"])
        self.assertEqual(launch_herdr._cwd("${PWD}/x"), os.getcwd() + "/x")
        # No cwd anywhere: where `tl` runs, like tmuxp and Zellij.
        self.assertEqual(launch_herdr._tab_cwd({"cwd": None}, {"cwd": None}), os.getcwd())

    def test_impossible_sizes_are_warned(self):
        wf = {"id": "w", "name": "w", "tabs": [
            {"id": "a", "name": "a", "panes": [{"direction": "row", "children": [
                {"id": "x", "size": "60%"}, {"id": "y", "size": "60%"}]}]},
            {"id": "b", "name": "b", "panes": [{"id": "p", "size": "100%"}, {"id": "q"}]},
            {"id": "c", "name": "c", "panes": [{"direction": "row", "children": [
                {"id": "ok", "size": "30%"}, {"id": "rest"}]}]},
        ]}
        self.assertEqual(gen_herdr.compile_plan(wf, common.load_defaults())["warnings"], [
            "tab a.panes.0: child sizes sum to 120%; Herdr scales them to fit",
            "tab b.panes: child sizes sum to 100%; Herdr scales them to fit",
        ])

    def test_close_failure_does_not_mask_original_error(self):
        fake = FakeHerdr()

        def invoke(cmd):
            if cmd[:2] == ["tab", "create"]:
                raise launch_herdr.HerdrError("boom")
            if cmd[:2] == ["workspace", "close"]:
                raise OSError("gone")
            return fake(cmd)

        with self.assertRaisesRegex(launch_herdr.HerdrError, "boom.*could not be closed: gone"):
            launch_herdr.launch(self.plan, invoke=invoke)

    def test_missing_dirs_are_reported(self):
        with tempfile.TemporaryDirectory() as present:
            plan = {"cwd": present, "root_direction": "row", "tabs": [
                {"cwd": None, "panes": [{"id": "a", "cwd": None},
                                       {"id": "b", "cwd": present + "/nope"}]},
            ]}
            self.assertEqual(launch_herdr.missing_dirs(plan), [present + "/nope"])

    def test_missing_binary_is_clean_failure(self):
        with patch("terminal_layouts.launch_herdr.shutil.which", return_value=None):
            with self.assertRaisesRegex(launch_herdr.HerdrError, "not found"):
                launch_herdr.launch(self.plan)

    def test_incompatible_plan_rejected_before_api_calls(self):
        fake = FakeHerdr()
        self.plan["version"] = 999
        with self.assertRaisesRegex(launch_herdr.HerdrError, "Unsupported"):
            launch_herdr.launch(self.plan, invoke=fake)
        self.assertEqual(fake.calls, [])

    def test_invalid_workflow_rejected(self):
        wf = common.load_workflow("ai-agents")
        del wf["tabs"]
        with self.assertRaises(Exception):
            gen_herdr.compile_plan(wf, common.load_defaults())


class CliLaunchOptions(unittest.TestCase):
    """`tl launch herdr` --cwd / --new / --label (Herdr itself is not called)."""

    def launch(self, *argv):
        seen = {}

        def fake_launch(plan, run_commands=False):
            seen["plan"] = plan
            return "w9"

        out, err = io.StringIO(), io.StringIO()
        with patch.object(launch_herdr, "launch", fake_launch), \
                redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(["launch", "herdr", *argv])
        return rc, seen.get("plan"), err.getvalue()

    def test_defaults_keep_manifest_label(self):
        rc, plan, _ = self.launch("pentest")
        self.assertEqual((rc, plan["label"]), (0, "Pentest"))
        # Workflows that run in the current directory are named after it.
        rc, plan, _ = self.launch("ai-agents")
        self.assertEqual((rc, plan["label"], plan["cwd"]), (0, "ai-" + os.path.basename(os.getcwd()), os.getcwd()))

    def test_cwd_overrides_directory_and_names_the_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, plan, _ = self.launch("pentest", "--cwd", tmp)
            self.assertEqual((rc, plan["cwd"], plan["label"]), (0, tmp, "pt-" + os.path.basename(tmp)))
            rc, plan, _ = self.launch("pentest", "--cwd", tmp, "--label", "acme")
            self.assertEqual(plan["label"], "acme")
            # Tabs keep their own directories; the rest inherit --cwd.
            self.assertEqual(set(launch_herdr._pane_cwds(plan)), {tmp})

    def test_new_creates_workflow_dir_and_prefixed_label(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            rc, plan, _ = self.launch("pentest", "--new", "acme")
            target = os.path.join(home, "ops", "pentest", "acme")
            self.assertEqual((rc, plan["cwd"], plan["label"]), (0, target, "pt-acme"))
            self.assertTrue(os.path.isdir(target))
            rc, plan, _ = self.launch("claude-projects", "--new", "site")
            self.assertEqual(plan["label"], "cp-site")

    def test_bad_directories_are_rejected_before_launch(self):
        for argv in (["--cwd", "/nonexistent/dir"], ["--new", "../escape"], ["--new", "a/b"],
                     ["--new", ".."], ["--new", ""]):
            with self.subTest(argv=argv):
                rc, plan, err = self.launch("pentest", *argv)
                self.assertEqual((rc, plan), (2, None))
                self.assertIn("error:", err)

    def test_failed_launch_removes_only_the_directory_it_created(self):
        def failing(plan, run_commands=False):
            raise launch_herdr.HerdrError("Herdr server unavailable")

        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            base = os.path.join(home, "ops", "pentest")
            os.makedirs(os.path.join(base, "kept"))
            for name, survives in (("fresh", False), ("kept", True)):
                with self.subTest(name=name), patch.object(launch_herdr, "launch", failing), \
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(cli.main(["launch", "herdr", "pentest", "--new", name]), 1)
                self.assertEqual(os.path.isdir(os.path.join(base, name)), survives)

    def test_uncreatable_new_directory_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as home, patch.dict(os.environ, {"HOME": home}):
            (Path(home) / "ops").write_text("a file, not a directory")
            rc, plan, err = self.launch("pentest", "--new", "acme")
            self.assertEqual((rc, plan), (1, None))
            self.assertIn("error: cannot create", err)
            self.assertNotIn("Traceback", err)

    def test_cwd_and_new_are_exclusive(self):
        rc, plan, err = self.launch("pentest", "--cwd", "/tmp", "--new", "x")
        self.assertEqual((rc, plan), (2, None))
        self.assertIn("only one of", err)


if __name__ == "__main__":
    unittest.main()

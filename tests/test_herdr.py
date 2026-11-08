"""Pure-plan and mocked-Herdr adapter tests (Herdr binary not required)."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from terminal_layouts import common, gen_herdr, launch_herdr


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


class HerdrTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(gen_herdr.render("ai-agents"))

    def test_plan_is_deterministic_and_safe(self):
        self.assertEqual(gen_herdr.render("ai-agents"), gen_herdr.render("ai-agents"))
        self.assertEqual(self.plan["version"], 1)
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


if __name__ == "__main__":
    unittest.main()

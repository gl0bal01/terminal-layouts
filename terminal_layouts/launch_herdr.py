"""Explicit Herdr launcher for a generated plan.

Creates only terminal topology by default; passing --run-commands is required
to execute the commands from the canonical manifest. No agent auto-starts.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

from terminal_layouts.gen_herdr import FORMAT, VERSION


class HerdrError(RuntimeError):
    """A missing capability or failed Herdr API operation."""


def _invoke_cli(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(["herdr", *argv], text=True, capture_output=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise HerdrError(f"herdr {' '.join(argv[:2])} failed: {detail}")
    try:
        data = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError as exc:
        raise HerdrError(f"herdr {' '.join(argv[:2])} returned non-JSON output") from exc
    if not isinstance(data, dict) or data.get("error") or data.get("ok") is False:
        raise HerdrError(f"herdr {' '.join(argv[:2])} returned an error: {data}")
    return data


def _response_id(response: dict[str, Any], component: str, key: str) -> str:
    value = response.get("result", {}).get(component, {}).get(key)
    if not isinstance(value, str) or not value:
        raise HerdrError(f"Herdr response lacks result.{component}.{key}")
    return value


def _cwd(value: str | None) -> str | None:
    if value == "$PWD":
        return os.getcwd()
    return value


def _first_leaf(pane: dict[str, Any]) -> dict[str, Any]:
    while "children" in pane:
        pane = pane["children"][0]
    return pane


def launch(
    plan: dict[str, Any],
    *,
    run_commands: bool = False,
    invoke: Callable[[list[str]], dict[str, Any]] | None = None,
) -> str:
    """Materialize a plan in the *running* Herdr server, returning workspace id.

    The optional invoke callback is used in tests and must return Herdr's JSON.
    On failure a partially created workspace may remain for inspection.
    """
    if plan.get("format") != FORMAT or plan.get("version") != VERSION:
        raise HerdrError("Unsupported Herdr plan format/version")
    if invoke is None:
        if shutil.which("herdr") is None:
            raise HerdrError("Herdr executable not found; install Herdr first")
        invoke = _invoke_cli
    try:
        invoke(["status", "server"])
    except HerdrError as exc:
        raise HerdrError("Herdr server unavailable; start 'herdr server' or open Herdr first") from exc

    tabs = plan["tabs"]
    # The workspace creation command also creates the initial tab/root pane.
    first_cwd = _cwd(tabs[0].get("cwd") or plan.get("cwd"))
    args = ["workspace", "create", "--label", plan["label"], "--no-focus"]
    if first_cwd:
        args += ["--cwd", first_cwd]
    response = invoke(args)
    workspace_id = _response_id(response, "workspace", "workspace_id")
    first_tab_id = _response_id(response, "tab", "tab_id")
    first_pane_id = _response_id(response, "root_pane", "pane_id")
    commands: list[tuple[str, str]] = []
    tab_ids: list[str] = []

    def create_tree(tree: dict[str, Any], anchor: str, effective_cwd: str | None) -> None:
        if "children" not in tree:
            own_cwd = _cwd(tree.get("cwd"))
            if own_cwd and own_cwd != effective_cwd:
                raise HerdrError(
                    f"pane {tree['id']} requires cwd {own_cwd!r}, but its existing root "
                    f"pane has cwd {effective_cwd!r}; use a tab-level cwd instead"
                )
            invoke(["pane", "rename", anchor, tree["name"]])
            if tree["command"]:
                cmd = tree["command"]
                if tree.get("args"):
                    cmd += " " + shlex.join(tree["args"])
                commands.append((anchor, cmd))
            return
        direction = {"row": "right", "column": "down"}[tree["direction"]]
        anchors = [anchor]
        # Establish sibling boundaries first; recurse afterwards so a nested
        # split stays inside its parent's region rather than disrupting peers.
        for child in tree["children"][1:]:
            cmd = ["pane", "split", anchors[-1], "--direction", direction, "--no-focus"]
            child_cwd = _cwd(_first_leaf(child).get("cwd"))
            if child_cwd:
                cmd += ["--cwd", child_cwd]
            child_result = invoke(cmd)
            anchors.append(_response_id(child_result, "pane", "pane_id"))
        for child, pane_id in zip(tree["children"], anchors):
            child_cwd = _cwd(_first_leaf(child).get("cwd")) or effective_cwd
            create_tree(child, pane_id, child_cwd)

    for index, tab in enumerate(tabs):
        if index == 0:
            tab_id, root_id = first_tab_id, first_pane_id
            invoke(["tab", "rename", tab_id, tab["label"]])
        else:
            tab_args = ["tab", "create", "--workspace", workspace_id,
                        "--label", tab["label"], "--no-focus"]
            tab_cwd = _cwd(tab.get("cwd") or plan.get("cwd"))
            if tab_cwd:
                tab_args += ["--cwd", tab_cwd]
            result = invoke(tab_args)
            tab_id = _response_id(result, "tab", "tab_id")
            root_id = _response_id(result, "root_pane", "pane_id")
        tab_ids.append(tab_id)
        panes = tab["panes"]
        if len(panes) == 1:
            root = panes[0]
        else:
            root = {"direction": plan["root_direction"], "children": panes}
        create_tree(root, root_id, _cwd(tab.get("cwd") or plan.get("cwd")))

    # Select the intended tab, leaving agent panes inert unless opted in.
    focus_index = next((i for i, tab in enumerate(tabs) if tab["focus"]), 0)
    invoke(["workspace", "focus", workspace_id])
    invoke(["tab", "focus", tab_ids[focus_index]])
    if run_commands:
        for pane_id, command in commands:
            invoke(["pane", "run", pane_id, command])
    return workspace_id

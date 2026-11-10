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


def _cwd(value: str | None, base: str | None = None) -> str | None:
    """Expand a plan directory at launch time.

    $PWD / ${PWD} is the real working directory (never a stale env var), other
    env vars and ~ are expanded, and a relative path is anchored at `base`,
    the parent directory (like Zellij), else the working directory.
    """
    if not value:
        return None
    for pwd in ("${PWD}", "$PWD"):
        if value == pwd or value.startswith(pwd + "/"):
            value = os.getcwd() + value[len(pwd):]
            break
    value = os.path.expanduser(os.path.expandvars(value))
    return os.path.normpath(os.path.join(base or os.getcwd(), value))


def _tab_cwd(plan: dict[str, Any], tab: dict[str, Any]) -> str:
    # No cwd anywhere = where `tl` runs, as tmuxp and Zellij do.
    plan_cwd = _cwd(plan.get("cwd")) or os.getcwd()
    return _cwd(tab.get("cwd"), plan_cwd) or plan_cwd


def _leaf_cwd(leaf: dict[str, Any], tab_cwd: str) -> str:
    return _cwd(leaf.get("cwd"), tab_cwd) or tab_cwd


def _first_leaf(pane: dict[str, Any]) -> dict[str, Any]:
    while "children" in pane:
        pane = pane["children"][0]
    return pane


def _leaves(pane: dict[str, Any]) -> list[dict[str, Any]]:
    if "children" not in pane:
        return [pane]
    return [leaf for child in pane["children"] for leaf in _leaves(child)]


def _tab_root(plan: dict[str, Any], tab: dict[str, Any]) -> dict[str, Any]:
    panes = tab["panes"]
    if len(panes) == 1:
        return panes[0]
    return {"direction": plan["root_direction"], "children": panes}


def _focus_leaf(tree: dict[str, Any]) -> str | None:
    """Id of the leaf that should hold tab focus (first focused node, DFS)."""
    if tree.get("focus"):
        return _first_leaf(tree)["id"]
    for child in tree.get("children", []):
        found = _focus_leaf(child)
        if found:
            return found
    return None


def _ratios(children: list[dict[str, Any]]) -> list[float]:
    """Herdr --ratio for each chained sibling split.

    Splitting a pane keeps `ratio` of its area for the original (left/top)
    pane, so split i keeps weight[i] out of the weights still to be placed.
    Unsized siblings share whatever percentage the sized ones leave.
    """
    sizes = [child.get("size") or 0 for child in children]
    known = [size for size in sizes if size]
    free = len(sizes) - len(known)
    rest = 100 - sum(known)
    fill = rest / free if free and rest > 0 else (sum(known) / len(known) if known else 1)
    weights = [size or fill for size in sizes]
    return [weights[i] / sum(weights[i:]) for i in range(len(weights) - 1)]


def _pane_cwds(plan: dict[str, Any]) -> list[str]:
    """Directory every pane is created in, in creation order."""
    return [_leaf_cwd(leaf, _tab_cwd(plan, tab))
            for tab in plan["tabs"] for leaf in _leaves(_tab_root(plan, tab))]


def missing_dirs(plan: dict[str, Any]) -> list[str]:
    """Pane directories that do not exist; Herdr silently falls back to $HOME."""
    return [d for d in dict.fromkeys(_pane_cwds(plan)) if not os.path.isdir(d)]


def launch(
    plan: dict[str, Any],
    *,
    run_commands: bool = False,
    invoke: Callable[[list[str]], dict[str, Any]] | None = None,
    pane_ids: dict[str, dict[str, str]] | None = None,
) -> str:
    """Materialize a plan in the *running* Herdr server, returning workspace id.

    The optional invoke callback is used in tests and must return Herdr's JSON.
    If given, pane_ids is filled with {tab id: {leaf id: Herdr pane id}}.
    On any failure the workspace created by this call is closed again, so the
    server is left exactly as it was.
    """
    if plan.get("format") != FORMAT or plan.get("version") != VERSION:
        raise HerdrError("Unsupported Herdr plan format/version")
    if invoke is None:
        if shutil.which("herdr") is None:
            raise HerdrError("Herdr executable not found; install Herdr first")
        invoke = _invoke_cli
    unavailable = "Herdr server unavailable; start 'herdr server' or open Herdr first"
    try:
        # Plain `status server` prints text; --json exits 0 even when not running.
        status = invoke(["status", "server", "--json"])
    except HerdrError as exc:
        raise HerdrError(unavailable) from exc
    if status.get("running") is not True:
        raise HerdrError(unavailable)
    if status.get("compatible") is False:
        raise HerdrError("Herdr client/server protocol mismatch; restart the Herdr server")

    created: list[tuple[dict[str, Any], str]] = []  # (leaf, pane id), creation order

    def split(anchor: str, direction: str, ratio: float, child: dict[str, Any],
              tab_cwd: str, focus_id: str | None) -> str:
        # The new pane is the first leaf of `child`; later splits keep it there.
        leaf = _first_leaf(child)
        cmd = ["pane", "split", anchor, "--direction", direction, "--ratio", f"{ratio:.4g}",
               "--focus" if leaf["id"] == focus_id else "--no-focus",
               "--cwd", _leaf_cwd(leaf, tab_cwd)]
        return _response_id(invoke(cmd), "pane", "pane_id")

    def create_tree(tree: dict[str, Any], anchor: str, tab_cwd: str,
                    focus_id: str | None) -> None:
        if "children" not in tree:
            invoke(["pane", "rename", anchor, tree["name"]])
            created.append((tree, anchor))
            return
        direction = {"row": "right", "column": "down"}[tree["direction"]]
        children = tree["children"]
        anchors = [anchor]
        # Establish sibling boundaries first; recurse afterwards so a nested
        # split stays inside its parent's region rather than disrupting peers.
        for child, ratio in zip(children[1:], _ratios(children)):
            anchors.append(split(anchors[-1], direction, ratio, child, tab_cwd, focus_id))
        for child, pane_id in zip(children, anchors):
            create_tree(child, pane_id, tab_cwd, focus_id)

    workspace_id: str | None = None
    try:
        tab_ids: list[str] = []
        for index, tab in enumerate(plan["tabs"]):
            tab_cwd = _tab_cwd(plan, tab)
            root = _tab_root(plan, tab)
            cwd_args = ["--cwd", _leaf_cwd(_first_leaf(root), tab_cwd)]
            if index == 0:
                # Workspace creation also creates the first tab and its root pane.
                response = invoke(["workspace", "create", "--label", plan["label"],
                                   "--no-focus", *cwd_args])
                workspace_id = _response_id(response, "workspace", "workspace_id")
                invoke(["tab", "rename", _response_id(response, "tab", "tab_id"), tab["label"]])
            else:
                response = invoke(["tab", "create", "--workspace", workspace_id,
                                   "--label", tab["label"], "--no-focus", *cwd_args])
            tab_ids.append(_response_id(response, "tab", "tab_id"))
            start = len(created)
            create_tree(root, _response_id(response, "root_pane", "pane_id"),
                        tab_cwd, _focus_leaf(root))
            if pane_ids is not None:
                pane_ids[tab["id"]] = {leaf["id"]: pane for leaf, pane in created[start:]}

        # Select the intended tab, leaving agent panes inert unless opted in.
        focus_index = next((i for i, tab in enumerate(plan["tabs"]) if tab["focus"]), 0)
        invoke(["workspace", "focus", workspace_id])
        invoke(["tab", "focus", tab_ids[focus_index]])
        if run_commands:
            for leaf, pane_id in created:
                if leaf["command"]:
                    args = " " + shlex.join(leaf["args"]) if leaf.get("args") else ""
                    invoke(["pane", "run", pane_id, leaf["command"] + args])
    except BaseException as exc:
        if workspace_id is None:
            raise
        try:
            invoke(["workspace", "close", workspace_id])
            note = f"partial workspace {workspace_id} was closed"
        except Exception as close_exc:  # never mask the original failure
            note = f"partial workspace {workspace_id} could not be closed: {close_exc}"
        if isinstance(exc, HerdrError):
            raise HerdrError(f"{exc} ({note})") from exc
        if hasattr(exc, "add_note"):  # Python 3.11+
            exc.add_note(note)
        raise
    return workspace_id

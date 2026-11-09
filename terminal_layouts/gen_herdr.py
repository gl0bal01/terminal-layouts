"""Compile a manifest into a deterministic, inert Herdr workspace plan.

Herdr is an API-backed runtime, not a static layout file. The generated JSON is
an inspectable plan; it does not open Herdr or run any user commands.
"""
from __future__ import annotations

import json
from typing import Any

from terminal_layouts import common

FORMAT = "terminal-layouts.herdr.plan"
VERSION = 2


def _pane(source: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    common_keys = {
        "focus": bool(source.get("focus")),
        "size": common.size_percent(source.get("size")),
    }
    if common.pane_is_leaf(source):
        cwd = source.get("cwd")
        return {
            "id": source["id"],
            "name": common.pane_name(source),
            "cwd": common.resolve_path(cwd, defaults) if cwd else None,
            "command": source.get("command") or "",
            "args": source.get("args") or [],
            **common_keys,
        }
    return {
        "direction": source["direction"],
        "children": [_pane(child, defaults) for child in source["children"]],
        **common_keys,
    }


def _warnings_for(pane: dict[str, Any], path: str) -> list[str]:
    # tmuxp and Zellij keep the pane open after its command exits too
    # (gen_zellij always emits close_on_exit=false), so this is parity, but
    # the manifest asked for something no backend currently honours.
    warnings: list[str] = []
    if pane.get("close_on_exit"):
        warnings.append(f"{path}: close_on_exit=true is not honoured; pane stays open")
    sizes = [common.size_percent(child.get("size")) or 0 for child in pane.get("children", [])]
    total = sum(sizes)
    if any(sizes) and (total > 100 or (all(sizes) and total != 100)
                       or (not all(sizes) and total == 100)):
        warnings.append(f"{path}: child sizes sum to {total}%; Herdr scales them to fit")
    for index, child in enumerate(pane.get("children", [])):
        warnings += _warnings_for(child, f"{path}.{index}")
    return warnings


def compile_plan(workflow: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    from jsonschema import Draft7Validator  # ~0.1 s import: only when a plan is compiled

    with common.SCHEMA_FILE.open(encoding="utf-8") as f:
        Draft7Validator(json.load(f)).validate(workflow)
    tabs: list[dict[str, Any]] = []
    warnings: list[str] = []
    for tab in workflow["tabs"]:
        if tab.get("tmux_only") or tab.get("zellij_only"):
            warnings.append(f"tab {tab['id']}: excluded (multiplexer-specific)")
            continue
        if len(tab["panes"]) == 1:
            warnings += _warnings_for(tab["panes"][0], f"tab {tab['id']}.panes.0")
        else:  # several root panes are split as siblings, sizes included
            warnings += _warnings_for({"children": tab["panes"]}, f"tab {tab['id']}.panes")
        tabs.append({
            "id": tab["id"],
            "label": (tab.get("emoji", "") + " " + tab["name"]).strip(),
            "focus": tab.get("focus", False),
            "cwd": common.resolve_path(tab["cwd"], defaults) if tab.get("cwd") else None,
            "panes": [_pane(pane, defaults) for pane in tab["panes"]],
        })
    if not tabs:
        raise ValueError("Herdr plan has no cross-backend tabs")
    return {
        "format": FORMAT,
        "version": VERSION,
        "id": workflow["id"],
        "label": workflow["name"],
        "cwd": common.resolve_cwd(workflow, defaults),
        "root_direction": defaults.get("defaults", {}).get("root_direction", "row"),
        "tabs": tabs,
        "warnings": warnings,
    }


def render(workflow_id: str) -> str:
    plan = compile_plan(common.load_workflow(workflow_id), common.load_defaults())
    return json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
